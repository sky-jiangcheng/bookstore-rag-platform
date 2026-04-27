from fastapi import APIRouter

from .api import (
    async_import,
    book_management,
    duplicate_management,
    filter_management,
    import_management,
    log_management,
    purchase_management,
    replenishment,
    task_management,
)

router = APIRouter()
router.include_router(import_management.router, prefix="/api/v1/import", tags=["数据导入"])
router.include_router(duplicate_management.router, prefix="/api/v1/duplicates", tags=["智能查重"])
router.include_router(book_management.router, prefix="/api/v1", tags=["图书管理"])
router.include_router(replenishment.router, prefix="/api/v1/replenishment", tags=["补货管理"])
router.include_router(purchase_management.router, prefix="/api/v1", tags=["采购管理"])
router.include_router(filter_management.router)
router.include_router(async_import.router, prefix="/api/v1/import", tags=["异步导入"])
router.include_router(task_management.router, prefix="/api/v1/tasks", tags=["任务管理"])
router.include_router(log_management.router, prefix="/api/v1", tags=["日志管理"])
