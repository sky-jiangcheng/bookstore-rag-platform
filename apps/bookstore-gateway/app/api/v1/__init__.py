"""
API v1 路由模块

汇总所有 v1 版本的路由
"""

from fastapi import APIRouter

# 主书单流程已切到 AgentScope 主线，仅保留辅助路由
from app.api.v1.book_list.utilities import router as book_list_utilities_router

# 创建主路由器
router = APIRouter()

# 注册路由
router.include_router(book_list_utilities_router)

__all__ = ["router"]
