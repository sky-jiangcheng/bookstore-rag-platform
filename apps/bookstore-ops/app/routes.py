from fastapi import APIRouter

from .api import async_import, log_management, task_management, testing

router = APIRouter()
router.include_router(log_management.router, prefix="/api/v1", tags=["日志管理"])
router.include_router(task_management.router, prefix="/api/v1/tasks", tags=["任务管理"])
router.include_router(async_import.router, prefix="/api/v1/import", tags=["异步导入"])

# 仅在 development/testing 环境下注册测试路由
import os
_app_env = os.getenv("APP_ENV", "development").lower()
if _app_env in ("development", "testing"):
    router.include_router(testing.router)
