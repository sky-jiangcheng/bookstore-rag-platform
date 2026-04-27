# 图书管理系统 AgenticRAG 重构完整计划

## 执行摘要

本计划提供两种实施方案：
- **方案A（推荐）**: 基于 AgentScope 框架（2-3周，低风险）
- **方案B**: 自研 AgenticRAG（6-8周，完全可控）

建议采用**渐进式策略**：先用 AgentScope 快速实现 MVP，再逐步替换核心组件为自研代码。

---

## 第一部分：架构设计

### 1.1 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Vue.js)                       │
│  ┌──────────────┬──────────────┬─────────────────────────┐  │
│  │ Agent Chat   │ 推理可视化   │ 实时书单预览            │  │
│  │ Interface    │ Reasoning    │ Live Preview            │  │
│  └──────────────┴──────────────┴─────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebSocket / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                  Agent 服务层 (FastAPI)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Agent Orchestrator                        │  │
│  │         (AgentScope / 自研框架)                        │  │
│  └───────────────────────────────────────────────────────┘  │
│         │              │              │                     │
│    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐              │
│    │ 需求分析 │    │ 智能检索 │    │ 书单生成 │              │
│    │ Agent   │    │ Agent   │    │ Agent   │              │
│    └────┬────┘    └────┬────┘    └────┬────┘              │
│         │              │              │                     │
│    ┌────▼──────────────▼──────────────▼────┐              │
│    │           Tool Registry               │              │
│    │  ┌────────┐ ┌────────┐ ┌────────┐    │              │
│    │  │Vector  │ │Database│ │Inventory│   │              │
│    │  │Search  │ │ Query  │ │ Check   │   │              │
│    │  └────────┘ └────────┘ └────────┘    │              │
│    └───────────────────────────────────────┘              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      数据层                                 │
│  ┌────────────┬────────────┬────────────┬──────────────┐   │
│  │  Milvus    │  PostgreSQL│   Redis    │   Memory     │   │
│  │  (Vector)  │  (业务数据) │  (Cache)   │  (AgentScope)│   │
│  └────────────┴────────────┴────────────┴──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件设计

```python
# 统一接口设计（兼容两种方案）
from abc import ABC, abstractmethod
from typing import Dict, List, Any, AsyncIterator
from dataclasses import dataclass

@dataclass
class AgentMessage:
    """统一消息格式"""
    role: str  # user/assistant/system/tool
    content: str
    metadata: Dict[str, Any] = None
    timestamp: float = None

@dataclass
class BookListResult:
    """书单结果"""
    books: List[Dict]
    reasoning_chain: List[Dict]
    quality_score: float
    total_price: float
    confidence: float

class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, name: str, model: str = None):
        self.name = name
        self.model = model
        self.memory = []
        self.tools = {}
    
    @abstractmethod
    async def run(self, input_msg: AgentMessage) -> AsyncIterator[AgentMessage]:
        """执行智能体，支持流式输出"""
        pass
    
    def register_tool(self, name: str, func: callable):
        """注册工具"""
        self.tools[name] = func
    
    async def execute_tool(self, name: str, params: Dict) -> Any:
        """执行工具"""
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        return await self.tools[name](**params)


class RequirementAgent(BaseAgent):
    """需求分析智能体"""
    
    async def run(self, input_msg: AgentMessage) -> AsyncIterator[AgentMessage]:
        # 1. 分析用户输入
        analysis = await self._analyze_requirement(input_msg.content)
        
        # 2. 评估完整性
        if analysis["confidence"] < 0.7:
            yield AgentMessage(
                role="assistant",
                content=analysis["clarification_question"],
                metadata={"type": "clarification"}
            )
        else:
            yield AgentMessage(
                role="assistant", 
                content="需求分析完成",
                metadata={
                    "type": "requirement_analysis",
                    "data": analysis
                }
            )
    
    async def _analyze_requirement(self, text: str) -> Dict:
        """分析需求"""
        # 实现细节...
        pass


class RetrievalAgent(BaseAgent):
    """检索智能体"""
    
    async def run(self, input_msg: AgentMessage) -> AsyncIterator[AgentMessage]:
        requirement = input_msg.metadata.get("data", {})
        
        # 并行检索
        results = await self._parallel_retrieve(requirement)
        
        # 融合排序
        ranked = self._fusion_rerank(results)
        
        yield AgentMessage(
            role="assistant",
            content=f"检索到 {len(ranked)} 本候选书籍",
            metadata={"type": "retrieval_result", "data": ranked}
        )
    
    async def _parallel_retrieve(self, requirement: Dict) -> List[Dict]:
        """并行多路检索"""
        import asyncio
        
        tasks = [
            self.execute_tool("vector_search", {"query": requirement}),
            self.execute_tool("db_query", {"filters": requirement}),
            self.execute_tool("popular_books", {"category": requirement.get("category")})
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]


class RecommendationAgent(BaseAgent):
    """推荐智能体"""
    
    async def run(self, input_msg: AgentMessage) -> AsyncIterator[AgentMessage]:
        requirement = input_msg.metadata.get("requirement", {})
        candidates = input_msg.metadata.get("candidates", [])
        
        # 1. 规划分类占比
        plan = self._plan_categories(requirement, len(candidates))
        yield AgentMessage(
            role="assistant",
            content="正在规划书单结构...",
            metadata={"type": "planning", "plan": plan}
        )
        
        # 2. 选择书籍
        selected = self._select_books(candidates, plan)
        
        # 3. 质量评估
        quality = self._evaluate_quality(selected, requirement)
        
        if quality["score"] < 0.8:
            # 质量不达标，重新选择
            selected = self._reselect_with_strategy(selected, requirement)
        
        yield AgentMessage(
            role="assistant",
            content="书单生成完成",
            metadata={
                "type": "booklist",
                "data": BookListResult(
                    books=selected,
                    reasoning_chain=self._generate_reasoning(),
                    quality_score=quality["score"],
                    total_price=sum(b["price"] for b in selected),
                    confidence=quality["confidence"]
                )
            }
        )
```

---

## 第二部分：分阶段实施计划

### Phase 0: 准备阶段（Week 0）

#### 技术选型决策

```yaml
# config/implementation_strategy.yaml
phase1:
  approach: "agent_scope"  # 或 "custom"
  reason: "快速验证，降低风险"
  
phase2:
  approach: "hybrid"
  migrate_strategy: "逐步替换核心组件"
  
phase3:
  approach: "custom_optimized"
  goal: "完全可控的自研方案"
```

#### 环境准备

```bash
# 1. 安装 AgentScope（用于Phase 1）
pip install agentscope

# 2. 配置模型
export OPENAI_API_KEY=your_key
export DASHSCOPE_API_KEY=your_key  # 阿里云平台

# 3. 启动 AgentScope Studio（调试工具）
agentscope studio --host 0.0.0.0 --port 5001

# 4. 数据库迁移（如需）
# 准备支持 Agent 会话持久化的表结构
```

---

### Phase 1: MVP 快速验证（Week 1-2）

**目标**: 使用 AgentScope 快速实现核心功能，验证方案可行性

#### Week 1: 基础 Agent 实现

**Day 1-2: 需求分析 Agent**

```python
# backend/agents/requirement_agent.py
import agentscope
from agentscope.agents import ReActAgent
from agentscope.message import Msg

class BookListRequirementAgent(ReActAgent):
    """书单需求分析 Agent"""
    
    def __init__(self):
        super().__init__(
            name="RequirementAgent",
            sys_prompt="""你是专业的图书需求分析师。
            
任务：
1. 深入理解用户的阅读需求
2. 识别目标受众（职业、年龄、水平）
3. 提取关键主题、分类、关键词
4. 发现隐含偏好和约束条件
5. 评估需求完整性（0-1分数）

输出格式（JSON）：
{
  "target_audience": {
    "occupation": "职业",
    "age_group": "年龄段",
    "reading_level": "阅读水平"
  },
  "categories": [{"name": "分类", "percentage": 30}],
  "keywords": ["关键词"],
  "constraints": {
    "budget": 预算,
    "exclude_textbooks": true/false,
    "other": ["其他约束"]
  },
  "confidence": 0.85,
  "needs_clarification": false,
  "clarification_questions": ["问题1", "问题2"]
}""",
            model="gpt-4",  # 或 dashscope/qwen-max
        )
    
    def analyze(self, user_input: str) -> dict:
        """分析需求入口"""
        msg = Msg(name="user", content=user_input, role="user")
        response = self.reply(msg)
        
        # 解析 JSON 响应
        import json
        try:
            result = json.loads(response.content)
            return result
        except:
            return {
                "confidence": 0.5,
                "needs_clarification": True,
                "clarification_questions": ["能否更详细地描述您的需求？"]
            }


# 注册到 AgentScope
agentscope.init(
    model_configs=[
        {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "${OPENAI_API_KEY}",
        }
    ]
)
```

**Day 3-4: 检索 Agent + 工具**

```python
# backend/agents/retrieval_agent.py
import agentscope
from agentscope.tools import tool
from typing import List, Dict

class BookRetrievalAgent(ReActAgent):
    """图书检索 Agent"""
    
    def __init__(self, vector_store, db_session):
        self.vector_store = vector_store
        self.db = db_session
        
        super().__init__(
            name="RetrievalAgent",
            sys_prompt="""你是图书检索专家。

可用工具：
1. vector_search - 语义检索（适合模糊需求）
2. db_query - 精确查询（适合明确分类/作者）
3. check_inventory - 库存检查

策略：
- 需求明确 → db_query
- 需求模糊 → vector_search  
- 综合需求 → 两者结合

输出格式：
{
  "retrieval_strategy": "使用的策略",
  "results": [{"book_id": 1, "title": "...", "relevance": 0.9}],
  "total_found": 100,
  "available_count": 85
}""",
            model="gpt-4",
        )
        
        # 注册工具
        self.register_tools()
    
    def register_tools(self):
        """注册现有功能为工具"""
        
        @tool
        def vector_search(query: str, top_k: int = 20) -> List[Dict]:
            """向量语义检索"""
            results = self.vector_store.search(query, top_k)
            return [{
                "book_id": r.id,
                "title": r.title,
                "author": r.author,
                "price": r.price,
                "relevance_score": r.score
            } for r in results]
        
        @tool
        def db_query(
            category: str = None,
            author: str = None,
            min_price: float = None,
            max_price: float = None,
            limit: int = 50
        ) -> List[Dict]:
            """数据库精确查询"""
            query = self.db.query(Book)
            if category:
                query = query.filter(Book.category == category)
            if author:
                query = query.filter(Book.author.contains(author))
            if min_price:
                query = query.filter(Book.price >= min_price)
            if max_price:
                query = query.filter(Book.price <= max_price)
            
            books = query.limit(limit).all()
            return [{
                "book_id": b.id,
                "title": b.title,
                "author": b.author,
                "price": b.price,
                "stock": b.stock
            } for b in books]
        
        @tool
        def check_inventory(book_ids: List[int]) -> Dict[int, int]:
            """检查库存"""
            inventory = {}
            for bid in book_ids:
                stock = self.db.query(Stock).filter(
                    Stock.book_id == bid
                ).first()
                inventory[bid] = stock.quantity if stock else 0
            return inventory
        
        # 绑定工具到 Agent
        self.vector_search = vector_search
        self.db_query = db_query
        self.check_inventory = check_inventory
```

**Day 5-7: 推荐 Agent + 工作流编排**

```python
# backend/agents/recommendation_agent.py
from agentscope.pipelines import SequentialPipeline

class BookListRecommendationAgent(ReActAgent):
    """书单生成 Agent"""
    
    def generate_booklist(
        self, 
        requirement: dict, 
        candidates: list
    ) -> dict:
        """生成书单"""
        
        # 1. 规划分类
        category_plan = self._plan_categories(
            requirement, 
            len(candidates)
        )
        
        # 2. 按分类选书
        selected = []
        for cat, count in category_plan.items():
            cat_books = [
                c for c in candidates 
                if c["category"] == cat
            ]
            # 按匹配度排序选取
            cat_books.sort(
                key=lambda x: x.get("relevance_score", 0), 
                reverse=True
            )
            selected.extend(cat_books[:count])
        
        # 3. 质量评估
        quality = self._evaluate_quality(selected, requirement)
        
        # 4. 如果不达标，重新选择
        if quality["score"] < 0.8:
            selected = self._optimize_selection(
                selected, candidates, requirement
            )
        
        return {
            "books": selected,
            "category_plan": category_plan,
            "quality_score": quality,
            "total_price": sum(b["price"] for b in selected),
            "reasoning": self._generate_explanation(
                selected, requirement
            )
        }
    
    def _plan_categories(self, requirement: dict, total: int) -> dict:
        """规划分类占比"""
        categories = requirement.get("categories", [])
        
        if not categories:
            # 默认均分
            return {"综合": total}
        
        plan = {}
        remaining = total
        
        for i, cat in enumerate(categories):
            if i == len(categories) - 1:
                plan[cat["name"]] = remaining
            else:
                count = int(total * cat["percentage"] / 100)
                plan[cat["name"]] = count
                remaining -= count
        
        return plan


# 工作流编排
class BookListWorkflow:
    """书单生成工作流"""
    
    def __init__(self):
        self.req_agent = BookListRequirementAgent()
        self.retrieval_agent = None  # 需要注入依赖
        self.rec_agent = BookListRecommendationAgent()
    
    async def execute(self, user_input: str) -> dict:
        """执行完整工作流"""
        
        # Step 1: 需求分析
        req_result = self.req_agent.analyze(user_input)
        
        if req_result["needs_clarification"]:
            return {
                "status": "clarification_needed",
                "questions": req_result["clarification_questions"]
            }
        
        # Step 2: 检索
        candidates = self.retrieval_agent.retrieve(req_result)
        
        # Step 3: 生成书单
        booklist = self.rec_agent.generate_booklist(
            req_result, 
            candidates
        )
        
        return {
            "status": "success",
            "requirement": req_result,
            "booklist": booklist
        }
```

#### Week 2: API 集成与前端改造

**后端 API**

```python
# backend/api/agent_api.py
from fastapi import APIRouter, WebSocket
from fastapi.responses import StreamingResponse
import json
import asyncio

router = APIRouter(prefix="/v2/agent", tags=["Agent"])

@router.post("/chat")
async def agent_chat(request: AgentChatRequest):
    """Agent 对话接口（非流式）"""
    workflow = BookListWorkflow()
    
    result = await workflow.execute(request.message)
    
    return {
        "success": result["status"] == "success",
        "data": result,
        "session_id": request.session_id
    }

@router.websocket("/ws")
async def agent_websocket(websocket: WebSocket):
    """WebSocket 实时对话（流式）"""
    await websocket.accept()
    
    try:
        while True:
            # 接收用户消息
            data = await websocket.receive_json()
            user_msg = data["message"]
            
            # 创建 Agent 实例
            agent = BookListRequirementAgent()
            
            # 流式返回思考过程
            async for step in agent.run_streaming(user_msg):
                await websocket.send_json({
                    "type": step.type,  # thought/action/observation/result
                    "content": step.content,
                    "metadata": step.metadata
                })
                
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()
```

**前端改造**

```vue
<!-- frontend/src/views/AgentBookList/index.vue -->
<template>
  <div class="agent-booklist-container">
    <h2>AI 智能书单助手</h2>
    
    <!-- 步骤指示器 -->
    <el-steps :active="currentStep" finish-status="success">
      <el-step title="需求分析" description="AI理解您的需求" />
      <el-step title="智能检索" description="从书库搜索" />
      <el-step title="生成书单" description="精选推荐" />
    </el-steps>
    
    <!-- 对话区域 -->
    <AgentChatInterface
      :messages="messages"
      :thinking="isThinking"
      @send="handleSendMessage"
    />
    
    <!-- 实时推理展示 -->
    <ReasoningPanel
      v-if="reasoningSteps.length > 0"
      :steps="reasoningSteps"
    />
    
    <!-- 书单结果 -->
    <BookListResult
      v-if="bookList"
      :data="bookList"
      @regenerate="handleRegenerate"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAgentStore } from '@/stores/agent'

const agentStore = useAgentStore()
const messages = ref([])
const reasoningSteps = ref([])
const isThinking = ref(false)
const bookList = ref(null)
const currentStep = ref(0)

// WebSocket 连接
let ws = null

onMounted(() => {
  // 连接 Agent WebSocket
  ws = new WebSocket('ws://localhost:8000/v2/agent/ws')
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    switch(data.type) {
      case 'thought':
        reasoningSteps.value.push(data)
        break
      case 'action':
        currentStep.value = getStepFromAction(data.content)
        break
      case 'result':
        bookList.value = data.content
        isThinking.value = false
        break
    }
  }
})

const handleSendMessage = async (message) => {
  messages.value.push({ role: 'user', content: message })
  isThinking.value = true
  reasoningSteps.value = []
  
  ws.send(JSON.stringify({ message }))
}
</script>
```

---

### Phase 2: 功能增强（Week 3-4）

**目标**: 添加高级功能，优化性能

#### Week 3: 高级功能

**1. 多智能体协作**

```python
# backend/agents/multi_agent.py
from agentscope.pipelines import IfElsePipeline, SwitchPipeline

class MultiAgentOrchestrator:
    """多智能体编排器"""
    
    def __init__(self):
        self.agents = {
            "requirement": RequirementAgent(),
            "retrieval": RetrievalAgent(),
            "recommendation": RecommendationAgent(),
            "evaluation": EvaluationAgent()  # 新增
        }
    
    async def collaborative_generate(self, user_input: str) -> dict:
        """协作生成书单"""
        
        # 1. 需求分析
        req = await self.agents["requirement"].analyze(user_input)
        
        # 2. 并行检索（多路召回）
        retrieval_tasks = [
            self.agents["retrieval"].vector_search(req),
            self.agents["retrieval"].db_query(req),
            self.agents["retrieval"].search_popular(req)
        ]
        results = await asyncio.gather(*retrieval_tasks)
        
        # 3. 融合排序
        fused = self._fusion_rerank(results)
        
        # 4. 生成书单
        booklist = await self.agents["recommendation"].generate(
            req, fused
        )
        
        # 5. 质量评估
        evaluation = await self.agents["evaluation"].evaluate(
            booklist, req
        )
        
        # 6. 如果质量不达标，迭代优化
        if evaluation["score"] < 0.8:
            booklist = await self._iterate_improve(
                booklist, evaluation, req
            )
        
        return {
            "booklist": booklist,
            "evaluation": evaluation,
            "process": self._get_process_trace()
        }
```

**2. 记忆系统**

```python
# backend/memory/agent_memory.py
class BookListMemory:
    """书单推荐记忆系统"""
    
    def __init__(self, redis_client, db_session):
        self.short_term = redis_client  # 短期对话记忆
        self.long_term = db_session     # 长期用户画像
    
    async def get_user_context(self, user_id: str) -> dict:
        """获取用户上下文"""
        # 短期记忆：最近对话
        recent_dialogues = await self.short_term.get_recent(user_id, limit=5)
        
        # 长期记忆：用户画像
        profile = await self.long_term.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        return {
            "recent_dialogues": recent_dialogues,
            "preferences": profile.preferences if profile else {},
            "history_booklists": profile.history if profile else []
        }
    
    async def learn_from_feedback(
        self, 
        user_id: str, 
        booklist: dict, 
        feedback: dict
    ):
        """从反馈中学习"""
        # 更新用户偏好
        if feedback["liked"]:
            await self._update_preference(
                user_id, 
                booklist["categories"], 
                weight=1.0
            )
        else:
            await self._update_preference(
                user_id, 
                booklist["categories"], 
                weight=-0.5
            )
```

**3. 自我反思**

```python
# backend/agents/self_reflection.py
class SelfReflection:
    """智能体自我反思"""
    
    async def reflect(
        self, 
        booklist: dict, 
        requirement: dict,
        user_feedback: str = None
    ) -> dict:
        """反思改进"""
        
        reflection_prompt = f"""
        评估刚才的书单推荐：
        
        需求：{requirement}
        书单：{booklist}
        反馈：{user_feedback}
        
        请回答：
        1. 分类比例是否合理？
        2. 是否有遗漏的重要书籍？
        3. 用户可能喜欢/不喜欢什么？
        4. 如何改进？
        """
        
        reflection = await self.llm.generate(reflection_prompt)
        
        # 如果发现问题，生成改进计划
        if "不合理" in reflection or "遗漏" in reflection:
            return {
                "needs_improvement": True,
                "issues": self._extract_issues(reflection),
                "improvement_plan": self._generate_plan(reflection)
            }
        
        return {"needs_improvement": False}
```

#### Week 4: 性能优化

**1. 缓存策略**

```python
# backend/cache/agent_cache.py
from functools import wraps
import hashlib

class AgentCache:
    """Agent 结果缓存"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = {
            "vector_search": 300,    # 5分钟
            "requirement_analysis": 3600,  # 1小时
            "popular_books": 1800    # 30分钟
        }
    
    def cache_result(self, func_name: str, ttl: int = None):
        """缓存装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_key(func_name, args, kwargs)
                
                # 尝试从缓存获取
                cached = await self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 存入缓存
                await self.redis.setex(
                    cache_key,
                    ttl or self.ttl.get(func_name, 300),
                    json.dumps(result)
                )
                
                return result
            return wrapper
        return decorator
```

**2. 异步优化**

```python
# 并行工具调用
async def parallel_tool_execution(tools: list, params: dict) -> list:
    """并行执行多个工具"""
    tasks = [tool(**params) for tool in tools]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

# 流式输出
async def stream_agent_response(agent, message):
    """流式返回 Agent 响应"""
    async for chunk in agent.run_streaming(message):
        yield f"data: {json.dumps(chunk)}\n\n"
```

---

### Phase 3: 迁移到自研（可选，Week 5-8）

**目标**: 逐步替换 AgentScope 为核心组件，实现完全可控

#### 迁移策略

```python
# backend/agents/factory.py
class AgentFactory:
    """智能体工厂（支持切换实现）"""
    
    @staticmethod
    def create_agent(agent_type: str, implementation: str = "agentscope"):
        """创建智能体"""
        if implementation == "agentscope":
            return AgentFactory._create_agentscope_agent(agent_type)
        elif implementation == "custom":
            return AgentFactory._create_custom_agent(agent_type)
        else:
            raise ValueError(f"Unknown implementation: {implementation}")
    
    @staticmethod
    def _create_custom_agent(agent_type: str):
        """创建自研智能体"""
        from .custom_agents import (
            CustomRequirementAgent,
            CustomRetrievalAgent,
            CustomRecommendationAgent
        )
        
        agents = {
            "requirement": CustomRequirementAgent,
            "retrieval": CustomRetrievalAgent,
            "recommendation": CustomRecommendationAgent
        }
        
        return agents[agent_type]()
```

#### 自研核心实现

```python
# backend/agents/custom_base.py
class CustomReActAgent(BaseAgent):
    """自研 ReAct Agent"""
    
    async def run(self, input_msg: AgentMessage) -> AsyncIterator[AgentMessage]:
        """ReAct 循环"""
        max_steps = 5
        
        for step in range(max_steps):
            # 1. Thought
            thought = await self._think(input_msg)
            yield AgentMessage(
                role="assistant",
                content=thought.content,
                metadata={"type": "thought", "step": step}
            )
            
            # 2. Action
            action = self._decide_action(thought)
            
            if action.type == "final":
                # 生成最终答案
                result = await self._generate_final(thought)
                yield AgentMessage(
                    role="assistant",
                    content=result,
                    metadata={"type": "final"}
                )
                break
            
            yield AgentMessage(
                role="assistant",
                content=f"执行: {action.type}",
                metadata={"type": "action", "action": action}
            )
            
            # 3. Observation
            observation = await self._execute_action(action)
            yield AgentMessage(
                role="system",
                content=str(observation),
                metadata={"type": "observation"}
            )
            
            # 4. Reflection（可选）
            if step > 0:
                reflection = await self._reflect()
                if reflection.needs_adjustment:
                    action = reflection.adjusted_action
```

---

## 第三部分：风险评估与应对

### 风险矩阵

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|----------|
| **AgentScope 依赖风险** | 低 | 中 | 抽象接口，便于切换 |
| **LLM 成本过高** | 中 | 高 | 缓存、降级策略 |
| **响应时间变长** | 中 | 中 | 流式输出、异步化 |
| **结果不可控** | 中 | 高 | 约束规则、人工审核 |
| **团队学习成本** | 中 | 低 | 文档、培训 |

### 降级策略

```python
# backend/fallback/fallback_strategy.py
class FallbackStrategy:
    """降级策略"""
    
    async def execute_with_fallback(self, user_input: str) -> dict:
        """带降级的执行"""
        try:
            # 尝试 Agent 方案
            return await self.agent_workflow.execute(user_input)
        except Exception as e:
            logger.warning(f"Agent failed: {e}, falling back to rule-based")
            
            # 降级到规则引擎
            return await self.rule_based_recommend(user_input)
    
    async def rule_based_recommend(self, user_input: str) -> dict:
        """基于规则的传统推荐"""
        # 使用现有的推荐逻辑
        return await legacy_recommendation_service.recommend(user_input)
```

---

## 第四部分：成功指标

### 技术指标

| 指标 | 当前 | Phase 1 目标 | Phase 2 目标 |
|------|------|-------------|-------------|
| **推荐准确率** | 70% | 80% | 85% |
| **平均响应时间** | 5s | <3s | <2s |
| **对话完成率** | 60% | 80% | 90% |
| **用户满意度** | 3.5/5 | 4.2/5 | 4.5/5 |

### 业务指标

- **转化率**: 推荐→采购的转化比例
- **客单价**: 平均采购金额提升
- **复购率**: 用户重复使用推荐功能
- **人工介入率**: 需要人工调整的比例（越低越好）

---

## 第五部分：实施检查清单

### Phase 1 检查清单

- [ ] AgentScope 环境搭建完成
- [ ] RequirementAgent 实现并测试
- [ ] RetrievalAgent + 3个工具实现
- [ ] RecommendationAgent 实现
- [ ] WebSocket API 实现
- [ ] 前端 Agent Chat 界面完成
- [ ] 基础集成测试通过
- [ ] 性能基准测试完成

### Phase 2 检查清单

- [ ] 多智能体协作实现
- [ ] 记忆系统集成
- [ ] 自我反思功能实现
- [ ] 缓存策略实施
- [ ] 异步优化完成
- [ ] A/B 测试框架搭建
- [ ] 监控和日志完善

### Phase 3 检查清单（可选）

- [ ] 自研 Agent 基类实现
- [ ] AgentScope → 自研迁移完成
- [ ] 性能对比测试
- [ ] 完全脱离外部依赖

---

## 附录

### A. 参考资源

- **AgentScope 文档**: https://doc.agentscope.io/
- **ReAct Paper**: https://arxiv.org/abs/2210.03629
- **LangChain Agents**: https://python.langchain.com/docs/modules/agents/

### B. 团队分工建议

| 角色 | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| **后端开发** | Agent 实现 (2人) | 高级功能 (2人) | 自研迁移 (2人) |
| **前端开发** | Chat UI (1人) | 可视化 (1人) | 优化 (1人) |
| **算法工程师** | Prompt 调优 (1人) | 策略优化 (1人) | 模型微调 (1人) |
| **测试工程师** | 集成测试 (0.5人) | 性能测试 (0.5人) | 回归测试 (0.5人) |

### C. 预算估算

**Phase 1 (2周)**
- 人力: 3人 × 2周 = 6人周
- LLM API 调用: ¥500-1000（测试阶段）
- **总计: ~¥50,000**

**Phase 2 (2周)**
- 人力: 4人 × 2周 = 8人周
- LLM API 调用: ¥2000-3000（生产环境）
- **总计: ~¥70,000**

**Phase 3 (4周，可选)**
- 人力: 3人 × 4周 = 12人周
- **总计: ~¥90,000**

---

## 总结

本计划提供了一条从 **传统推荐系统** 到 **AgenticRAG 智能书单平台** 的清晰路径：

### 核心优势

1. **风险可控** - Phase 1 使用成熟框架快速验证
2. **渐进式演进** - 每个 Phase 都有独立价值
3. **技术先进** - 引入 ReAct、多智能体、自我反思等前沿技术
4. **业务价值** - 显著提升推荐质量和用户体验

### 关键成功因素

1. **充分的测试** - 每个阶段都要有 A/B 测试
2. **监控完善** - 实时跟踪 Agent 行为和性能
3. **用户反馈** - 快速迭代基于真实用户反馈
4. **团队培训** - 确保团队掌握 Agent 开发技能

### 下一步行动

1. **本周**: 评审本计划，确定实施细节
2. **下周**: 启动 Phase 1，搭建 AgentScope 环境
3. **Month 1 结束**: 完成 Phase 1，评估是否继续
4. **Month 2 结束**: 完成 Phase 2，上线生产环境

**预计总投入**: 4-6周，可将推荐准确率从 70% 提升到 85%，用户满意度从 3.5 提升到 4.5！
