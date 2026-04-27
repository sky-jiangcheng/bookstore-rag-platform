"""
适配器模块
"""

from .book_list_adapter import (BookListAgentAdapter, adapt_booklist_result,
                                adapt_requirements)

__all__ = [
    "BookListAgentAdapter",
    "adapt_requirements",
    "adapt_booklist_result",
]
