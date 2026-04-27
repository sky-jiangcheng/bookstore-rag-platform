from fastapi import APIRouter

from .api import (
    agent_api,
    async_import,
    auth_management,
    batch_search,
    book_list_feedback,
    book_list_recommendation_agentic,
    book_list_template,
    book_management,
    demand_analysis,
    duplicate_management,
    filter_management,
    import_management,
    log_management,
    purchase_management,
    recommendation,
    replenishment,
    smart_recommendation,
    task_management,
    testing,
    user_management,
)
from .api.v1.book_list import utilities

router = APIRouter()
router.include_router(auth_management.router, prefix="/api/v1/auth", tags=["认证"])
router.include_router(import_management.router, prefix="/api/v1/import", tags=["数据导入"])
router.include_router(duplicate_management.router, prefix="/api/v1/duplicates", tags=["智能查重"])
router.include_router(log_management.router, prefix="/api/v1", tags=["日志管理"])
router.include_router(book_management.router, prefix="/api/v1", tags=["图书管理"])
router.include_router(user_management.router, prefix="/api/v1", tags=["用户角色管理"])
router.include_router(purchase_management.router, prefix="/api/v1", tags=["采购管理"])
router.include_router(smart_recommendation.router, prefix="/api/v1", tags=["智能推荐"])
router.include_router(recommendation.router, prefix="/api/v1/recommendation", tags=["推荐管理"])
router.include_router(replenishment.router, prefix="/api/v1/replenishment", tags=["补货管理"])
router.include_router(book_list_recommendation_agentic.router, tags=["书单管理（AgentScope 主线）"])
router.include_router(book_list_template.router, tags=["书单模板管理"])
router.include_router(book_list_feedback.router, tags=["书单满意度反馈"])
router.include_router(utilities.router, tags=["书单管理辅助接口"])
router.include_router(demand_analysis.router, tags=["需求解析"])
router.include_router(filter_management.router)
router.include_router(testing.router)
router.include_router(task_management.router, prefix="/api/v1/tasks", tags=["任务管理"])
router.include_router(async_import.router, prefix="/api/v1/import", tags=["异步导入"])
router.include_router(batch_search.router, prefix="/api/v1/search", tags=["批量搜索"])
router.include_router(agent_api.router)
