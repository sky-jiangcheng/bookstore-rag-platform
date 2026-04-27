"""
图书检索工具集
集成向量检索、数据库查询、库存检查
"""

from typing import Dict, List, Optional

from .registry import tool, tool_registry


def _category_matches(requested: Optional[str], actual: str) -> bool:
    """判断请求分类与书籍分类是否匹配。

    这里做一点轻量同义词兜底，避免在离线/演示模式下因为分类字面值不一致而返回空结果。
    """
    if not requested:
        return True

    req = requested.lower()
    actual_lower = actual.lower()
    if req in actual_lower or actual_lower in req:
        return True

    aliases = {
        "编程": ["python", "java", "算法", "数据结构", "机器学习", "软件", "开发"],
        "程序": ["python", "java", "算法", "数据结构", "机器学习", "软件", "开发"],
        "开发": ["python", "java", "算法", "数据结构", "机器学习", "软件", "开发"],
        "软件": ["python", "java", "算法", "数据结构", "机器学习", "软件", "开发"],
    }
    for alias, mapped_categories in aliases.items():
        if alias in req:
            return any(token in actual_lower for token in mapped_categories)

    return False


# 模拟向量存储（实际项目中使用真实的 Milvus/Weaviate）
class MockVectorStore:
    """模拟向量存储"""

    def __init__(self):
        # 模拟书籍数据
        self.books = [
            {
                "id": 1,
                "title": "Python编程从入门到实践",
                "author": "Eric Matthes",
                "price": 89.0,
                "category": "Python",
                "embedding": [0.1, 0.2, 0.3],
            },
            {
                "id": 2,
                "title": "算法导论",
                "author": "Thomas Cormen",
                "price": 128.0,
                "category": "算法",
                "embedding": [0.2, 0.3, 0.4],
            },
            {
                "id": 3,
                "title": "深度学习",
                "author": "Ian Goodfellow",
                "price": 168.0,
                "category": "机器学习",
                "embedding": [0.3, 0.4, 0.5],
            },
            {
                "id": 4,
                "title": "Java核心技术",
                "author": "Cay Horstmann",
                "price": 149.0,
                "category": "Java",
                "embedding": [0.15, 0.25, 0.35],
            },
            {
                "id": 5,
                "title": "数据结构与算法分析",
                "author": "Mark Allen Weiss",
                "price": 79.0,
                "category": "算法",
                "embedding": [0.25, 0.35, 0.45],
            },
        ]

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """模拟向量搜索"""
        # 简单的关键词匹配模拟
        results = []
        query_lower = query.lower()

        for book in self.books:
            score = 0.0
            if query_lower in book["title"].lower():
                score += 0.8
            if query_lower in book["category"].lower():
                score += 0.6
            if query_lower in book["author"].lower():
                score += 0.4
            if any(token in query_lower for token in ["编程", "程序", "开发", "软件"]):
                if _category_matches("编程", book["category"]):
                    score += 0.3

            if score > 0:
                book_copy = book.copy()
                book_copy["score"] = min(score, 1.0)
                results.append(book_copy)

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


# 全局向量存储实例
vector_store = MockVectorStore()


@tool(name="vector_search", description="基于语义的向量检索")
def vector_search_tool(query: str, top_k: int = 20) -> List[Dict]:
    """
    向量语义检索工具

    Args:
        query: 搜索查询（自然语言描述）
        top_k: 返回结果数量

    Returns:
        List[Dict]: 书籍列表，包含相关度分数
    """
    results = vector_store.search(query, top_k)

    return [
        {
            "book_id": r["id"],
            "title": r["title"],
            "author": r["author"],
            "price": r["price"],
            "category": r["category"],
            "relevance_score": r["score"],
            "source": "vector",
        }
        for r in results
    ]


@tool(name="db_query", description="数据库精确查询")
def db_query_tool(
    category: str = None,
    author: str = None,
    min_price: float = None,
    max_price: float = None,
    limit: int = 50,
) -> List[Dict]:
    """
    数据库精确查询工具

    Args:
        category: 书籍分类
        author: 作者名（支持模糊匹配）
        min_price: 最低价格
        max_price: 最高价格
        limit: 返回数量限制

    Returns:
        List[Dict]: 符合条件的书籍列表
    """
    # 模拟数据库查询
    results = []

    for book in vector_store.books:
        # 分类过滤
        if not _category_matches(category, book["category"]):
            continue

        # 作者过滤
        if author and author.lower() not in book["author"].lower():
            continue

        # 价格过滤
        if min_price is not None and book["price"] < min_price:
            continue
        if max_price is not None and book["price"] > max_price:
            continue

        results.append(
            {
                "book_id": book["id"],
                "title": book["title"],
                "author": book["author"],
                "price": book["price"],
                "category": book["category"],
                "source": "database",
            }
        )

    return results[:limit]


@tool(name="check_inventory", description="检查书籍库存")
def check_inventory_tool(book_ids: List[int]) -> Dict[int, int]:
    """
    库存检查工具

    Args:
        book_ids: 书籍ID列表

    Returns:
        Dict[int, int]: 书籍ID到库存数量的映射
    """
    # 模拟库存数据
    inventory = {
        1: 100,  # Python编程
        2: 50,  # 算法导论
        3: 30,  # 深度学习
        4: 80,  # Java核心技术
        5: 60,  # 数据结构与算法
    }

    result = {}
    for book_id in book_ids:
        result[book_id] = inventory.get(book_id, 0)

    return result


@tool(name="get_popular_books", description="获取热门书籍")
def get_popular_books_tool(category: str = None, limit: int = 10) -> List[Dict]:
    """
    获取热门书籍

    Args:
        category: 分类筛选（可选）
        limit: 返回数量

    Returns:
        List[Dict]: 热门书籍列表
    """
    # 模拟热门书籍（按销量排序）
    popular = [
        {"id": 1, "title": "Python编程从入门到实践", "sales": 1000},
        {"id": 2, "title": "算法导论", "sales": 800},
        {"id": 4, "title": "Java核心技术", "sales": 600},
        {"id": 3, "title": "深度学习", "sales": 500},
        {"id": 5, "title": "数据结构与算法分析", "sales": 400},
    ]

    results = []
    for pop in popular:
        book = next((b for b in vector_store.books if b["id"] == pop["id"]), None)
        if book:
            # 分类过滤
            if not _category_matches(category, book["category"]):
                continue

            results.append(
                {
                    "book_id": book["id"],
                    "title": book["title"],
                    "author": book["author"],
                    "price": book["price"],
                    "category": book["category"],
                    "sales": pop["sales"],
                    "source": "popular",
                }
            )

    return results[:limit]


# 自动注册所有工具
def register_all_tools():
    """注册所有工具到工具注册表"""
    tool_registry.register(
        "vector_search",
        vector_search_tool,
        description="基于语义的向量检索，适合模糊需求",
        parameters={
            "query": {"type": "string", "description": "搜索查询"},
            "top_k": {"type": "integer", "description": "返回数量", "default": 20},
        },
    )

    tool_registry.register(
        "db_query",
        db_query_tool,
        description="数据库精确查询，适合明确条件",
        parameters={
            "category": {"type": "string", "description": "书籍分类", "optional": True},
            "author": {"type": "string", "description": "作者", "optional": True},
            "min_price": {"type": "number", "description": "最低价格", "optional": True},
            "max_price": {"type": "number", "description": "最高价格", "optional": True},
            "limit": {"type": "integer", "description": "返回数量", "default": 50},
        },
    )

    tool_registry.register(
        "check_inventory",
        check_inventory_tool,
        description="检查书籍库存状态",
        parameters={"book_ids": {"type": "array", "description": "书籍ID列表"}},
    )

    tool_registry.register(
        "get_popular_books",
        get_popular_books_tool,
        description="获取热门畅销书籍",
        parameters={
            "category": {"type": "string", "description": "分类筛选", "optional": True},
            "limit": {"type": "integer", "description": "返回数量", "default": 10},
        },
    )

    print(f"✅ 已注册 {len(tool_registry.list_tools())} 个工具:")
    for tool_name in tool_registry.list_tools():
        print(f"   - {tool_name}")


# 初始化时自动注册
register_all_tools()
