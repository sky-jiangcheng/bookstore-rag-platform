"""
多智能体协作系统
实现多智能体并行工作和协作生成书单
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

from .models import BookListResult, RequirementAnalysis
from .recommendation_agent import RecommendationAgent
from .requirement_agent import RequirementAgent
from .retrieval_agent import RetrievalAgent

logger = logging.getLogger(__name__)


class EvaluationAgent:
    """
    评估智能体
    评估书单质量并提供改进建议
    """

    def __init__(self):
        self.quality_threshold = 0.8
        self.diversity_threshold = 0.7

    async def evaluate(
        self, booklist: BookListResult, requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估书单质量

        Args:
            booklist: 生成的书单
            requirement: 原始需求

        Returns:
            Dict: 评估结果
        """
        scores = {}
        issues = []

        if not booklist.books:
            issues.append("书单为空")
            return {
                "overall_score": 0.0,
                "scores": {
                    "requirement_match": 0.0,
                    "diversity": 0.0,
                    "book_quality": 0.0,
                    "budget": 0.0,
                },
                "issues": issues,
                "suggestions": [
                    {
                        "type": "relevance",
                        "action": "adjust",
                        "target": "retrieval",
                        "description": "需要重新检索候选书籍",
                    }
                ],
                "needs_improvement": True,
                "timestamp": datetime.now().isoformat(),
            }

        # 1. 需求匹配度评估 (30%)
        match_score = self._evaluate_requirement_match(booklist, requirement)
        scores["requirement_match"] = match_score * 0.3
        if match_score < 0.7:
            issues.append(f"需求匹配度较低 ({match_score:.0%})")

        # 2. 分类多样性评估 (25%)
        diversity_score = self._evaluate_diversity(booklist)
        scores["diversity"] = diversity_score * 0.25
        if diversity_score < self.diversity_threshold:
            issues.append(f"分类多样性不足 ({diversity_score:.0%})")

        # 3. 书籍质量评估 (25%)
        quality_score = self._evaluate_book_quality(booklist)
        scores["book_quality"] = quality_score * 0.25
        if quality_score < 0.7:
            issues.append(f"书籍平均质量较低 ({quality_score:.0%})")

        # 4. 预算符合度评估 (20%)
        budget_score = self._evaluate_budget(booklist, requirement)
        scores["budget"] = budget_score * 0.2
        if budget_score < 0.8:
            issues.append(f"预算符合度不足 ({budget_score:.0%})")

        total_score = sum(scores.values())

        # 生成改进建议
        suggestions = self._generate_suggestions(booklist, requirement, issues)

        return {
            "overall_score": round(total_score, 2),
            "scores": scores,
            "issues": issues,
            "suggestions": suggestions,
            "needs_improvement": total_score < self.quality_threshold,
            "timestamp": datetime.now().isoformat(),
        }

    def _evaluate_requirement_match(
        self, booklist: BookListResult, requirement: Dict[str, Any]
    ) -> float:
        """评估需求匹配度"""
        if not booklist.books:
            return 0.0

        # 检查分类匹配
        req_categories = set()
        if requirement.get("categories"):
            req_categories = {c["name"] for c in requirement["categories"]}

        book_categories = {b.category for b in booklist.books}

        if req_categories:
            category_match = len(req_categories & book_categories) / len(req_categories)
        else:
            category_match = 0.5

        # 检查关键词匹配
        keywords = set(requirement.get("keywords", []))
        if keywords:
            keyword_matches = 0
            for book in booklist.books:
                title_words = set(book.title.lower().split())
                if keywords & title_words:
                    keyword_matches += 1
            keyword_match = keyword_matches / len(booklist.books)
        else:
            keyword_match = 0.5

        return category_match * 0.6 + keyword_match * 0.4

    def _evaluate_diversity(self, booklist: BookListResult) -> float:
        """评估分类多样性"""
        if not booklist.books:
            return 0.0

        categories = len(booklist.category_distribution)

        # 理想情况下至少有3个分类
        if categories >= 3:
            return 1.0
        elif categories == 2:
            return 0.7
        elif categories == 1:
            return 0.4
        return 0.0

    def _evaluate_book_quality(self, booklist: BookListResult) -> float:
        """评估书籍质量"""
        if not booklist.books:
            return 0.0

        # 基于相关度评分
        avg_relevance = sum(b.relevance_score for b in booklist.books) / len(
            booklist.books
        )

        # 基于库存可用性
        available_ratio = sum(1 for b in booklist.books if b.stock > 0) / len(
            booklist.books
        )

        return avg_relevance * 0.7 + available_ratio * 0.3

    def _evaluate_budget(
        self, booklist: BookListResult, requirement: Dict[str, Any]
    ) -> float:
        """评估预算符合度"""
        budget = requirement.get("constraints", {}).get("budget")
        if not budget:
            return 1.0

        if booklist.total_price <= budget:
            return 1.0

        # 超预算时按比例扣分
        overspend_ratio = (booklist.total_price - budget) / budget
        return max(0, 1 - overspend_ratio)

    def _generate_suggestions(
        self, booklist: BookListResult, requirement: Dict[str, Any], issues: List[str]
    ) -> List[Dict[str, Any]]:
        """生成改进建议"""
        suggestions = []

        if "分类多样性不足" in str(issues):
            suggestions.append(
                {
                    "type": "diversity",
                    "action": "increase",
                    "target": "categories",
                    "description": "增加更多分类的书籍",
                }
            )

        if "需求匹配度较低" in str(issues):
            suggestions.append(
                {
                    "type": "relevance",
                    "action": "adjust",
                    "target": "retrieval",
                    "description": "调整检索策略以提高相关性",
                }
            )

        if "预算符合度不足" in str(issues):
            suggestions.append(
                {
                    "type": "budget",
                    "action": "optimize",
                    "target": "selection",
                    "description": "选择价格更合适的书籍",
                }
            )

        return suggestions


class MultiAgentOrchestrator:
    """
    多智能体编排器
    协调多个 Agent 并行工作和协作
    """

    def __init__(self):
        self.req_agent = RequirementAgent()
        self.retrieval_agent = RetrievalAgent()
        self.rec_agent = RecommendationAgent()
        self.eval_agent = EvaluationAgent()
        self.max_iterations = 3

    async def collaborative_generate(
        self, user_input: str, stream: bool = True, target_count: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        协作生成书单

        Args:
            user_input: 用户输入
            stream: 是否流式输出

        Yields:
            Dict: 包含步骤信息的字典
        """
        iteration = 0
        current_booklist = None

        # Step 1: 需求分析
        yield {
            "type": "phase_start",
            "phase": "requirement_analysis",
            "content": "正在分析您的需求...",
        }

        requirement = await self.req_agent.analyze(user_input)

        if requirement.needs_clarification:
            yield {
                "type": "clarification_needed",
                "questions": requirement.clarification_questions,
            }
            return

        yield {
            "type": "phase_complete",
            "phase": "requirement_analysis",
            "data": requirement.to_dict(),
        }

        # 迭代优化循环
        while iteration < self.max_iterations:
            iteration += 1

            yield {
                "type": "iteration_start",
                "iteration": iteration,
                "content": f"第 {iteration} 轮书单生成...",
            }

            # Step 2: 并行检索（多路召回）
            yield {
                "type": "phase_start",
                "phase": "retrieval",
                "content": "正在从多个渠道检索书籍...",
            }

            retrieval_tasks = [
                self._semantic_retrieval(requirement),
                self._exact_retrieval(requirement),
                self._popular_retrieval(requirement),
            ]

            results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)

            # 融合结果
            fused_candidates = self._fusion_rerank(results)

            yield {
                "type": "phase_complete",
                "phase": "retrieval",
                "data": {
                    "candidate_count": len(fused_candidates),
                    "sources": ["semantic", "exact", "popular"],
                },
            }

            # Step 3: 生成书单
            yield {"type": "phase_start", "phase": "generation", "content": "正在生成书单..."}

            current_booklist = self.rec_agent.generate_booklist(
                requirement=requirement.__dict__,
                candidates=fused_candidates,
                target_count=target_count,
            )

            yield {
                "type": "phase_complete",
                "phase": "generation",
                "data": {
                    "book_count": len(current_booklist.books),
                    "total_price": current_booklist.total_price,
                    "quality_score": current_booklist.quality_score,
                },
            }

            # Step 4: 质量评估
            yield {
                "type": "phase_start",
                "phase": "evaluation",
                "content": "正在评估书单质量...",
            }

            evaluation = await self.eval_agent.evaluate(
                current_booklist, requirement.__dict__
            )

            yield {
                "type": "phase_complete",
                "phase": "evaluation",
                "data": {
                    "overall_score": evaluation["overall_score"],
                    "issues": evaluation["issues"],
                    "needs_improvement": evaluation["needs_improvement"],
                },
            }

            # 如果质量达标，退出循环
            if not evaluation["needs_improvement"]:
                yield {
                    "type": "optimization_complete",
                    "content": "书单质量达标！",
                    "iterations": iteration,
                }
                break

            # 如果需要改进且不是最后一次迭代
            if iteration < self.max_iterations:
                yield {
                    "type": "optimization_needed",
                    "content": f"书单需要优化，正在进行第 {iteration + 1} 轮...",
                    "suggestions": evaluation["suggestions"],
                }

                # 根据建议调整参数（这里简化处理）
                # 实际应用中可以实现更复杂的参数调整逻辑
            else:
                yield {
                    "type": "max_iterations_reached",
                    "content": f"已达到最大迭代次数 ({self.max_iterations})，返回当前最佳结果",
                }

        # 最终结果
        yield {
            "type": "complete",
            "content": "书单生成完成！",
            "booklist": {
                "books": [
                    {
                        "book_id": b.book_id,
                        "title": b.title,
                        "author": b.author,
                        "publisher": b.publisher,
                        "price": b.price,
                        "stock": b.stock,
                        "category": b.category,
                        "relevance_score": b.relevance_score,
                    }
                    for b in current_booklist.books
                ],
                "total_price": current_booklist.total_price,
                "quality_score": current_booklist.quality_score,
                "confidence": current_booklist.confidence,
                "category_distribution": current_booklist.category_distribution,
            },
            "requirement": requirement.__dict__,
            "iterations": iteration,
            "timestamp": datetime.now().isoformat(),
        }

    async def _semantic_retrieval(self, requirement: RequirementAnalysis) -> List[Any]:
        """语义检索"""
        try:
            return await self.retrieval_agent.retrieve(
                requirement.__dict__,
                strategy=self.retrieval_agent.strategies[0],  # semantic
            )
        except Exception as e:
            logger.error(f"Semantic retrieval failed: {e}")
            return []

    async def _exact_retrieval(self, requirement: RequirementAnalysis) -> List[Any]:
        """精确检索"""
        try:
            return await self.retrieval_agent.retrieve(
                requirement.__dict__,
                strategy=self.retrieval_agent.strategies[1],  # exact
            )
        except Exception as e:
            logger.error(f"Exact retrieval failed: {e}")
            return []

    async def _popular_retrieval(self, requirement: RequirementAnalysis) -> List[Any]:
        """热门推荐检索"""
        try:
            return await self.retrieval_agent.retrieve(
                requirement.__dict__,
                strategy=self.retrieval_agent.strategies[3],  # popular
            )
        except Exception as e:
            logger.error(f"Popular retrieval failed: {e}")
            return []

    def _fusion_rerank(self, results: List[Any]) -> List[Any]:
        """
        融合多路召回结果并重新排序

        使用 Reciprocal Rank Fusion (RRF) 算法
        """
        k = 60  # RRF 常数
        scores = {}

        for source_idx, candidates in enumerate(results):
            if isinstance(candidates, Exception):
                continue

            for rank, candidate in enumerate(candidates):
                if isinstance(candidate, Exception):
                    continue

                book_id = (
                    candidate.book_id
                    if hasattr(candidate, "book_id")
                    else candidate["book_id"]
                )

                if book_id not in scores:
                    scores[book_id] = {"candidate": candidate, "rrf_score": 0}

                # RRF 公式: 1 / (k + rank)
                scores[book_id]["rrf_score"] += 1 / (k + rank + 1)

        # 按 RRF 分数排序
        sorted_results = sorted(
            scores.values(), key=lambda x: x["rrf_score"], reverse=True
        )

        return [item["candidate"] for item in sorted_results]


# 便捷函数
async def collaborative_generate(
    user_input: str, stream: bool = True
) -> AsyncIterator[Dict[str, Any]]:
    """
    便捷的多智能体协作生成函数
    """
    orchestrator = MultiAgentOrchestrator()
    async for msg in orchestrator.collaborative_generate(user_input, stream):
        yield msg
