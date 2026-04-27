"""
AgenticRAG 核心架构
实现基于 ReAct (Reasoning + Acting) 的智能体框架
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime


class ActionType(Enum):
    """智能体动作类型"""
    RETRIEVE = "retrieve"           # 向量检索
    SEARCH_DB = "search_db"         # 数据库查询
    ANALYZE = "analyze"             # 数据分析
    GENERATE = "generate"           # 生成内容
    CLARIFY = "clarify"             # 澄清需求
    RECOMMEND = "recommend"         # 推荐书单
    PLAN = "plan"                   # 制定计划
    REFLECT = "reflect"             # 反思评估


@dataclass
class Thought:
    """思考过程"""
    step: int
    content: str
    reasoning: str
    confidence: float
    timestamp: datetime


@dataclass
class Action:
    """执行动作"""
    type: ActionType
    params: Dict[str, Any]
    tool_name: Optional[str] = None
    expected_result: Optional[str] = None


@dataclass
class Observation:
    """观察结果"""
    action_type: ActionType
    result: Any
    relevance_score: float
    timestamp: datetime


class AgentMemory:
    """
    智能体记忆系统
    - 短期记忆：当前对话上下文
    - 长期记忆：用户画像、历史偏好
    - 工作记忆：任务执行中的中间结果
    """
    
    def __init__(self):
        self.short_term: List[Dict] = []      # 短期对话历史
        self.long_term: Dict[str, Any] = {}    # 长期用户画像
        self.working: Dict[str, Any] = {}      # 工作记忆
        self.max_short_term = 10
    
    def add_dialogue(self, role: str, content: str, metadata: Dict = None):
        """添加对话记录"""
        self.short_term.append({
            "role": role,
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.now()
        })
        # 保持短期记忆在限制范围内
        if len(self.short_term) > self.max_short_term:
            self._consolidate_memory()
    
    def _consolidate_memory(self):
        """整合记忆：将旧的短期记忆压缩到长期记忆"""
        old_memories = self.short_term[:5]
        self.short_term = self.short_term[5:]
        
        # 提取关键信息更新长期记忆
        # TODO: 使用LLM总结关键信息
        
    def update_user_profile(self, key: str, value: Any):
        """更新用户画像"""
        self.long_term.setdefault("user_profile", {})[key] = value
    
    def get_context(self, window: int = 5) -> str:
        """获取最近对话上下文"""
        recent = self.short_term[-window:]
        return "\n".join([f"{m['role']}: {m['content']}" for m in recent])
    
    def clear_working_memory(self):
        """清空工作记忆"""
        self.working = {}


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
    
    def register(self, name: str, func: Callable):
        """注册工具"""
        self.tools[name] = func
    
    def execute(self, tool_name: str, params: Dict) -> Any:
        """执行工具"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        return self.tools[tool_name](**params)
    
    def list_tools(self) -> List[str]:
        """列出可用工具"""
        return list(self.tools.keys())


class BookListAgent:
    """
    书单推荐智能体
    基于 ReAct 框架实现
    """
    
    def __init__(self, llm_client, vector_store, db_session):
        self.llm = llm_client
        self.vector_store = vector_store
        self.db = db_session
        self.memory = AgentMemory()
        self.tools = ToolRegistry()
        self.thoughts: List[Thought] = []
        self.actions: List[Action] = []
        self.observations: List[Observation] = []
        
        # 注册工具
        self._register_tools()
    
    def _register_tools(self):
        """注册可用工具"""
        self.tools.register("vector_search", self._vector_search)
        self.tools.register("db_query", self._db_query)
        self.tools.register("analyze_preferences", self._analyze_preferences)
        self.tools.register("generate_book_list", self._generate_book_list)
        self.tools.register("check_inventory", self._check_inventory)
    
    async def run(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """
        执行智能体主循环
        """
        # 添加用户输入到记忆
        self.memory.add_dialogue("user", user_input)
        
        # ReAct 循环
        max_iterations = 5
        for i in range(max_iterations):
            # 1. Reasoning - 思考
            thought = await self._reason(i, user_input)
            self.thoughts.append(thought)
            
            # 2. Acting - 决策动作
            action = self._decide_action(thought)
            if action.type == ActionType.GENERATE:
                # 生成最终答案，结束循环
                break
            
            self.actions.append(action)
            
            # 3. Observation - 执行并观察
            observation = await self._execute_action(action)
            self.observations.append(observation)
            
            # 4. Reflection - 反思
            if i > 0:
                await self._reflect()
        
        # 生成最终回复
        final_response = await self._generate_response()
        self.memory.add_dialogue("assistant", final_response["content"])
        
        return final_response
    
    async def _reason(self, step: int, user_input: str) -> Thought:
        """
        思考过程：分析当前状态，决定下一步行动
        使用 CoT (Chain of Thought) 提示
        """
        context = self.memory.get_context()
        working_memory = json.dumps(self.memory.working, ensure_ascii=False)
        
        prompt = f"""作为书单推荐智能体，分析当前情况并决定下一步：

用户输入：{user_input}
对话历史：
{context}

工作记忆：{working_memory}

已执行动作：{[a.type.value for a in self.actions]}

请回答：
1. 当前需求理解：用户真正想要什么？
2. 信息是否足够：是否需要更多信息？
3. 下一步行动：应该执行哪个动作？
4. 信心评分：0-1之间

以JSON格式输出：
{{
  "understanding": "需求理解",
  "sufficient": true/false,
  "next_action": "retrieve/analyze/generate/clarify",
  "reasoning": "推理过程",
  "confidence": 0.8
}}"""
        
        response = await self.llm.generate(prompt)
        result = json.loads(response)
        
        return Thought(
            step=step,
            content=result["understanding"],
            reasoning=result["reasoning"],
            confidence=result["confidence"],
            timestamp=datetime.now()
        )
    
    def _decide_action(self, thought: Thought) -> Action:
        """基于思考结果决定动作"""
        # 如果信心低，需要澄清
        if thought.confidence < 0.5:
            return Action(
                type=ActionType.CLARIFY,
                params={"reason": thought.reasoning}
            )
        
        # 根据推理决定动作
        if "分类" in thought.content or "主题" in thought.content:
            return Action(
                type=ActionType.RETRIEVE,
                params={"query": thought.content, "top_k": 10},
                tool_name="vector_search"
            )
        
        if "库存" in thought.content or "价格" in thought.content:
            return Action(
                type=ActionType.SEARCH_DB,
                params={"query": thought.content},
                tool_name="db_query"
            )
        
        # 默认生成书单
        return Action(
            type=ActionType.GENERATE,
            params={"thought": thought.content}
        )
    
    async def _execute_action(self, action: Action) -> Observation:
        """执行动作并返回观察结果"""
        if action.tool_name:
            result = self.tools.execute(action.tool_name, action.params)
        else:
            result = await self._execute_internal_action(action)
        
        # 存储到工作记忆
        self.memory.working[f"action_{action.type.value}"] = result
        
        return Observation(
            action_type=action.type,
            result=result,
            relevance_score=0.8,  # TODO: 计算相关性
            timestamp=datetime.now()
        )
    
    async def _execute_internal_action(self, action: Action) -> Any:
        """执行内部动作"""
        if action.type == ActionType.CLARIFY:
            return {"question": "能否详细说明您的阅读偏好？"}
        return {}
    
    async def _reflect(self):
        """
        反思：评估之前的行动是否有效
        使用 Self-Reflection 技术
        """
        if len(self.observations) < 2:
            return
        
        last_obs = self.observations[-1]
        prev_obs = self.observations[-2]
        
        # 如果结果没有改进，调整策略
        if last_obs.relevance_score <= prev_obs.relevance_score:
            # 需要改变策略
            self.memory.working["strategy_change"] = True
    
    async def _generate_response(self) -> Dict[str, Any]:
        """生成最终回复"""
        # 整合所有信息
        context = {
            "thoughts": [t.content for t in self.thoughts],
            "observations": [o.result for o in self.observations],
            "working_memory": self.memory.working
        }
        
        prompt = f"""基于以下信息生成书单推荐：

思考过程：{context['thoughts']}
检索结果：{context['observations']}

请生成：
1. 推荐书单（10-20本书）
2. 推荐理由
3. 分类占比分析
4. 预算估算

以JSON格式输出。"""
        
        response = await self.llm.generate(prompt)
        
        return {
            "content": response,
            "recommendations": json.loads(response),
            "actions_taken": [a.type.value for a in self.actions],
            "confidence": self.thoughts[-1].confidence if self.thoughts else 0.5
        }
    
    # ========== 工具函数 ==========
    
    def _vector_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """向量检索工具"""
        # 调用现有向量搜索
        return self.vector_store.search(query, top_k)
    
    def _db_query(self, query: str) -> List[Dict]:
        """数据库查询工具"""
        # 查询数据库
        return []
    
    def _analyze_preferences(self, history: List[Dict]) -> Dict:
        """分析用户偏好"""
        # 分析用户历史行为
        return {}
    
    def _generate_book_list(self, requirements: Dict) -> Dict:
        """生成书单"""
        # 调用现有书单生成逻辑
        return {}
    
    def _check_inventory(self, book_ids: List[int]) -> Dict:
        """检查库存"""
        # 查询库存状态
        return {}


class MultiAgentSystem:
    """
    多智能体协作系统
    - 需求分析智能体
    - 检索智能体
    - 推荐智能体
    - 评估智能体
    """
    
    def __init__(self):
        self.agents: Dict[str, BookListAgent] = {}
        self.orchestrator = None  # 协调器
    
    def register_agent(self, name: str, agent: BookListAgent):
        """注册智能体"""
        self.agents[name] = agent
    
    async def collaborative_recommend(self, user_input: str) -> Dict:
        """
        多智能体协作推荐
        """
        # 1. 需求分析智能体
        requirement_agent = self.agents.get("requirement")
        req_result = await requirement_agent.run(user_input)
        
        # 2. 检索智能体并行检索
        retrieval_agent = self.agents.get("retrieval")
        # TODO: 并行检索
        
        # 3. 推荐智能体生成书单
        recommend_agent = self.agents.get("recommend")
        final_result = await recommend_agent.run(
            user_input,
            context=req_result
        )
        
        # 4. 评估智能体验证
        eval_agent = self.agents.get("evaluation")
        evaluation = await eval_agent.evaluate(final_result)
        
        return {
            "recommendation": final_result,
            "evaluation": evaluation,
            "process": "multi-agent"
        }
