"""
API 依赖注入配置

定义常用的依赖、异常处理等
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BookRecommendationError,
    LLMServiceError,
    RAGServiceError,
    ValidationError,
    VectorServiceError,
)
from app.core.service_registry import get_service
from app.models.auth import User
from app.utils.database import get_db

logger = logging.getLogger(__name__)


async def get_llm_service():
    """获取 LLM 服务依赖"""
    llm_service = get_service("llm_service")
    if not llm_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM 服务不可用"
        )
    return llm_service


async def get_vector_service():
    """获取向量服务依赖"""
    vector_service = get_service("vector_service")
    if not vector_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="向量服务不可用"
        )
    return vector_service


async def get_vector_db_service():
    """获取向量数据库服务依赖"""
    vector_db = get_service("vector_db")
    if not vector_db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="向量数据库服务不可用"
        )
    return vector_db


async def get_cache_service():
    """获取缓存服务依赖"""
    cache_service = get_service("cache_service")
    if not cache_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="缓存服务不可用"
        )
    return cache_service


def handle_service_error(error: Exception, context: str = "操作") -> None:
    """
    处理服务层错误
    
    Args:
        error: 异常对象
        context: 错误上下文描述
    """
    logger.error(f"{context}失败: {str(error)}", exc_info=True)
    
    if isinstance(error, ValidationError):
        raise HTTPException(status_code=400, detail=str(error))
    elif isinstance(error, (LLMServiceError, VectorServiceError)):
        raise HTTPException(status_code=503, detail=f"服务不可用: {str(error)}")
    elif isinstance(error, BookRecommendationError):
        raise HTTPException(status_code=404, detail=str(error))
    elif isinstance(error, RAGServiceError):
        raise HTTPException(status_code=503, detail=f"检索服务错误: {str(error)}")
    else:
        raise HTTPException(status_code=500, detail=f"系统错误: {str(error)}")
