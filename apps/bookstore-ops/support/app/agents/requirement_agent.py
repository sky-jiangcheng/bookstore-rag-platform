"""
智能体模块
基于 AgentScope 的书单推荐智能体实现
"""

from typing import Dict, List, Any, Optional, AsyncIterator
import json
import logging
import re

logger = logging.getLogger(__name__)

try:
    import agentscope
    from agentscope.agent import ReActAgent
    from agentscope.message import Msg
    from agentscope.formatter import OpenAIChatFormatter

    HAS_AGENTSCOPE = True
except ImportError:
    agentscope = None
    ReActAgent = object
    Msg = None
    OpenAIChatFormatter = None
    HAS_AGENTSCOPE = False
    logger.warning("agentscope not installed, RequirementAgent will use heuristic fallback")

from .models import RequirementAnalysis


class RequirementAgent(ReActAgent):
    """
    需求分析智能体
    分析用户的书单需求，提取结构化信息
    """
    
    def __init__(self, model_config: Dict = None):
        self.model_config = model_config or {}
        self._fallback_mode = not HAS_AGENTSCOPE
        if isinstance(self.model_config, dict):
            self._default_model = self.model_config.get(
                "model_name",
                self.model_config.get("model", "gpt-4"),
            )
        else:
            self._default_model = self.model_config or "gpt-4"

        if not HAS_AGENTSCOPE:
            return

        # 默认使用 OpenAI GPT-4，可配置为其他模型
        sys_prompt = """你是专业的图书需求分析助手。

任务：分析用户的阅读需求，提取以下信息：
1. 目标受众：职业、年龄段、阅读水平
2. 书籍分类：主题类别及占比
3. 关键词：核心主题词
4. 约束条件：预算、排除项、特殊要求
5. 需求完整性评分（0-1）

如果需求不完整，提出澄清问题。

输出格式（必须有效的JSON）：
{
  "target_audience": {
    "occupation": "职业（学生/程序员/教师/通用）",
    "age_group": "年龄段（儿童/青少年/成人/老年）",
    "reading_level": "阅读水平（入门/进阶/高级）"
  },
  "categories": [
    {"name": "分类名", "percentage": 30}
  ],
  "keywords": ["关键词1", "关键词2"],
  "constraints": {
    "budget": 500,
    "exclude_textbooks": false,
    "other": ["其他约束"]
  },
  "confidence": 0.85,
  "needs_clarification": false,
  "clarification_questions": []
}"""
        
        super().__init__(
            name="RequirementAgent",
            sys_prompt=sys_prompt,
            model=self._default_model,
            formatter=OpenAIChatFormatter()
        )
    
    async def analyze(self, user_input: str) -> RequirementAnalysis:
        """
        分析用户需求
        
        Args:
            user_input: 用户原始输入
            
        Returns:
            RequirementAnalysis: 结构化需求分析结果
        """
        if self._fallback_mode:
            return self._heuristic_analyze(user_input)

        if Msg is None:
            return self._heuristic_analyze(user_input)

        # 构建用户消息
        msg = Msg(
            name="user",
            content=user_input,
            role="user"
        )
        
        # 调用 Agent 生成回复（使用 await 等待协程执行）
        try:
            response = await self.reply(msg)

            # 解析 JSON 响应
            result = json.loads(response.content)
            return RequirementAnalysis(**result)
        except (json.JSONDecodeError, TypeError, ValueError, AttributeError, Exception) as exc:
            logger.warning("RequirementAgent agent-mode failed, using heuristic fallback: %s", exc)
            # Agent 模式失败时优先返回可执行的结果，避免整条 RAG 链路中断
            return self._heuristic_analyze(user_input, low_confidence=False)
    
    async def analyze_streaming(self, user_input: str) -> AsyncIterator[Dict]:
        """
        流式分析用户需求，实时返回思考过程
        
        Args:
            user_input: 用户原始输入
            
        Yields:
            Dict: 包含类型和内容的字典
        """
        # 发送开始分析的消息
        yield {
            "type": "thought",
            "content": "正在分析您的需求...",
            "step": 1
        }
        
        # 分析受众
        yield {
            "type": "thought", 
            "content": "识别目标受众...",
            "step": 2
        }
        
        # 分析分类
        yield {
            "type": "thought",
            "content": "提取书籍分类...",
            "step": 3
        }
        
        # 实际分析（使用 await 等待协程执行）
        result = await self.analyze(user_input)
        
        # 发送结果
        yield {
            "type": "result",
            "content": "需求分析完成",
            "data": {
                "target_audience": result.target_audience,
                "categories": result.categories,
                "keywords": result.keywords,
                "constraints": result.constraints,
                "confidence": result.confidence,
                "needs_clarification": result.needs_clarification,
                "clarification_questions": result.clarification_questions
            }
        }

    def _heuristic_analyze(
        self,
        user_input: str,
        low_confidence: bool = False
    ) -> RequirementAnalysis:
        """当 AgentScope 不可用或解析失败时，使用简单启发式解析。"""
        text = user_input.lower()

        target_audience = "通用"
        if any(keyword in text for keyword in ["大学", "学生", "本科", "研究生"]):
            target_audience = "大学生"
        elif any(keyword in text for keyword in ["孩子", "儿童", "小学生"]):
            target_audience = "儿童"
        elif any(keyword in text for keyword in ["程序员", "开发", "编程", "python", "算法"]):
            target_audience = "程序员"

        categories: List[Dict[str, Any]] = []
        category_keywords = [
            ("编程", ["编程", "python", "java", "代码", "开发"]),
            ("算法", ["算法", "数据结构", "leetcode"]),
            ("历史", ["历史", "朝代", "古代"]),
            ("科普", ["科普", "科学", "自然"]),
            ("传记", ["传记", "人物", "自传"]),
        ]
        for name, keywords in category_keywords:
            if any(keyword in text for keyword in keywords):
                categories.append({"name": name, "percentage": 25})

        if not categories:
            categories = [{"name": "综合", "percentage": 100}]

        budget_match = re.search(r"(\d+(?:\.\d+)?)\s*元", user_input)
        budget = float(budget_match.group(1)) if budget_match else None

        questions = []
        if low_confidence or target_audience == "通用":
            questions.append("能否更详细地描述您的阅读需求？例如目标读者、主题和预算范围。")

        return RequirementAnalysis(
            target_audience={
                "occupation": target_audience,
                "age_group": "成人" if target_audience != "儿童" else "儿童",
                "reading_level": "通用",
            },
            categories=categories,
            keywords=[w for w in ["编程", "算法", "历史", "科普", "传记"] if w in user_input],
            constraints={"budget": budget, "exclude_textbooks": False, "other": []},
            confidence=0.35 if low_confidence else 0.55,
            needs_clarification=bool(questions),
            clarification_questions=questions,
        )


class BookListRequirementAgent(RequirementAgent):
    """书单需求分析专用 Agent（别名）"""
    pass


async def _demo() -> None:
    """本地调试示例。"""
    if not HAS_AGENTSCOPE:
        print("agentscope not installed, running fallback demo")
        agent = RequirementAgent()
        result = await agent.analyze("我想为大学生生成一份编程入门书单，预算500元")
        print("分析结果:")
        print(f"目标受众: {result.target_audience}")
        print(f"分类: {result.categories}")
        print(f"置信度: {result.confidence}")
        print(f"需要澄清: {result.needs_clarification}")
        return

    # 配置模型
    agentscope.init(
        model_configs=[
            {
                "model_type": "openai",
                "model_name": "gpt-4",
                "api_key": "${OPENAI_API_KEY}",
            }
        ]
    )

    # 创建 Agent
    agent = RequirementAgent()

    # 测试
    test_input = "我想为大学生生成一份包含编程、算法、数据结构的书单，预算在500元以内"
    result = await agent.analyze(test_input)

    print("分析结果:")
    print(f"目标受众: {result.target_audience}")
    print(f"分类: {result.categories}")
    print(f"置信度: {result.confidence}")
    print(f"需要澄清: {result.needs_clarification}")


# 初始化示例
if __name__ == "__main__":
    import asyncio

    asyncio.run(_demo())
