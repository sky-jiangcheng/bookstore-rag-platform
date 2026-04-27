"""
API 共享模块

包含依赖注入、异常处理等通用功能
"""

from app.api.v1.shared.dependencies import (
    get_cache_service,
    get_llm_service,
    get_vector_db_service,
    get_vector_service,
    handle_service_error,
)

__all__ = [
    "get_cache_service",
    "get_llm_service",
    "get_vector_db_service",
    "get_vector_service",
    "handle_service_error",
]
