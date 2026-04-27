"""按服务域组装 FastAPI 应用的工厂。"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RouterSpec:
    module_path: str
    prefix: str = ""
    tags: Tuple[str, ...] = ()


SERVICE_ROUTES: Dict[str, List[RouterSpec]] = {
    "gateway": [
        RouterSpec("app.api.auth_management", "/api/v1/auth", ("认证",)),
        RouterSpec("app.api.import_management", "/api/v1/import", ("数据导入",)),
        RouterSpec("app.api.duplicate_management", "/api/v1/duplicates", ("智能查重",)),
        RouterSpec("app.api.log_management", "/api/v1", ("日志管理",)),
        RouterSpec("app.api.book_management", "/api/v1", ("图书管理",)),
        RouterSpec("app.api.user_management", "/api/v1", ("用户角色管理",)),
        RouterSpec("app.api.purchase_management", "/api/v1", ("采购管理",)),
        RouterSpec("app.api.smart_recommendation", "/api/v1", ("智能推荐",)),
        RouterSpec("app.api.recommendation", "/api/v1/recommendation", ("推荐管理",)),
        RouterSpec("app.api.replenishment", "/api/v1/replenishment", ("补货管理",)),
        RouterSpec(
            "app.api.book_list_recommendation_agentic", "", ("书单管理（AgentScope 主线）",)
        ),
        RouterSpec("app.api.book_list_template", "", ("书单模板管理",)),
        RouterSpec("app.api.book_list_feedback", "", ("书单满意度反馈",)),
        RouterSpec("app.api.v1.book_list.utilities", "", ("书单管理辅助接口",)),
        RouterSpec("app.api.demand_analysis", "", ("需求解析",)),
        RouterSpec("app.api.filter_management", "", ()),
        RouterSpec("app.api.testing", "", ()),
        RouterSpec("app.api.task_management", "/api/v1/tasks", ("任务管理",)),
        RouterSpec("app.api.async_import", "/api/v1/import", ("异步导入",)),
        RouterSpec("app.api.batch_search", "/api/v1/search", ("批量搜索",)),
        RouterSpec("app.api.agent_api", "", ()),
    ],
    "auth": [
        RouterSpec("app.api.auth_management", "/api/v1/auth", ("认证",)),
        RouterSpec("app.api.user_management", "/api/v1", ("用户角色管理",)),
        RouterSpec("app.api.log_management", "/api/v1", ("日志管理",)),
    ],
    "rag": [
        RouterSpec("app.api.smart_recommendation", "/api/v1", ("智能推荐",)),
        RouterSpec("app.api.recommendation", "/api/v1/recommendation", ("推荐管理",)),
        RouterSpec(
            "app.api.book_list_recommendation_agentic", "", ("书单管理（AgentScope 主线）",)
        ),
        RouterSpec("app.api.book_list_template", "", ("书单模板管理",)),
        RouterSpec("app.api.book_list_feedback", "", ("书单满意度反馈",)),
        RouterSpec("app.api.v1.book_list.utilities", "", ("书单管理辅助接口",)),
        RouterSpec("app.api.demand_analysis", "", ("需求解析",)),
        RouterSpec("app.api.batch_search", "/api/v1/search", ("批量搜索",)),
        RouterSpec("app.api.agent_api", "", ()),
        RouterSpec("app.api.testing", "", ()),
    ],
    "catalog": [
        RouterSpec("app.api.import_management", "/api/v1/import", ("数据导入",)),
        RouterSpec("app.api.duplicate_management", "/api/v1/duplicates", ("智能查重",)),
        RouterSpec("app.api.book_management", "/api/v1", ("图书管理",)),
        RouterSpec("app.api.replenishment", "/api/v1/replenishment", ("补货管理",)),
        RouterSpec("app.api.purchase_management", "/api/v1", ("采购管理",)),
        RouterSpec("app.api.filter_management", "", ()),
        RouterSpec("app.api.async_import", "/api/v1/import", ("异步导入",)),
        RouterSpec("app.api.task_management", "/api/v1/tasks", ("任务管理",)),
        RouterSpec("app.api.log_management", "/api/v1", ("日志管理",)),
    ],
    "ops": [
        RouterSpec("app.api.log_management", "/api/v1", ("日志管理",)),
        RouterSpec("app.api.task_management", "/api/v1/tasks", ("任务管理",)),
        RouterSpec("app.api.async_import", "/api/v1/import", ("异步导入",)),
        RouterSpec("app.api.testing", "", ()),
    ],
}


def _import_router(module_path: str):
    module = importlib.import_module(module_path)
    return getattr(module, "router")


def create_service_app(service_name: str = "gateway") -> FastAPI:
    """根据服务域创建应用实例。"""
    normalized = service_name.strip().lower()

    from app.config import CORS_ORIGINS

    app = FastAPI(
        title=f"书店智能管理系统API ({normalized})",
        description="基于AI的书店管理系统API",
        version="1.0.0",
    )
    app.state.service_name = normalized
    app.state.database_ready = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    route_specs = SERVICE_ROUTES.get(normalized, SERVICE_ROUTES["gateway"])

    for spec in route_specs:
        router = _import_router(spec.module_path)
        include_kwargs = {}
        if spec.prefix:
            include_kwargs["prefix"] = spec.prefix
        if spec.tags:
            include_kwargs["tags"] = list(spec.tags)
        app.include_router(router, **include_kwargs)

    @app.get("/")
    async def root():
        return {"message": "书店智能管理系统API", "service": normalized}

    @app.get("/health")
    async def health_check():
        status = (
            "healthy"
            if app.state.database_ready or normalized != "gateway"
            else "degraded"
        )
        return {"status": status, "service": normalized}

    @app.on_event("startup")
    async def startup_event():
        from app.utils.database import engine

        from .bootstrap import initialize_runtime

        app.state.database_ready = initialize_runtime(engine=engine, logger=logger)

    return app
