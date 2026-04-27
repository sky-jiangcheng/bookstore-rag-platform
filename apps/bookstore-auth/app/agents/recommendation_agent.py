"""
推荐智能体
根据需求和候选书籍生成最终书单
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from ..agents.models import BookCandidate, BookListResult


@dataclass
class CategoryPlan:
    """分类规划"""

    name: str
    count: int
    percentage: float


class RecommendationAgent:
    """
    书单推荐智能体
    根据需求分析和候选书籍，生成最优书单
    """

    def __init__(self):
        self.min_books = 5
        self.max_books = 20
        self.default_count = 10

    def generate_booklist(
        self,
        requirement: Dict[str, Any],
        candidates: List[BookCandidate],
        target_count: int = None,
    ) -> BookListResult:
        """
        生成书单

        Args:
            requirement: 需求分析结果
            candidates: 候选书籍列表
            target_count: 目标书籍数量（可选）

        Returns:
            BookListResult: 生成的书单
        """
        if not candidates:
            return BookListResult(
                books=[],
                reasoning_chain=[{"step": "error", "message": "没有候选书籍"}],
                quality_score=0.0,
                total_price=0.0,
                confidence=0.0,
                category_distribution={},
            )

        desired_count = target_count or self.default_count

        # 1. 规划分类占比
        plan = self._plan_categories(requirement, len(candidates), desired_count)
        reasoning_chain = [{"step": "planning", "plan": plan}]

        # 2. 按分类选书
        selected = self._select_books_by_plan(candidates, plan, desired_count)
        reasoning_chain.append({"step": "selection", "selected_count": len(selected)})

        # 3. 质量评估
        evaluation_requirement = dict(requirement)
        evaluation_requirement["target_count"] = desired_count
        quality = self._evaluate_quality(selected, evaluation_requirement)
        reasoning_chain.append({"step": "evaluation", "quality": quality})

        # 4. 如果质量不达标，尝试优化
        if quality["score"] < 0.7 and len(candidates) > len(selected):
            selected = self._optimize_selection(
                selected,
                candidates,
                evaluation_requirement,
                target_count=desired_count,
            )
            if len(selected) > desired_count:
                selected = selected[:desired_count]
            quality = self._evaluate_quality(selected, evaluation_requirement)
            reasoning_chain.append({"step": "optimization", "quality": quality})

        # 5. 计算统计信息
        total_price = sum(b.price for b in selected)
        category_dist = self._calculate_distribution(selected)

        return BookListResult(
            books=selected,
            reasoning_chain=reasoning_chain,
            quality_score=quality["score"],
            total_price=total_price,
            confidence=quality["confidence"],
            category_distribution=category_dist,
        )

    def _plan_categories(
        self,
        requirement: Dict[str, Any],
        available_count: int,
        desired_count: int = None,
    ) -> List[CategoryPlan]:
        """
        规划分类占比

        Args:
            requirement: 需求分析
            available_count: 可用书籍数量

        Returns:
            List[CategoryPlan]: 分类规划列表
        """
        desired_count = desired_count or self.default_count
        categories = requirement.get("categories", [])

        if not categories:
            # 默认均分
            return [
                CategoryPlan(
                    name="综合",
                    count=min(desired_count, available_count),
                    percentage=100.0,
                )
            ]

        plans = []
        total_percentage = sum(c.get("percentage", 0) for c in categories)

        # 根据需求中的分类比例分配
        for i, cat in enumerate(categories):
            percentage = cat.get("percentage", 100 / len(categories))
            # 标准化百分比
            normalized_pct = (
                (percentage / total_percentage) * 100
                if total_percentage > 0
                else percentage
            )

            # 计算数量
            if i == len(categories) - 1:
                # 最后一个分类占剩余全部
                count = desired_count - sum(p.count for p in plans)
            else:
                count = max(1, int(desired_count * normalized_pct / 100))

            plans.append(
                CategoryPlan(
                    name=cat.get("name", "未分类"),
                    count=min(count, available_count),
                    percentage=normalized_pct,
                )
            )

        return plans

    def _select_books_by_plan(
        self,
        candidates: List[BookCandidate],
        plan: List[CategoryPlan],
        target_count: int = None,
    ) -> List[BookCandidate]:
        """
        按规划选择书籍

        Args:
            candidates: 候选书籍
            plan: 分类规划
            target_count: 目标数量

        Returns:
            List[BookCandidate]: 选中的书籍
        """
        selected = []
        used_ids = set()

        # 按分类选择
        for cat_plan in plan:
            # 筛选该分类的候选书籍
            cat_candidates = [
                c
                for c in candidates
                if c.category == cat_plan.name and c.book_id not in used_ids
            ]

            # 按相关度排序
            cat_candidates.sort(key=lambda x: x.relevance_score, reverse=True)

            # 选择前 N 本
            for book in cat_candidates[: cat_plan.count]:
                selected.append(book)
                used_ids.add(book.book_id)

        # 如果不够，补充高相关度书籍
        if len(selected) < self.min_books:
            remaining = [c for c in candidates if c.book_id not in used_ids]
            remaining.sort(key=lambda x: x.relevance_score, reverse=True)

            needed = min(self.min_books - len(selected), len(remaining))
            selected.extend(remaining[:needed])

        # 限制最大数量
        if target_count and len(selected) > target_count:
            selected = selected[:target_count]

        return selected

    def _evaluate_quality(
        self, books: List[BookCandidate], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估书单质量

        Args:
            books: 书单
            requirement: 需求

        Returns:
            Dict: 质量评估结果
        """
        if not books:
            return {"score": 0.0, "confidence": 0.0, "issues": ["书单为空"]}

        scores = {}

        # 1. 数量合理性 (20%)
        expected_count = max(
            requirement.get("target_count", self.default_count),
            1,
        )
        count_score = min(len(books) / expected_count, 1.0)
        scores["count"] = count_score * 0.2

        # 2. 分类多样性 (30%)
        categories = set(b.category for b in books)
        diversity_score = min(len(categories) / 3, 1.0)  # 至少3个分类得满分
        scores["diversity"] = diversity_score * 0.3

        # 3. 平均相关度 (30%)
        avg_relevance = sum(b.relevance_score for b in books) / len(books)
        scores["relevance"] = avg_relevance * 0.3

        # 4. 预算符合度 (20%)
        budget = requirement.get("constraints", {}).get("budget")
        if budget:
            total_price = sum(b.price for b in books)
            if total_price <= budget:
                budget_score = 1.0
            else:
                budget_score = max(0, 1 - (total_price - budget) / budget)
        else:
            budget_score = 1.0
        scores["budget"] = budget_score * 0.2

        total_score = sum(scores.values())

        # 计算置信度
        confidence = min(avg_relevance * 1.2, 1.0)

        return {
            "score": round(total_score, 2),
            "confidence": round(confidence, 2),
            "breakdown": scores,
        }

    def _optimize_selection(
        self,
        current: List[BookCandidate],
        candidates: List[BookCandidate],
        requirement: Dict[str, Any],
        target_count: int = None,
    ) -> List[BookCandidate]:
        """
        优化书单选择

        Args:
            current: 当前书单
            candidates: 所有候选
            requirement: 需求

        Returns:
            List[BookCandidate]: 优化后的书单
        """
        # 简单策略：尝试添加更多高相关度书籍
        used_ids = {b.book_id for b in current}
        remaining = [c for c in candidates if c.book_id not in used_ids]
        remaining.sort(key=lambda x: x.relevance_score, reverse=True)

        # 尝试添加书籍，直到质量提升或达到上限
        optimized = list(current)
        max_target = target_count or self.max_books
        for book in remaining:
            if len(optimized) >= min(self.max_books, max_target):
                break
            optimized.append(book)

            quality = self._evaluate_quality(optimized, requirement)
            if quality["score"] >= 0.7:
                break

        return optimized

    def _calculate_distribution(self, books: List[BookCandidate]) -> Dict[str, int]:
        """
        计算分类分布

        Args:
            books: 书单

        Returns:
            Dict[str, int]: 分类到数量的映射
        """
        distribution = {}
        for book in books:
            distribution[book.category] = distribution.get(book.category, 0) + 1
        return distribution

    def explain_recommendation(
        self, booklist: BookListResult, requirement: Dict[str, Any]
    ) -> str:
        """
        生成推荐理由说明

        Args:
            booklist: 书单结果
            requirement: 需求

        Returns:
            str: 推荐理由文本
        """
        lines = []

        # 总体说明
        lines.append(f"为您推荐了 {len(booklist.books)} 本书籍，总价格 ¥{booklist.total_price:.2f}")

        # 分类分布
        if booklist.category_distribution:
            lines.append("\n分类分布：")
            for cat, count in booklist.category_distribution.items():
                lines.append(f"  - {cat}: {count} 本")

        # 推荐理由
        lines.append("\n推荐理由：")
        for book in booklist.books[:3]:  # 只展示前3本的详细理由
            lines.append(f"  📖 {book.title}")
            lines.append(f"     相关度: {book.relevance_score:.0%}, 价格: ¥{book.price}")

        # 质量评分
        lines.append(f"\n书单质量评分: {booklist.quality_score:.0%}")

        return "\n".join(lines)


# 便捷函数
def generate_booklist(
    requirement: Dict[str, Any],
    candidates: List[BookCandidate],
    target_count: int = None,
) -> BookListResult:
    """
    便捷的书单生成函数

    Args:
        requirement: 需求分析结果
        candidates: 候选书籍
        target_count: 目标数量

    Returns:
        BookListResult: 生成的书单
    """
    agent = RecommendationAgent()
    return agent.generate_booklist(requirement, candidates, target_count)


# 测试代码
if __name__ == "__main__":
    # 创建模拟候选书籍
    candidates = [
        BookCandidate(
            1,
            "Python编程从入门到实践",
            "Eric Matthes",
            "人民邮电出版社",
            89.0,
            100,
            "Python",
            0.95,
            "vector",
        ),
        BookCandidate(
            2, "算法导论", "Thomas Cormen", "机械工业出版社", 128.0, 50, "算法", 0.88, "database"
        ),
        BookCandidate(
            3, "深度学习", "Ian Goodfellow", "人民邮电出版社", 168.0, 30, "机器学习", 0.82, "vector"
        ),
        BookCandidate(
            4,
            "Java核心技术",
            "Cay Horstmann",
            "机械工业出版社",
            149.0,
            80,
            "Java",
            0.75,
            "popular",
        ),
        BookCandidate(
            5,
            "数据结构与算法分析",
            "Mark Allen Weiss",
            "机械工业出版社",
            79.0,
            60,
            "算法",
            0.90,
            "database",
        ),
    ]

    # 模拟需求
    requirement = {
        "target_audience": {
            "occupation": "程序员",
            "age_group": "成人",
            "reading_level": "进阶",
        },
        "categories": [
            {"name": "Python", "percentage": 60},
            {"name": "算法", "percentage": 40},
        ],
        "keywords": ["Python", "数据结构"],
        "constraints": {"budget": 500, "exclude_textbooks": False, "other": []},
        "confidence": 0.85,
        "needs_clarification": False,
        "clarification_questions": [],
    }

    # 生成书单
    agent = RecommendationAgent()
    result = agent.generate_booklist(requirement, candidates)

    print("=" * 60)
    print("📚 生成的书单")
    print("=" * 60)
    print(f"\n共 {len(result.books)} 本书")
    print(f"总价格: ¥{result.total_price:.2f}")
    print(f"质量评分: {result.quality_score:.0%}")
    print(f"置信度: {result.confidence:.0%}")

    print("\n📖 书籍列表:")
    for i, book in enumerate(result.books, 1):
        print(f"{i}. {book.title} ({book.category}) - ¥{book.price}")

    print("\n📊 分类分布:")
    for cat, count in result.category_distribution.items():
        print(f"  {cat}: {count} 本")

    print("\n📝 推荐理由:")
    print(agent.explain_recommendation(result, requirement))
