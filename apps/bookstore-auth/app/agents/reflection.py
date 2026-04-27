"""
自我反思系统
实现智能体自我反思和改进
"""

import logging
from typing import Any, Dict, List, Optional

from .models import BookListResult, ReflectionResult

logger = logging.getLogger(__name__)


class SelfReflection:
    """
    智能体自我反思系统
    评估书单质量，识别问题，生成改进计划
    """

    def __init__(self):
        self.quality_threshold = 0.75
        self.min_categories = 2
        self.max_single_category_ratio = 0.7

    async def reflect(
        self,
        booklist: BookListResult,
        requirement: Dict[str, Any],
        user_feedback: Optional[str] = None,
    ) -> ReflectionResult:
        """
        对书单进行反思

        Args:
            booklist: 生成的书单
            requirement: 原始需求
            user_feedback: 用户反馈（可选）

        Returns:
            ReflectionResult: 反思结果
        """
        issues = []
        quality_breakdown = {}

        # 1. 分类结构分析
        category_score, category_issues = self._analyze_categories(
            booklist, requirement
        )
        quality_breakdown["category_structure"] = category_score
        issues.extend(category_issues)

        # 2. 需求匹配度分析
        match_score, match_issues = self._analyze_requirement_match(
            booklist, requirement
        )
        quality_breakdown["requirement_match"] = match_score
        issues.extend(match_issues)

        # 3. 书籍质量分析
        quality_score, quality_issues = self._analyze_book_quality(booklist)
        quality_breakdown["book_quality"] = quality_score
        issues.extend(quality_issues)

        # 4. 预算分析
        budget_score, budget_issues = self._analyze_budget(booklist, requirement)
        quality_breakdown["budget_fit"] = budget_score
        issues.extend(budget_issues)

        # 5. 用户反馈分析（如果有）
        if user_feedback:
            feedback_score, feedback_issues = self._analyze_user_feedback(
                booklist, user_feedback
            )
            quality_breakdown["user_feedback"] = feedback_score
            issues.extend(feedback_issues)

        # 计算总体质量分
        overall_score = sum(quality_breakdown.values()) / len(quality_breakdown)

        # 生成改进计划
        improvement_plan = self._generate_improvement_plan(
            booklist, requirement, issues, quality_breakdown
        )

        # 生成反思总结
        reflection_summary = self._generate_reflection_summary(
            overall_score, issues, improvement_plan
        )

        return ReflectionResult(
            needs_improvement=overall_score < self.quality_threshold,
            issues=issues,
            improvement_plan=improvement_plan,
            reflection_summary=reflection_summary,
            quality_breakdown=quality_breakdown,
        )

    def _analyze_categories(
        self, booklist: BookListResult, requirement: Dict[str, Any]
    ) -> tuple:
        """
        分析分类结构

        Returns:
            tuple: (分数, 问题列表)
        """
        issues = []
        score = 1.0

        if not booklist.books:
            return 0.0, ["书单为空"]

        # 检查分类数量
        category_count = len(booklist.category_distribution)
        if category_count < self.min_categories:
            issues.append(f"分类数量过少（{category_count}个，建议至少{self.min_categories}个）")
            score -= 0.3

        # 检查分类分布是否均衡
        if booklist.category_distribution:
            max_count = max(booklist.category_distribution.values())
            total = sum(booklist.category_distribution.values())
            max_ratio = max_count / total

            if max_ratio > self.max_single_category_ratio:
                dominant_category = max(
                    booklist.category_distribution.items(), key=lambda x: x[1]
                )[0]
                issues.append(f"分类分布不均衡，{dominant_category}占比过高({max_ratio:.0%})")
                score -= 0.2

        # 检查是否缺少期望的分类
        expected_categories = set()
        if requirement.get("categories"):
            expected_categories = {c["name"] for c in requirement["categories"]}

        actual_categories = set(booklist.category_distribution.keys())
        missing = expected_categories - actual_categories

        if missing:
            issues.append(f"缺少期望的分类：{', '.join(missing)}")
            score -= 0.2 * len(missing)

        return max(0, score), issues

    def _analyze_requirement_match(
        self, booklist: BookListResult, requirement: Dict[str, Any]
    ) -> tuple:
        """
        分析需求匹配度

        Returns:
            tuple: (分数, 问题列表)
        """
        issues = []
        score = 1.0

        if not booklist.books:
            return 0.0, ["书单为空"]

        # 检查关键词匹配
        keywords = set(requirement.get("keywords", []))
        if keywords:
            matched_keywords = set()
            for book in booklist.books:
                title_lower = book.title.lower()
                for keyword in keywords:
                    if keyword.lower() in title_lower:
                        matched_keywords.add(keyword)

            match_ratio = len(matched_keywords) / len(keywords)
            if match_ratio < 0.5:
                issues.append(f"关键词匹配度低（{match_ratio:.0%}）")
                score -= 0.3

        # 检查目标受众匹配
        target_audience = requirement.get("target_audience", {})
        if target_audience and target_audience.get("reading_level"):
            # 这里可以基于书籍元数据检查难度级别
            # 简化处理，假设相关度能反映匹配程度
            avg_relevance = sum(b.relevance_score for b in booklist.books) / len(
                booklist.books
            )
            if avg_relevance < 0.6:
                issues.append(f"书籍与目标受众匹配度较低（相关度{avg_relevance:.0%}）")
                score -= 0.2

        return max(0, score), issues

    def _analyze_book_quality(self, booklist: BookListResult) -> tuple:
        """
        分析书籍质量

        Returns:
            tuple: (分数, 问题列表)
        """
        issues = []
        score = 1.0

        if not booklist.books:
            return 0.0, ["书单为空"]

        # 检查平均相关度
        avg_relevance = sum(b.relevance_score for b in booklist.books) / len(
            booklist.books
        )
        if avg_relevance < 0.7:
            issues.append(f"书籍平均相关度较低（{avg_relevance:.0%}）")
            score -= 0.3

        # 检查库存可用性
        available_count = sum(1 for b in booklist.books if b.stock > 0)
        available_ratio = available_count / len(booklist.books)
        if available_ratio < 0.8:
            issues.append(f"库存不足的书籍较多（{available_ratio:.0%}可用）")
            score -= 0.2

        # 检查价格范围
        prices = [b.price for b in booklist.books]
        if prices:
            avg_price = sum(prices) / len(prices)
            price_variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)

            # 如果价格方差过大，说明书籍价格分布不均匀
            if price_variance > (avg_price * 0.5) ** 2:
                issues.append("书籍价格波动较大")
                score -= 0.1

        return max(0, score), issues

    def _analyze_budget(
        self, booklist: BookListResult, requirement: Dict[str, Any]
    ) -> tuple:
        """
        分析预算符合度

        Returns:
            tuple: (分数, 问题列表)
        """
        issues = []
        score = 1.0

        budget = requirement.get("constraints", {}).get("budget")
        if not budget:
            return 1.0, []  # 无预算限制，满分

        if booklist.total_price > budget:
            overspend = booklist.total_price - budget
            overspend_ratio = overspend / budget
            issues.append(f"超出预算¥{overspend:.2f}（超支{overspend_ratio:.0%}）")
            score -= min(0.5, overspend_ratio)

        # 检查预算利用率
        utilization = booklist.total_price / budget
        if utilization < 0.5:
            issues.append(f"预算利用率过低（{utilization:.0%}）")
            score -= 0.1

        return max(0, score), issues

    def _analyze_user_feedback(
        self, booklist: BookListResult, user_feedback: str
    ) -> tuple:
        """
        分析用户反馈

        Returns:
            tuple: (分数, 问题列表)
        """
        issues = []
        score = 1.0

        # 简单的情感分析
        negative_keywords = ["不好", "不满意", "不喜欢", "太多", "太少", "太贵", "不对"]
        positive_keywords = ["好", "满意", "喜欢", "不错", "很好", "合适"]

        feedback_lower = user_feedback.lower()

        negative_count = sum(1 for kw in negative_keywords if kw in feedback_lower)
        positive_count = sum(1 for kw in positive_keywords if kw in feedback_lower)

        if negative_count > 0:
            issues.append("用户反馈包含负面评价")
            score -= 0.3 * negative_count

        if positive_count == 0 and negative_count == 0:
            # 中性反馈
            score -= 0.1

        # 提取具体反馈
        if "太多" in feedback_lower:
            issues.append("用户认为书籍数量过多")
        if "太少" in feedback_lower:
            issues.append("用户认为书籍数量过少")
        if "太贵" in feedback_lower:
            issues.append("用户认为价格过高")

        return max(0, score), issues

    def _generate_improvement_plan(
        self,
        booklist: BookListResult,
        requirement: Dict[str, Any],
        issues: List[str],
        quality_breakdown: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        生成改进计划

        Returns:
            Dict: 包含改进策略的字典
        """
        plan = {
            "priority": "medium",
            "actions": [],
            "params_adjustment": {},
            "estimated_improvement": 0.0,
        }

        if not issues:
            plan["priority"] = "none"
            plan["actions"].append("无需改进")
            return plan

        # 根据问题严重程度确定优先级
        critical_count = sum(
            1 for issue in issues if "书单为空" in issue or "分类数量过少" in issue
        )
        if critical_count > 0:
            plan["priority"] = "high"
        elif len(issues) >= 3:
            plan["priority"] = "high"
        elif len(issues) >= 2:
            plan["priority"] = "medium"
        else:
            plan["priority"] = "low"

        # 生成具体改进措施
        actions = []

        if any("分类" in issue for issue in issues):
            actions.append(
                {
                    "target": "diversity",
                    "action": "increase_category_variety",
                    "description": "增加更多分类的书籍",
                    "params": {"min_categories": self.min_categories + 1},
                }
            )

        if any("关键词" in issue or "匹配" in issue for issue in issues):
            actions.append(
                {
                    "target": "relevance",
                    "action": "adjust_retrieval_strategy",
                    "description": "调整检索策略以提高相关性",
                    "params": {"use_semantic": True, "use_exact": True},
                }
            )

        if any("预算" in issue or "价格" in issue for issue in issues):
            actions.append(
                {
                    "target": "budget",
                    "action": "optimize_price_range",
                    "description": "优化价格范围选择",
                    "params": {"strict_budget": True},
                }
            )

        if any("相关度" in issue for issue in issues):
            actions.append(
                {
                    "target": "quality",
                    "action": "increase_relevance_threshold",
                    "description": "提高相关度阈值",
                    "params": {"min_relevance": 0.8},
                }
            )

        if any("库存" in issue for issue in issues):
            actions.append(
                {
                    "target": "availability",
                    "action": "prioritize_in_stock",
                    "description": "优先选择库存充足的书籍",
                    "params": {"min_stock": 10},
                }
            )

        plan["actions"] = actions

        # 估算改进幅度
        current_score = sum(quality_breakdown.values()) / len(quality_breakdown)
        estimated_improvement = min(0.2, (self.quality_threshold - current_score) * 0.8)
        plan["estimated_improvement"] = round(estimated_improvement, 2)

        return plan

    def _generate_reflection_summary(
        self, overall_score: float, issues: List[str], improvement_plan: Dict[str, Any]
    ) -> str:
        """
        生成反思总结

        Returns:
            str: 反思总结文本
        """
        summary_parts = []

        # 质量评估
        if overall_score >= 0.8:
            summary_parts.append(f"书单质量优秀（{overall_score:.0%}）")
        elif overall_score >= 0.6:
            summary_parts.append(f"书单质量良好（{overall_score:.0%}），但有改进空间")
        else:
            summary_parts.append(f"书单质量需要改进（{overall_score:.0%}）")

        # 问题概述
        if issues:
            summary_parts.append(f"发现{len(issues)}个问题：")
            for i, issue in enumerate(issues[:3], 1):  # 只列出前3个问题
                summary_parts.append(f"  {i}. {issue}")
            if len(issues) > 3:
                summary_parts.append(f"  ... 等共{len(issues)}个问题")
        else:
            summary_parts.append("未发现明显问题")

        # 改进计划
        if improvement_plan.get("actions"):
            action_count = len(improvement_plan["actions"])
            summary_parts.append(f"建议执行{action_count}项改进措施")

        return "\n".join(summary_parts)

    async def iterative_improve(
        self,
        booklist: BookListResult,
        requirement: Dict[str, Any],
        max_iterations: int = 2,
    ) -> Dict[str, Any]:
        """
        迭代改进书单

        Args:
            booklist: 初始书单
            requirement: 需求
            max_iterations: 最大迭代次数

        Returns:
            Dict: 包含改进历史的结果
        """
        history = []
        current_booklist = booklist

        for iteration in range(max_iterations):
            # 进行反思
            reflection = await self.reflect(current_booklist, requirement)

            history.append(
                {
                    "iteration": iteration + 1,
                    "score": sum(reflection.quality_breakdown.values())
                    / len(reflection.quality_breakdown),
                    "issues": reflection.issues,
                    "needs_improvement": reflection.needs_improvement,
                }
            )

            # 如果不需要改进，停止迭代
            if not reflection.needs_improvement:
                break

            # 这里可以实现基于改进计划的自动优化逻辑
            # 简化处理，实际应用中可以根据 improvement_plan 调整参数重新生成
            logger.info(
                f"Iteration {iteration + 1}: {len(reflection.issues)} issues found"
            )

        return {
            "final_booklist": current_booklist,
            "reflection_history": history,
            "total_iterations": len(history),
            "improvement_made": len(history) > 1,
        }


# 便捷函数
async def reflect_on_booklist(
    booklist: BookListResult,
    requirement: Dict[str, Any],
    user_feedback: Optional[str] = None,
) -> ReflectionResult:
    """
    便捷函数：对书单进行反思
    """
    reflection = SelfReflection()
    return await reflection.reflect(booklist, requirement, user_feedback)
