"""
适配器模块
"""

from .book_list_adapter import BookListAgentAdapter, adapt_requirements, adapt_booklist_result

__all__ = [
    "BookListAgentAdapter",
    "adapt_requirements",
    "adapt_booklist_result",
]
