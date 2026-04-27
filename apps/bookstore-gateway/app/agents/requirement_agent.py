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
from ..constants.keywords_config import (
    TARGET_AUDIENCE_OCCUPATION,
    TARGET_AUDIENCE_AGE,
    READING_LEVEL,
    BOOK_CATEGORIES,
    CONSTRAINT_KEYWORDS,
    CONFIDENCE_THRESHOLD,
    CLARIFICATION_QUESTIONS,
)


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

重要规则：
- 如果信息不足，不要使用"通用"、"综合"等兜底词汇
- 置信度低于 0.5 时，必须要求用户澄清
- 针对性地提出澄清问题，而不是笼统的提问
- 当识别到职业信息时，相应推断其可能的阅读偏好

输出格式（必须有效的JSON）：
{
  "target_audience": {
    "occupation": "职业（程序员/教师/大学生/产品经理等，未知则填'未识别'）",
    "age_group": "年龄段（儿童/青少年/成人/老年，未知则填'未识别'）",
    "reading_level": "阅读水平（入门/进阶/高级/学术，未知则填'未识别'）"
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
  "clarification_questions": ["具体的澄清问题"]
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
        """
        基于关键词配置的启发式需求分析

        优化策略：
        1. 使用扩展的关键词配置进行多维度识别
        2. 计算匹配度得分，动态调整置信度
        3. 移除通用兜底文案，强制澄清
        4. 提供针对性的澄清引导
        """
        text = user_input.lower()

        # 分析目标受众 - 职业维度
        occupation = None
        occupation_match_count = 0
        for occ, keywords in TARGET_AUDIENCE_OCCUPATION.items():
            match_count = sum(1 for kw in keywords if kw.lower() in text)
            if match_count > occupation_match_count:
                occupation = occ
                occupation_match_count = match_count

        # 分析目标受众 - 年龄维度
        age_group = None
        for age, keywords in TARGET_AUDIENCE_AGE.items():
            if any(kw.lower() in text for kw in keywords):
                age_group = age
                break

        # 分析阅读水平
        reading_level = None
        for level, keywords in READING_LEVEL.items():
            if any(kw.lower() in text for kw in keywords):
                reading_level = level
                break

        # 分析书籍分类
        categories: List[Dict[str, Any]] = []
        matched_categories = {}
        for category, keywords in BOOK_CATEGORIES.items():
            match_count = sum(1 for kw in keywords if kw.lower() in text)
            if match_count > 0:
                matched_categories[category] = match_count

        # 根据匹配度分配百分比
        if matched_categories:
            total_matches = sum(matched_categories.values())
            for category, matches in matched_categories.items():
                percentage = max(10, round((matches / total_matches) * 100))
                categories.append({"name": category, "percentage": percentage})

        # 分析约束条件
        budget = None
        budget_match = re.search(r"(\d+(?:\.\d+)?)\s*元", user_input)
        if budget_match:
            budget = float(budget_match.group(1))

        exclude_textbooks = any(
            kw in text for kw in CONSTRAINT_KEYWORDS.get("exclude_textbooks", [])
        )

        # 提取关键词
        keywords = []
        for category_list in BOOK_CATEGORIES.values():
            for kw in category_list:
                if kw.lower() in text and len(kw) > 1:
                    keywords.append(kw)

        # 计算置信度
        confidence_factors = {
            "occupation": 0.25 if occupation else 0,
            "age": 0.15 if age_group else 0,
            "level": 0.15 if reading_level else 0,
            "categories": 0.30 if categories else 0,
            "budget": 0.10 if budget else 0,
            "base": 0.05,
        }
        confidence = sum(confidence_factors.values())

        # 生成澄清问题
        questions = []

        if confidence < CONFIDENCE_THRESHOLD["LOW"]:
            # 低置信度，需要全面澄清
            questions.append(CLARIFICATION_QUESTIONS["general"])
        else:
            # 针对性澄清
            if not occupation:
                questions.append(CLARIFICATION_QUESTIONS["occupation"])
            if not age_group:
                questions.append(CLARIFICATION_QUESTIONS["age"])
            if not reading_level:
                questions.append(CLARIFICATION_QUESTIONS["level"])
            if not categories:
                questions.append(CLARIFICATION_QUESTIONS["category"])
            if not budget and confidence < CONFIDENCE_THRESHOLD["MEDIUM"]:
                questions.append(CLARIFICATION_QUESTIONS["budget"])

        # 构建目标受众
        target_audience = {
            "occupation": occupation or "未识别",
            "age_group": age_group or "未识别",
            "reading_level": reading_level or "未识别",
        }

        # 构建约束
        constraints = {
            "budget": budget,
            "exclude_textbooks": exclude_textbooks,
            "other": [],
        }

        # 如果置信度太低，添加强制澄清标记
        needs_clarification = confidence < CONFIDENCE_THRESHOLD["MEDIUM"] or bool(questions)

        return RequirementAnalysis(
            target_audience=target_audience,
            categories=categories if categories else [],
            keywords=keywords[:10],  # 限制关键词数量
            constraints=constraints,
            confidence=round(confidence, 2),
            needs_clarification=needs_clarification,
            clarification_questions=questions if len(questions) <= 3 else questions[:3],
        )


class BookListRequirementAgent(RequirementAgent):
    """书单需求分析专用 Agent（别名）"""
    pass


async def _demo() -> None:
    """
    本地调试示例 - 演示优化后的需求分析功能
    """
    if not HAS_AGENTSCOPE:
        print("agentscope not installed, running optimized heuristic demo")
        agent = RequirementAgent()

        # 测试用例：展示优化效果
        test_cases = [
            "我想为大学生生成一份编程入门书单，预算500元",
            "程序员想学习人工智能和机器学习",
            "给小孩子看的历史和科普书",
            "产品经理需要什么书",
            "推荐几本书",  # 模糊输入，测试澄清
        ]

        print("\n" + "=" * 60)
        print("优化后的需求分析演示")
        print("=" * 60)

        for i, test_input in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}: {test_input}")
            print("-" * 60)

            result = await agent.analyze(test_input)

            print(f"目标受众: {result.target_audience}")
            print(f"书籍分类: {result.categories}")
            print(f"关键词: {result.keywords[:5]}")  # 只显示前5个
            print(f"约束条件: {result.constraints}")
            print(f"置信度: {result.confidence}")
            print(f"需要澄清: {result.needs_clarification}")
            if result.needs_clarification:
                print(f"澄清问题: {result.clarification_questions}")

        print("\n" + "=" * 60)
        print("演示完成")
        print("=" * 60)
        return

    # 配置模型（使用 AgentScope）
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
