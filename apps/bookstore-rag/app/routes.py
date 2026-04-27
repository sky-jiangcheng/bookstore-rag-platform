from fastapi import APIRouter

from app.api import (
    agent_api,
    batch_search,
    book_list_feedback,
    book_list_recommendation_agentic,
    book_list_template,
    book_filter_management,
    demand_analysis,
    recommendation,
    smart_recommendation,
    testing,
)
from app.api.v1.book_list import utilities

router = APIRouter()
router.include_router(smart_recommendation.router, prefix="/api/v1", tags=["智能推荐"])
router.include_router(recommendation.router, prefix="/api/v1/recommendation", tags=["推荐管理"])
router.include_router(book_list_recommendation_agentic.router, tags=["书单管理（AgentScope 主线）"])
router.include_router(book_list_template.router, tags=["书单模板管理"])
router.include_router(book_list_feedback.router, tags=["书单满意度反馈"])
router.include_router(demand_analysis.router, tags=["需求解析"])
router.include_router(batch_search.router, prefix="/api/v1/search", tags=["批量搜索"])
router.include_router(agent_api.router)
router.include_router(testing.router)
router.include_router(utilities.router, tags=["书单管理辅助接口"])
router.include_router(book_filter_management.router, prefix="/api/v1", tags=["图书筛选管理"])
