"""
智能书单适配器
将现有智能书单API与AgenticRAG架构桥接
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.models import RequirementAnalysis
from app.api.v1.book_list.schemas import (
    BookRecommendation,
    CategoryRequirement,
    ParsedRequirements
)

logger = logging.getLogger(__name__)


class BookListAgentAdapter:
    """
    适配器模式：将现有智能书单需求转换为Agent格式
    保持与现有API的数据模型兼容
    """

    @classmethod
    def convert_requirements(cls, parsed_reqs: ParsedRequirements) -> Dict[str, Any]:
        """
        将现有ParsedRequirements转换为Agent需求格式

        Args:
            parsed_reqs: 解析后的需求

        Returns:
            Dict: Agent可用的需求格式
        """
        try:
            # 转换分类
            categories = []
            if parsed_reqs.categories:
                for cat in parsed_reqs.categories:
                    categories.append(
                        {
                            "name": cat.category,
                            "percentage": cat.percentage,
                            "count": cat.count,
                        }
                    )

            # 构建目标受众
            target_audience = {
                "occupation": parsed_reqs.target_audience or "通用",
                "age_group": cls._map_cognitive_level(parsed_reqs.cognitive_level),
                "reading_level": parsed_reqs.cognitive_level or "通用",
            }

            # 构建约束条件
            constraints = {
                "budget": None,  # 可以从历史学习
                "exclude_textbooks": parsed_reqs.exclude_textbooks,
                "min_cognitive_level": parsed_reqs.min_cognitive_level,
                "max_cognitive_level": None,
                "preferred_publishers": [],
                "avoided_publishers": [],
                "other": parsed_reqs.constraints or [],
            }

            # 动态计算置信度
            confidence = cls._calculate_confidence(parsed_reqs)

            return {
                "target_audience": target_audience,
                "categories": categories,
                "keywords": parsed_reqs.keywords or [],
                "constraints": constraints,
                "confidence": confidence,
                "needs_clarification": False,
                "clarification_questions": [],
            }
        except Exception as e:
            logger.error(f"转换需求失败: {str(e)}")
            # 返回默认值
            return {
                "target_audience": {
                    "occupation": "通用",
                    "age_group": "成人",
                    "reading_level": "通用",
                },
                "categories": [],
                "keywords": [],
                "constraints": {
                    "budget": None,
                    "exclude_textbooks": True,
                    "min_cognitive_level": None,
                    "max_cognitive_level": None,
                    "preferred_publishers": [],
                    "avoided_publishers": [],
                    "other": [],
                },
                "confidence": 0.5,
                "needs_clarification": True,
                "clarification_questions": ["需求解析失败，请重新输入"],
            }

    @classmethod
    def convert_to_requirement_analysis(
        cls, parsed_reqs: ParsedRequirements
    ) -> RequirementAnalysis:
        """
        转换为RequirementAnalysis对象（用于Agent）

        Args:
            parsed_reqs: 解析后的需求

        Returns:
            RequirementAnalysis: Agent需求分析对象
        """
        try:
            agent_req = cls.convert_requirements(parsed_reqs)

            return RequirementAnalysis(
                target_audience=agent_req["target_audience"],
                categories=agent_req["categories"],
                keywords=agent_req["keywords"],
                constraints=agent_req["constraints"],
                confidence=agent_req["confidence"],
                needs_clarification=agent_req["needs_clarification"],
                clarification_questions=agent_req["clarification_questions"],
            )
        except Exception as e:
            logger.error(f"转换为RequirementAnalysis失败: {str(e)}")
            # 返回默认值
            return RequirementAnalysis(
                target_audience={"occupation": "通用", "age_group": "成人", "reading_level": "通用"},
                categories=[],
                keywords=[],
                constraints={"budget": None, "exclude_textbooks": True, "min_cognitive_level": None, "max_cognitive_level": None, "preferred_publishers": [], "avoided_publishers": [], "other": []},
                confidence=0.5,
                needs_clarification=True,
                clarification_questions=["需求分析失败，请重新输入"],
            )

    @classmethod
    def convert_booklist_result(
        cls, agent_result: Dict[str, Any], parsed_reqs: ParsedRequirements
    ) -> List[BookRecommendation]:
        """
        将Agent结果转换为现有BookRecommendation格式

        Args:
            agent_result: Agent生成的书单结果
            parsed_reqs: 原始需求

        Returns:
            List[BookRecommendation]: 标准书单格式
        """
        try:
            recommendations = []
            booklist = agent_result.get("booklist", {})
            books = booklist.get("books", [])

            for book_data in books:
                # 计算匹配分数
                match_score = book_data.get("relevance_score", 0.8)

                # 生成备注
                remark = None
                if book_data.get("stock", 0) < 10:
                    remark = "库存较少"

                # 安全访问price字段
                price = None
                try:
                    price_str = book_data.get("price")
                    if price_str:
                        price = float(price_str)
                except (ValueError, TypeError):
                    logger.warning(f"价格转换失败: {book_data.get('price')}")

                recommendation = BookRecommendation(
                    book_id=book_data.get("book_id", 0),
                    barcode=book_data.get("barcode", ""),
                    title=book_data.get("title", ""),
                    author=book_data.get("author"),
                    publisher=book_data.get("publisher"),
                    price=price,
                    stock=book_data.get("stock", 0),
                    category=book_data.get("category", "通用"),
                    cognitive_level=book_data.get("cognitive_level"),
                    difficulty_level=book_data.get("difficulty_level"),
                    match_score=match_score,
                    remark=remark,
                )
                recommendations.append(recommendation)

            return recommendations
        except Exception as e:
            logger.error(f"转换书单结果失败: {str(e)}")
            return []

    @classmethod
    def convert_agent_result_to_response(
        cls,
        agent_result: Dict[str, Any],
        parsed_reqs: ParsedRequirements,
        request_id: Optional[str] = None,
        session_id: Optional[int] = None,
        generation_time_ms: int = 0,
    ) -> Dict[str, Any]:
        """
        将Agent结果转换为API响应格式

        Args:
            agent_result: Agent生成的结果
            parsed_reqs: 解析后的需求
            request_id: 请求ID
            session_id: 会话ID
            generation_time_ms: 生成耗时

        Returns:
            Dict: API响应格式
        """
        try:
            recommendations = cls.convert_booklist_result(agent_result, parsed_reqs)
            booklist = agent_result.get("booklist", {})

            # 计算分类分布
            category_distribution = booklist.get("category_distribution", {})
            if not category_distribution:
                # 手动计算
                category_distribution = {}
                for rec in recommendations:
                    cat = rec.category or "通用"
                    category_distribution[cat] = category_distribution.get(cat, 0) + 1

            return {
                "request_id": request_id,
                "session_id": session_id,
                "book_list_id": None,  # 如果需要保存到历史，后续更新
                "requirements": parsed_reqs.model_dump(),  # 转换为字典
                "recommendations": [rec.model_dump() for rec in recommendations],  # 转换为字典列表
                "total_count": len(recommendations),
                "category_distribution": category_distribution,
                "generation_time_ms": generation_time_ms,
                "success": True,
                "message": f"成功生成{len(recommendations)}本书的推荐书单",
                "quality_score": booklist.get("quality_score", 0.8),
                "confidence": booklist.get("confidence", 0.85),
                "agent_metadata": {
                    "iterations": agent_result.get("iterations", 1),
                    "used_memory": agent_result.get("used_memory", False),
                    "cache_hit": agent_result.get("cache_hit", False),
                },
            }
        except Exception as e:
            logger.error(f"转换Agent结果为响应失败: {str(e)}")
            return {
                "request_id": request_id,
                "session_id": session_id,
                "book_list_id": None,
                "requirements": parsed_reqs.model_dump() if parsed_reqs else {},
                "recommendations": [],
                "total_count": 0,
                "category_distribution": {},
                "generation_time_ms": generation_time_ms,
                "success": False,
                "message": f"生成书单失败: {str(e)}",
                "quality_score": 0.0,
                "confidence": 0.0,
                "agent_metadata": {
                    "iterations": 0,
                    "used_memory": False,
                    "cache_hit": False,
                },
            }

    @classmethod
    def _map_cognitive_level(cls, level: Optional[str]) -> str:
        """将认知水平映射为年龄组"""
        if not level:
            return "成人"

        level_map = {
            "儿童": "儿童",
            "小学生": "儿童",
            "中学生": "青少年",
            "高中生": "青少年",
            "大学生": "成人",
            "研究生": "成人",
            "专业人士": "成人",
            "通用": "成人",
        }
        return level_map.get(level, "成人")

    @classmethod
    def enhance_requirements_with_memory(
        cls, parsed_reqs: ParsedRequirements, user_context: Dict[str, Any]
    ) -> ParsedRequirements:
        """
        使用用户记忆增强需求

        Args:
            parsed_reqs: 原始需求
            user_context: 用户上下文（来自记忆系统）

        Returns:
            ParsedRequirements: 增强后的需求
        """
        try:
            preferences = user_context.get("preferences", {})
            if not preferences:
                return parsed_reqs

            # 创建副本
            enhanced = parsed_reqs.copy()

            # 补充缺失的分类
            if not enhanced.categories and preferences.get("preferred_categories"):
                preferred = preferences.get("preferred_categories", [])[:3]  # 取前3个
                if preferred:
                    enhanced.categories = [
                        CategoryRequirement(
                            category=cat,
                            percentage=100 // len(preferred),
                            count=max(1, 20 // len(preferred)),
                        )
                        for cat in preferred
                    ]

            # 添加避免的关键词
            if preferences.get("avoided_categories"):
                avoided = preferences.get("avoided_categories", [])
                if enhanced.constraints is None:
                    enhanced.constraints = []
                enhanced.constraints.extend([f"避免{cat}" for cat in avoided])

            return enhanced
        except Exception as e:
            logger.error(f"增强需求失败: {str(e)}")
            return parsed_reqs

    @staticmethod
    def create_user_input_from_requirements(parsed_reqs: ParsedRequirements) -> str:
        """
        从需求对象重建用户输入（用于Agent）

        Args:
            parsed_reqs: 解析后的需求

        Returns:
            str: 用户输入字符串
        """
        try:
            parts = []

            if parsed_reqs.target_audience:
                parts.append(f"为{parsed_reqs.target_audience}")

            if parsed_reqs.categories:
                cat_desc = ", ".join(
                    [f"{cat.category}{cat.percentage}%" for cat in parsed_reqs.categories]
                )
                parts.append(f"推荐{cat_desc}的书籍")

            if parsed_reqs.keywords:
                parts.append(f"关键词：{', '.join(parsed_reqs.keywords)}")

            if parsed_reqs.exclude_textbooks:
                parts.append("排除教材")

            return "，".join(parts) if parts else "推荐一些书籍"
        except Exception as e:
            logger.error(f"创建用户输入失败: {str(e)}")
            return "推荐一些书籍"

    @staticmethod
    def _calculate_confidence(parsed_reqs: ParsedRequirements) -> float:
        """
        动态计算需求的置信度

        Args:
            parsed_reqs: 解析后的需求

        Returns:
            float: 置信度值（0-1）
        """
        confidence = 0.5  # 基础置信度

        # 根据需求的完整性增加置信度
        if parsed_reqs.target_audience:
            confidence += 0.1
        if parsed_reqs.cognitive_level:
            confidence += 0.1
        if parsed_reqs.categories:
            confidence += 0.2
        if parsed_reqs.keywords:
            confidence += 0.1
        if parsed_reqs.constraints:
            confidence += 0.1

        # 确保置信度在0-1之间
        return min(1.0, max(0.0, confidence))


# 便捷函数
def adapt_requirements(parsed_reqs: ParsedRequirements) -> Dict[str, Any]:
    """便捷函数：转换需求"""
    return BookListAgentAdapter.convert_requirements(parsed_reqs)


def adapt_booklist_result(
    agent_result: Dict[str, Any], parsed_reqs: ParsedRequirements
) -> List[BookRecommendation]:
    """便捷函数：转换结果"""
    return BookListAgentAdapter.convert_booklist_result(agent_result, parsed_reqs)
