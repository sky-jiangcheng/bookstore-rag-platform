"""
可观测性系统集成配置

整合 Prometheus、Jaeger、结构化日志
"""

import logging
import time
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from app.core.logging_config import LogContext, setup_logging
from app.core.metrics import (MetricsCollector, metrics_registry)
from app.core.tracing import (TracingContext, get_jaeger_tracer,
                              initialize_jaeger_tracer)

logger = logging.getLogger(__name__)


class ObservabilityMiddleware:
    """可观测性中间件"""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, request: Request, call_next):
        """处理请求"""
        # 记录请求开始
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", str(time.time()))

        # 添加请求 ID 到请求状态
        request.state.request_id = request_id

        # 创建追踪上下文
        get_jaeger_tracer()
        with TracingContext(
            f"{request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "request_id": request_id,
            },
        ) as span:
            try:
                response = await call_next(request)

                # 记录成功请求
                duration = time.time() - start_time
                MetricsCollector.record_request(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code,
                    duration=duration,
                )

                # 添加自定义响应头
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Process-Time"] = str(duration)

                return response

            except Exception as e:
                # 记录错误
                duration = time.time() - start_time
                MetricsCollector.record_error(
                    error_type=type(e).__name__, endpoint=request.url.path
                )

                if span:
                    span.record_exception(e)

                logger.error(
                    f"请求处理失败: {str(e)}",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration": duration,
                    },
                    exc_info=True,
                )

                raise


def setup_observability(
    app: FastAPI,
    service_name: str = "bookstore",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
    log_file: Optional[str] = None,
    log_level: str = "INFO",
) -> None:
    """
    设置完整的可观测性系统

    Args:
        app: FastAPI 应用
        service_name: 服务名称
        jaeger_host: Jaeger 主机
        jaeger_port: Jaeger 端口
        log_file: 日志文件路径
        log_level: 日志级别
    """

    # 1. 设置结构化日志
    setup_logging(level=log_level, log_file=log_file, json_format=True)
    logger.info(
        "结构化日志系统已初始化",
        log_level=log_level,
        log_file=log_file,
    )

    # 2. 初始化 Jaeger 追踪
    jaeger_tracer = initialize_jaeger_tracer(
        service_name=service_name,
        jaeger_host=jaeger_host,
        jaeger_port=jaeger_port,
    )

    if jaeger_tracer:
        logger.info(
            "Jaeger 追踪系统已初始化",
            jaeger_host=jaeger_host,
            jaeger_port=jaeger_port,
        )

        # 为 FastAPI 添加追踪
        jaeger_tracer.instrument_fastapi(app)
        jaeger_tracer.instrument_requests()
        jaeger_tracer.instrument_httpx()

    # 3. 添加可观测性中间件
    app.add_middleware(ObservabilityMiddleware)
    logger.info("可观测性中间件已添加")

    # 4. 添加 Prometheus 指标端点
    @app.get("/metrics")
    async def metrics():
        """Prometheus 指标端点"""
        from prometheus_client import generate_latest

        return PlainTextResponse(
            generate_latest(metrics_registry),
            media_type="text/plain",
        )

    logger.info("Prometheus 指标端点已注册: /metrics")

    # 5. 添加健康检查端点
    @app.get("/health")
    async def health():
        """健康检查端点"""
        return {
            "status": "healthy",
            "service": service_name,
            "timestamp": time.time(),
        }

    logger.info("健康检查端点已注册: /health")

    # 6. 添加就绪检查端点
    @app.get("/ready")
    async def readiness():
        """就绪检查端点"""
        # 这里可以检查数据库、缓存等依赖
        return {
            "ready": True,
            "service": service_name,
            "timestamp": time.time(),
        }

    logger.info("就绪检查端点已注册: /ready")

    logger.info("可观测性系统设置完成")


def get_observability_status() -> dict:
    """获取可观测性系统状态"""
    return {
        "logging": "enabled",
        "tracing": "enabled" if get_jaeger_tracer() else "disabled",
        "metrics": "enabled",
        "timestamp": time.time(),
    }


# 便捷函数


def trace_and_log_operation(operation: str):
    """装饰器：同时添加追踪和日志"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with LogContext(operation):
                tracer = get_jaeger_tracer()
                if tracer:
                    with TracingContext(operation):
                        return await func(*args, **kwargs)
                else:
                    return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            with LogContext(operation):
                tracer = get_jaeger_tracer()
                if tracer:
                    with TracingContext(operation):
                        return func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
