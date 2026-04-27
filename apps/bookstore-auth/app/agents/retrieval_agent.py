"""
检索智能体
根据需求选择合适的检索策略，执行多路召回
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..agents.models import BookCandidate
from ..tools.registry import tool_registry


@dataclass
class RetrievalStrategy:
    """检索策略"""

    name: str
    description: str
    tools: List[str]
    priority: int


class RetrievalAgent:
    """
    图书检索智能体
    根据需求特征选择最优检索策略
    """

    def __init__(self):
        self.tool_registry = tool_registry
        self.strategies = self._init_strategies()

    def _init_strategies(self) -> List[RetrievalStrategy]:
        """初始化检索策略"""
        return [
            RetrievalStrategy(
                name="semantic",
                description="语义检索 - 适合模糊需求",
                tools=["vector_search"],
                priority=1,
            ),
            RetrievalStrategy(
                name="exact",
                description="精确检索 - 适合明确条件",
                tools=["db_query"],
                priority=2,
            ),
            RetrievalStrategy(
                name="hybrid",
                description="混合检索 - 综合语义和精确",
                tools=["vector_search", "db_query"],
                priority=3,
            ),
            RetrievalStrategy(
                name="popular",
                description="热门推荐 - 适合探索性需求",
                tools=["get_popular_books"],
                priority=4,
            ),
        ]

    def select_strategy(self, requirement: Dict[str, Any]) -> RetrievalStrategy:
        """
        根据需求特征选择检索策略

        Args:
            requirement: 需求分析结果

        Returns:
            RetrievalStrategy: 选择的检索策略
        """
        # 判断需求类型
        has_specific_category = bool(requirement.get("categories"))
        has_keywords = bool(requirement.get("keywords"))
        confidence = requirement.get("confidence", 0.5)

        # 策略选择逻辑
        if confidence > 0.8 and has_specific_category:
            # 高置信度 + 明确分类 → 精确检索
            return next(s for s in self.strategies if s.name == "exact")
        elif confidence > 0.6 and has_keywords:
            # 中等置信度 + 关键词 → 混合检索
            return next(s for s in self.strategies if s.name == "hybrid")
        elif confidence < 0.5:
            # 低置信度 → 热门推荐
            return next(s for s in self.strategies if s.name == "popular")
        else:
            # 默认语义检索
            return next(s for s in self.strategies if s.name == "semantic")

    async def retrieve(
        self, requirement: Dict[str, Any], strategy: Optional[RetrievalStrategy] = None
    ) -> List[BookCandidate]:
        """
        执行检索

        Args:
            requirement: 需求分析结果
            strategy: 指定策略（可选，自动选择）

        Returns:
            List[BookCandidate]: 候选书籍列表
        """
        # 选择策略
        if strategy is None:
            strategy = self.select_strategy(requirement)

        print(f"🎯 选择检索策略: {strategy.name} - {strategy.description}")

        # 并行执行多个工具
        tasks = []
        for tool_name in strategy.tools:
            task = self._execute_tool(tool_name, requirement)
            tasks.append(task)

        # 等待所有工具执行完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        all_books = []
        for result in results:
            if isinstance(result, Exception):
                print(f"⚠️ 工具执行失败: {result}")
                continue
            all_books.extend(result)

        # 去重（基于 book_id）
        seen_ids = set()
        unique_books = []
        for book in all_books:
            if book["book_id"] not in seen_ids:
                seen_ids.add(book["book_id"])
                unique_books.append(book)

        # 检查库存并过滤
        book_ids = [b["book_id"] for b in unique_books]
        inventory = await self.tool_registry.execute(
            "check_inventory", {"book_ids": book_ids}
        )

        available_books = []
        for book in unique_books:
            stock = inventory.get(book["book_id"], 0)
            if stock > 0:
                book["stock"] = stock
                available_books.append(book)

        # 转换为 BookCandidate 对象
        candidates = [self._to_candidate(book) for book in available_books]

        # 按相关度排序
        candidates.sort(key=lambda x: x.relevance_score, reverse=True)

        print(f"✅ 检索完成: 找到 {len(candidates)} 本可用书籍")
        return candidates

    async def _execute_tool(
        self, tool_name: str, requirement: Dict[str, Any]
    ) -> List[Dict]:
        """执行单个工具"""
        try:
            if tool_name == "vector_search":
                # 构建查询
                query = self._build_vector_query(requirement)
                params = {"query": query, "top_k": 20}

            elif tool_name == "db_query":
                # 构建数据库查询参数
                params = self._build_db_params(requirement)

            elif tool_name == "get_popular_books":
                # 获取热门书籍
                category = (
                    requirement.get("categories", [{}])[0].get("name")
                    if requirement.get("categories")
                    else None
                )
                params = {"category": category, "limit": 10}

            else:
                return []

            # 执行工具
            result = await self.tool_registry.execute(tool_name, params)
            return result if isinstance(result, list) else []

        except Exception as e:
            print(f"⚠️ 工具 {tool_name} 执行失败: {e}")
            return []

    def _build_vector_query(self, requirement: Dict[str, Any]) -> str:
        """构建向量检索查询"""
        parts = []

        # 添加关键词
        if requirement.get("keywords"):
            parts.extend(requirement["keywords"])

        # 添加分类
        if requirement.get("categories"):
            for cat in requirement["categories"]:
                parts.append(cat.get("name", ""))

        # 添加受众信息
        if requirement.get("target_audience"):
            audience = requirement["target_audience"]
            if audience.get("occupation"):
                parts.append(audience["occupation"])

        return " ".join(parts) if parts else "编程书籍"

    def _build_db_params(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """构建数据库查询参数"""
        params = {}

        # 分类
        if requirement.get("categories"):
            params["category"] = requirement["categories"][0].get("name")

        # 价格范围
        if requirement.get("constraints"):
            budget = requirement["constraints"].get("budget")
            if budget:
                params["max_price"] = float(budget)

        params["limit"] = 50
        return params

    def _to_candidate(self, book: Dict[str, Any]) -> BookCandidate:
        """转换为 BookCandidate"""
        return BookCandidate(
            book_id=book["book_id"],
            title=book["title"],
            author=book.get("author", "未知作者"),
            publisher=book.get("publisher", "未知出版社"),
            price=book.get("price", 0.0),
            stock=book.get("stock", 0),
            category=book.get("category", "未分类"),
            relevance_score=book.get("relevance_score", 0.5),
            source=book.get("source", "unknown"),
        )

    async def retrieve_parallel(
        self, requirement: Dict[str, Any]
    ) -> List[BookCandidate]:
        """
        并行多路召回检索
        同时使用多种策略，然后融合结果
        """
        print("🚀 启动并行多路召回...")

        # 定义多个检索任务
        tasks = [
            self.retrieve(requirement, self.strategies[0]),  # 语义检索
            self.retrieve(requirement, self.strategies[1]),  # 精确检索
            self.retrieve(requirement, self.strategies[3]),  # 热门推荐
        ]

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 融合结果
        all_candidates = []
        seen_ids = set()

        for result in results:
            if isinstance(result, Exception):
                continue
            for candidate in result:
                if candidate.book_id not in seen_ids:
                    seen_ids.add(candidate.book_id)
                    all_candidates.append(candidate)

        # 按相关度重新排序
        all_candidates.sort(key=lambda x: x.relevance_score, reverse=True)

        print(f"✅ 多路召回完成: 共 {len(all_candidates)} 本唯一书籍")
        return all_candidates


# 便捷函数
async def retrieve_books(requirement: Dict[str, Any]) -> List[BookCandidate]:
    """
    便捷的检索函数

    Args:
        requirement: 需求分析结果

    Returns:
        List[BookCandidate]: 候选书籍列表
    """
    agent = RetrievalAgent()
    return await agent.retrieve(requirement)


# 测试代码
if __name__ == "__main__":

    async def test():
        # 测试需求
        requirement = {
            "target_audience": {
                "occupation": "程序员",
                "age_group": "成人",
                "reading_level": "进阶",
            },
            "categories": [
                {"name": "Python", "percentage": 50},
                {"name": "算法", "percentage": 50},
            ],
            "keywords": ["Python", "数据结构"],
            "constraints": {"budget": 500, "exclude_textbooks": False, "other": []},
            "confidence": 0.85,
            "needs_clarification": False,
            "clarification_questions": [],
        }

        agent = RetrievalAgent()

        # 测试单策略检索
        print("\n=== 测试单策略检索 ===")
        candidates = await agent.retrieve(requirement)
        for c in candidates[:3]:
            print(f"  📚 {c.title} (相关度: {c.relevance_score:.2f}, 库存: {c.stock})")

        # 测试多路召回
        print("\n=== 测试多路召回 ===")
        candidates = await agent.retrieve_parallel(requirement)
        for c in candidates[:5]:
            print(f"  📚 {c.title} ({c.category}, ¥{c.price}, 库存: {c.stock})")

    # 运行测试
    asyncio.run(test())
