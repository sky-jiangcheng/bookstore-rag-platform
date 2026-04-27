# AgenticRAG 重构方案

## 1. 什么是 AgenticRAG？

AgenticRAG 是一种结合了**智能体（Agent）**和**检索增强生成（RAG）**的先进架构。不同于传统 RAG 的单轮检索+生成，AgenticRAG 引入了智能体的自主决策能力。

### 核心能力

| 能力 | 说明 | 本项目应用 |
|------|------|-----------|
| **自主规划** | 能分解复杂任务为多步骤 | 复杂书单需求拆解 |
| **工具调用** | 动态选择检索策略 | 向量检索+数据库+API |
| **反思改进** | 评估结果并优化 | 书单质量自评估 |
| **长期记忆** | 学习用户偏好 | 个性化推荐 |
| **多轮对话** | 持续澄清需求 | 交互式书单生成 |

---

## 2. 本项目现状评估

### 当前架构（已完成改进）

```
用户输入 → 需求解析 → 向量检索 → LLM生成 → 书单输出
              ↓
         多轮对话（简单）
```

**优势：**
- ✅ Pinia Store 状态管理
- ✅ 组件化架构
- ✅ 向量检索已集成
- ✅ 基础多轮对话

**不足：**
- ❌ 缺乏自主规划能力
- ❌ 工具调用单一（仅向量搜索）
- ❌ 无自我反思机制
- ❌ 长期记忆能力弱

---

## 3. AgenticRAG 重构方案

### Phase 1: 核心智能体架构（2周）

#### 3.1 后端改造

```python
# 新增文件结构
backend/app/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # 基础智能体
│   ├── requirement_agent.py   # 需求分析智能体
│   ├── retrieval_agent.py     # 检索智能体
│   ├── recommendation_agent.py # 推荐智能体
│   └── evaluation_agent.py    # 评估智能体
├── tools/
│   ├── __init__.py
│   ├── vector_tool.py         # 向量检索工具
│   ├── db_tool.py             # 数据库查询工具
│   ├── web_tool.py            # 外部API工具
│   └── inventory_tool.py      # 库存检查工具
├── memory/
│   ├── __init__.py
│   ├── short_term.py          # 短期记忆
│   ├── long_term.py           # 长期记忆
│   └── user_profile.py        # 用户画像
└── reasoning/
    ├── __init__.py
    ├── react.py               # ReAct框架
    ├── cot.py                 # Chain of Thought
    └── reflection.py          # 自我反思
```

#### 3.2 前端改造

```javascript
// 新增 Pinia Store
frontend/src/stores/
├── agentStore.js              // 智能体状态管理
├── memoryStore.js             // 记忆管理
└── toolStore.js               // 工具调用

// 新增组件
frontend/src/components/agent/
├── AgentChat.vue              // 智能体对话界面
├── ReasoningChain.vue         // 推理链展示
├── ToolCallPanel.vue          // 工具调用面板
└── ReflectionPanel.vue        // 反思过程展示
```

### Phase 2: 多智能体协作（2周）

#### 多智能体架构

```
用户输入
    ↓
┌─────────────────────────────────────────┐
│  Orchestrator（协调器）                   │
│  - 分析需求复杂度                         │
│  - 分配任务给不同智能体                   │
└─────────────────────────────────────────┘
    ↓
    ├─────────────┬─────────────┬─────────────┐
    ↓             ↓             ↓             ↓
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│需求分析 │→ │多源检索 │→ │书单生成 │→ │质量评估 │
│智能体  │  │智能体  │  │智能体  │  │智能体  │
└────────┘  └────────┘  └────────┘  └────────┘
    │             │             │             │
    └─────────────┴─────────────┴─────────────┘
                      ↓
              最终书单输出
```

### Phase 3: 高级功能（2周）

#### 高级特性

1. **自适应检索策略**
   - 根据需求选择检索方式
   - 向量检索 vs 数据库查询 vs 混合检索

2. **动态书单优化**
   - 实时库存检查
   - 预算自动调整
   - 分类比例优化

3. **用户画像学习**
   - 历史行为分析
   - 偏好持续学习
   - 个性化权重调整

---

## 4. 具体实施步骤

### Week 1-2: 基础架构

**Day 1-3: 智能体核心**
```python
# 1. 创建基础智能体类
class BaseAgent:
    def __init__(self, llm, memory, tools):
        self.llm = llm
        self.memory = memory
        self.tools = tools
    
    async def run(self, input) -> Output:
        # ReAct 循环
        for step in range(max_steps):
            thought = await self._think()
            action = self._decide_action(thought)
            observation = await self._execute(action)
            if action.is_final:
                break
        return self._generate_output()
```

**Day 4-7: 工具系统**
```python
# 2. 实现工具注册和调用
class ToolRegistry:
    def register(self, name, func):
        self.tools[name] = func
    
    async def execute(self, tool_name, params):
        return await self.tools[tool_name](**params)

# 注册现有功能为工具
registry.register("vector_search", vector_search_service)
registry.register("db_query", database_service)
registry.register("check_inventory", inventory_service)
```

**Day 8-14: 记忆系统**
```python
# 3. 实现记忆管理
class AgentMemory:
    def __init__(self):
        self.short_term = []  # 最近10轮对话
        self.long_term = {}   # 用户画像
        self.working = {}     # 工作记忆
    
    def consolidate(self):
        # 将短期记忆压缩到长期记忆
        pass
```

### Week 3-4: 多智能体协作

**需求分析智能体**
```python
class RequirementAgent(BaseAgent):
    """专门分析用户需求的智能体"""
    
    async def analyze(self, user_input):
        # 1. 理解显性需求
        explicit_reqs = await self._extract_explicit(user_input)
        
        # 2. 挖掘隐性需求
        implicit_reqs = await self._infer_implicit(user_input)
        
        # 3. 评估需求完整性
        completeness = self._assess_completeness(explicit_reqs, implicit_reqs)
        
        if completeness < 0.7:
            # 需要澄清
            return Action(type="clarify", questions=[...])
        
        return RequirementSpec(...)
```

**检索智能体**
```python
class RetrievalAgent(BaseAgent):
    """智能检索智能体"""
    
    async def retrieve(self, requirements):
        # 根据需求类型选择检索策略
        if requirements.is_specific:
            # 精确检索
            results = await self.tools["db_query"](requirements)
        else:
            # 语义检索
            results = await self.tools["vector_search"](requirements)
        
        # 多路召回融合
        fused_results = self._fusion_retrieval(results)
        
        # 相关性重排序
        reranked = await self._rerank(fused_results)
        
        return reranked
```

**推荐智能体**
```python
class RecommendationAgent(BaseAgent):
    """书单生成智能体"""
    
    async def generate(self, requirements, candidates):
        # 1. 分类配比规划
        category_plan = self._plan_categories(requirements)
        
        # 2. 书籍选择
        selected_books = []
        for category, count in category_plan.items():
            books = self._select_from_category(candidates, category, count)
            selected_books.extend(books)
        
        # 3. 质量检查
        quality_score = await self._evaluate_quality(selected_books)
        
        if quality_score < 0.8:
            # 需要重新检索
            return Action(type="re_retrieve", feedback="质量不足")
        
        return BookList(books=selected_books, reasoning=...)
```

### Week 5-6: 高级功能

**自我反思机制**
```python
class SelfReflection:
    """智能体自我反思"""
    
    async def reflect(self, action_history, result):
        reflection_prompt = f"""
        请评估刚才的书单推荐：
        1. 分类是否合理？
        2. 是否有更好的选择？
        3. 用户可能会喜欢吗？
        4. 如何改进？
        """
        
        reflection = await self.llm.generate(reflection_prompt)
        
        if reflection.needs_improvement:
            return ImprovementPlan(...)
```

**用户画像学习**
```python
class UserProfileLearner:
    """从交互中学习用户偏好"""
    
    def learn_from_feedback(self, book_list, user_feedback):
        # 更新用户画像
        if user_feedback.liked:
            self.user_profile.preferred_categories.append(
                book_list.main_category
            )
        
        if user_feedback.disliked:
            self.user_profile.excluded_categories.append(
                book_list.main_category
            )
        
        # 学习价格敏感度
        self.user_profile.price_sensitivity = self._analyze_price_preference(
            book_list, user_feedback
        )
```

---

## 5. API 设计

### 新 API 端点

```python
# 智能体对话 API
@router.post("/v2/agent/chat")
async def agent_chat(request: AgentChatRequest):
    """
    与智能体进行多轮对话
    """
    agent = BookListAgent(
        session_id=request.session_id,
        user_id=request.user_id
    )
    
    result = await agent.run(request.message)
    
    return {
        "response": result.content,
        "reasoning_chain": result.thoughts,
        "actions_taken": result.actions,
        "recommended_books": result.recommendations,
        "needs_clarification": result.needs_clarification
    }

# 智能体状态 API
@router.get("/v2/agent/{session_id}/status")
async def get_agent_status(session_id: str):
    """
    获取智能体当前状态和思考过程
    """
    agent = get_agent_by_session(session_id)
    
    return {
        "current_step": agent.current_step,
        "thought_history": agent.thoughts,
        "memory_summary": agent.memory.get_summary(),
        "confidence_score": agent.confidence
    }
```

---

## 6. 前端改造

### 新增交互界面

```vue
<!-- AgentChat.vue -->
<template>
  <div class="agent-chat">
    <!-- 推理链展示 -->
    <ReasoningChain :thoughts="agentStore.thoughts" />
    
    <!-- 工具调用展示 -->
    <ToolCallPanel :actions="agentStore.actions" />
    
    <!-- 对话区域 -->
    <ChatArea 
      :messages="agentStore.messages"
      @send="handleSend"
    />
    
    <!-- 实时书单预览 -->
    <LiveBookListPreview 
      :books="agentStore.currentRecommendations"
    />
  </div>
</template>
```

### 新增 Pinia Store

```javascript
// agentStore.js
export const useAgentStore = defineStore('agent', {
  state: () => ({
    sessionId: null,
    messages: [],
    thoughts: [],      // 推理过程
    actions: [],       // 工具调用
    isThinking: false,
    currentRecommendations: [],
    needsClarification: false
  }),
  
  actions: {
    async sendMessage(message) {
      this.isThinking = true
      
      const response = await api.post('/v2/agent/chat', {
        session_id: this.sessionId,
        message: message
      })
      
      // 更新推理链
      this.thoughts = response.reasoning_chain
      this.actions = response.actions_taken
      this.currentRecommendations = response.recommended_books
      
      this.isThinking = false
    }
  }
})
```

---

## 7. 性能优化

### 7.1 异步并行

```python
# 并行检索
async def parallel_retrieval(requirements):
    tasks = [
        vector_search(requirements),
        db_query(requirements),
        check_popular_books(requirements)
    ]
    
    results = await asyncio.gather(*tasks)
    return merge_results(results)
```

### 7.2 缓存策略

```python
# 缓存用户画像和常见查询
@cache.memoize(timeout=3600)
async def get_user_profile(user_id):
    return await load_user_profile(user_id)

@cache.memoize(timeout=300)
async def semantic_search(query):
    return await vector_search(query)
```

### 7.3 流式响应

```python
# SSE 流式返回推理过程
@app.get("/v2/agent/stream")
async def agent_stream(request: Request):
    async def event_generator():
        agent = BookListAgent()
        
        async for step in agent.run_streaming(request.message):
            yield f"data: {json.dumps(step)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

---

## 8. 评估指标

### 8.1 技术指标

| 指标 | 当前 | 目标 | 测量方式 |
|------|------|------|----------|
| 推荐准确率 | 70% | 85% | 用户反馈 |
| 响应时间 | 5s | <3s | API监控 |
| 多轮对话完成率 | 60% | 90% | 会话统计 |
| 用户满意度 | 3.5/5 | 4.5/5 | 评分系统 |

### 8.2 业务指标

- **转化率**：从推荐到采购的转化率
- **客单价**：平均采购金额
- **复购率**：用户重复使用推荐功能的频率
- **对话轮数**：完成任务所需的平均对话轮数

---

## 9. 实施路线图

### Month 1: MVP
- ✅ 基础智能体架构
- ✅ ReAct框架实现
- ✅ 简单工具调用

### Month 2: 增强
- ✅ 多智能体协作
- ✅ 记忆系统完善
- ✅ 自我反思机制

### Month 3: 优化
- ✅ 用户画像学习
- ✅ 性能优化
- ✅ A/B测试

---

## 10. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LLM成本增加 | 高 | 缓存、降级策略 |
| 响应时间变长 | 中 | 流式输出、并行化 |
| 结果不可控 | 中 | 人工审核、约束规则 |
| 用户学习成本 | 低 | 渐进式引导 |

---

## 总结

AgenticRAG 将使本项目从"简单的推荐系统"升级为"智能书单助手"。通过引入智能体的自主决策、多轮对话和持续学习能力，能够：

1. **更懂用户** - 通过多轮对话深入理解需求
2. **更智能** - 自主规划、工具调用、自我改进
3. **更个性化** - 长期学习用户偏好
4. **更可靠** - 自我反思和质量评估

预计开发周期：**6周**，可显著提升推荐质量和用户体验。
