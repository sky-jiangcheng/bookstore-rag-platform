"""按服务域组装 FastAPI 应用的工厂。"""

from __future__ import annotations

import importlib
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx

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
        RouterSpec("app.api.book_list_recommendation_agentic", "", ("书单管理（AgentScope 主线）",)),
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
        RouterSpec("app.api.agent_proxy", "/api/v1/agent", ("Agent Proxy",)),
    ],
    "platform": [
        RouterSpec("app.api.auth_management", "/api/v1/auth", ("认证",)),
        RouterSpec("app.api.smart_recommendation", "/api/v1", ("智能推荐",)),
        RouterSpec("app.api.recommendation", "/api/v1/recommendation", ("推荐管理",)),
        RouterSpec("app.api.book_list_recommendation_agentic", "", ("书单管理（AgentScope 主线）",)),
        RouterSpec("app.api.book_list_template", "", ("书单模板管理",)),
        RouterSpec("app.api.book_list_feedback", "", ("书单满意度反馈",)),
        RouterSpec("app.api.book_list_export", "", ("书单导出",)),
        RouterSpec("app.api.v1.book_list.utilities", "", ("书单管理辅助接口",)),
        RouterSpec("app.api.demand_analysis", "", ("需求解析",)),
        RouterSpec("app.api.agent_api", "", ()),
        RouterSpec("app.api.agent_proxy", "/api/v1/agent", ("Agent Proxy",)),
    ],
    "auth": [
        RouterSpec("app.api.auth_management", "/api/v1/auth", ("认证",)),
        RouterSpec("app.api.user_management", "/api/v1", ("用户角色管理",)),
        RouterSpec("app.api.log_management", "/api/v1", ("日志管理",)),
    ],
    "rag": [
        RouterSpec("app.api.smart_recommendation", "/api/v1", ("智能推荐",)),
        RouterSpec("app.api.recommendation", "/api/v1/recommendation", ("推荐管理",)),
        RouterSpec("app.api.book_list_recommendation_agentic", "", ("书单管理（AgentScope 主线）",)),
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

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        # --- Startup ---
        # Only create the httpx client for services that use agent_proxy
        _needs_proxy = normalized in {"platform", "gateway"}
        if _needs_proxy:
            app.state.agentic_client = httpx.AsyncClient(
                timeout=httpx.Timeout(25.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
            )
            logger.info("agentic httpx client created (service=%s)", normalized)

        # Bootstrap database & runtime
        from .bootstrap import initialize_runtime
        from app.utils.database import engine
        app.state.database_ready = initialize_runtime(engine=engine, logger=logger)

        yield

        # --- Shutdown ---
        client: httpx.AsyncClient | None = getattr(app.state, "agentic_client", None)
        if client is not None:
            await client.aclose()
            logger.info("agentic httpx client closed")

    app = FastAPI(
        title=f"书店智能管理系统API ({normalized})",
        description="基于AI的书店管理系统API",
        version="1.0.0",
        lifespan=_lifespan,
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

    # 安全响应头中间件
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        # 浏览器安全基线头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # API 响应默认不嵌入 iframe
        if not request.url.path.startswith("/docs"):
            response.headers.setdefault("X-Frame-Options", "DENY")
        return response

    route_specs = SERVICE_ROUTES.get(normalized, SERVICE_ROUTES["gateway"])
    _app_env = os.getenv("APP_ENV", "development").lower()
    _safe_envs = {"development", "testing"}

    for spec in route_specs:
        # 仅在开发/测试环境下注册 testing 路由
        if "testing" in spec.module_path and _app_env not in _safe_envs:
            logger.warning(f"Skipping testing route '{spec.module_path}' in {_app_env} environment")
            continue
        router = _import_router(spec.module_path)
        include_kwargs = {}
        if spec.prefix:
            include_kwargs["prefix"] = spec.prefix
        if spec.tags:
            include_kwargs["tags"] = list(spec.tags)
        app.include_router(router, **include_kwargs)

    @app.get("/health")
    async def health_check():
        requires_bootstrap = normalized in {"gateway", "platform"}
        status = "healthy" if app.state.database_ready or not requires_bootstrap else "degraded"
        return {"status": status, "service": normalized}

    @app.get("/api/v1/health")
    async def health_check_v1():
        """兼容 /api/v1/health 的健康检查端点，返回与 /health 相同的 JSON。"""
        requires_bootstrap = normalized in {"gateway", "platform"}
        status = "healthy" if app.state.database_ready or not requires_bootstrap else "degraded"
        return {"status": status, "service": normalized}

    # 使用环境变量或基于 __file__ 的可靠路径计算确定项目根目录
    project_root = Path(os.getenv("PROJECT_ROOT", str(Path(__file__).resolve().parents[4])))
    frontend_dist = project_root / "apps" / "bookstore-frontend" / "dist"
    if normalized == "platform" and frontend_dist.exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")

        @app.get("/")
        async def root():
            return FileResponse(frontend_dist / "index.html")

        @app.get("/{page_name}.html")
        async def html_page(page_name: str):
            page_file = frontend_dist / f"{page_name}.html"
            if page_file.exists():
                return FileResponse(page_file)
            raise HTTPException(status_code=404, detail="Page not found")

        @app.get("/{path:path}")
        async def frontend_fallback(path: str):
            target = frontend_dist / path
            if target.is_file():
                return FileResponse(target)
            return FileResponse(frontend_dist / "index.html")
    else:
        @app.get("/")
        async def root():
            return {"message": "书店智能管理系统API", "service": normalized}

    return app
