"""
图书检索工具集
集成向量检索、数据库查询、库存检查
"""

import os
from typing import Dict, List, Optional

import httpx

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


# ============================================================
# Agentic RAG 向量检索客户端
# 调用 bookstore-agentic-rag 服务的真实向量搜索接口
# ============================================================

class AgenticRAGClient:
    """
    连接 bookstore-agentic-rag 的向量搜索服务。

    通过 HTTP 调用 agentic-rag 的 /api/rag/search 接口，
    获取基于语义的向量检索结果。
    """

    def __init__(self):
        rag_url = os.environ.get("AGENTIC_RAG_URL")
        if not rag_url:
            raise RuntimeError(
                "环境变量 AGENTIC_RAG_URL 未设置，请指定 agentic-rag 服务的地址"
            )
        self.base_url = rag_url.rstrip("/")
        self.timeout = float(os.environ.get("AGENTIC_RAG_TIMEOUT", "5"))

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        调用 agentic-rag 的向量搜索服务。

        Args:
            query: 搜索查询（自然语言描述）
            top_k: 返回结果数量

        Returns:
            List[Dict]: 书籍列表，包含相关度分数

        Raises:
            RuntimeError: 当 agentic-rag 服务不可用或返回错误时抛出
        """
        url = f"{self.base_url}/api/rag/search"
        params = {"query": query, "top_k": min(top_k, 50)}

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        if not data.get("success"):
            raise RuntimeError(
                f"agentic-rag 搜索返回错误: {data.get('error', 'unknown')}"
            )

        results = data.get("results", [])
        mapped = []
        for r in results:
            mapped.append({
                "id": int(r.get("book_id", 0)),
                "title": r.get("title", ""),
                "author": r.get("author", ""),
                "price": r.get("price", 0),
                "category": r.get("category", ""),
                "score": r.get("relevance_score", 0),
            })
        return mapped[:top_k]


# 全局向量检索客户端实例
vector_store = AgenticRAGClient()

# 本地备用书籍数据（供 db_query / get_popular_books 使用）
FALLBACK_BOOKS = [
    {"id": 1, "title": "Python编程从入门到实践", "author": "Eric Matthes",
     "price": 89.0, "category": "Python"},
    {"id": 2, "title": "算法导论", "author": "Thomas Cormen",
     "price": 128.0, "category": "算法"},
    {"id": 3, "title": "深度学习", "author": "Ian Goodfellow",
     "price": 168.0, "category": "机器学习"},
    {"id": 4, "title": "Java核心技术", "author": "Cay Horstmann",
     "price": 149.0, "category": "Java"},
    {"id": 5, "title": "数据结构与算法分析", "author": "Mark Allen Weiss",
     "price": 79.0, "category": "算法"},
    {"id": 6, "title": "流畅的Python", "author": "Luciano Ramalho",
     "price": 139.0, "category": "Python"},
    {"id": 7, "title": "机器学习实战", "author": "Peter Harrington",
     "price": 89.0, "category": "机器学习"},
    {"id": 8, "title": "数据库系统概论", "author": "王珊",
     "price": 59.0, "category": "数据库"},
    {"id": 9, "title": "计算机网络", "author": "谢希仁",
     "price": 49.0, "category": "网络"},
    {"id": 10, "title": "操作系统概论", "author": "汤小丹",
     "price": 55.0, "category": "操作系统"},
]


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
    # 本地模拟数据库查询（基于 fallback 书籍数据）
    results = []

    for book in FALLBACK_BOOKS:
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
        book = next((b for b in FALLBACK_BOOKS if b["id"] == pop["id"]), None)
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
