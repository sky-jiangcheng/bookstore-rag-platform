"""
Jaeger 链路追踪配置

用于分布式链路追踪，完整记录请求在系统中的调用过程
"""

import logging
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


class JaegerTracer:
    """
    Jaeger 链路追踪管理器

    用于记录分布式系统中的完整调用链路
    """

    def __init__(
        self,
        service_name: str = "bookstore",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
    ):
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.tracer_provider = None
        self.tracer = None

    def initialize(self):
        """初始化追踪器"""
        try:
            # 创建 Jaeger 导出器
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.jaeger_host,
                agent_port=self.jaeger_port,
            )

            # 创建资源
            resource = Resource(
                attributes={
                    SERVICE_NAME: self.service_name,
                    "environment": "production",
                }
            )

            # 创建追踪提供者
            self.tracer_provider = TracerProvider(resource=resource)

            # 添加批处理导出器
            self.tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

            # 设置全局追踪提供者
            trace.set_tracer_provider(self.tracer_provider)

            # 获取追踪器
            self.tracer = trace.get_tracer(__name__)

            logger.info(f"Jaeger 追踪器已初始化: " f"{self.jaeger_host}:{self.jaeger_port}")

            return True

        except Exception as e:
            logger.error(f"Jaeger 追踪器初始化失败: {str(e)}")
            return False

    def instrument_fastapi(self, app):
        """为 FastAPI 应用添加追踪"""
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI 追踪已启用")
        except Exception as e:
            logger.warning(f"FastAPI 追踪启用失败: {str(e)}")

    def instrument_sqlalchemy(self, engine):
        """为 SQLAlchemy 引擎添加追踪"""
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.info("SQLAlchemy 追踪已启用")
        except Exception as e:
            logger.warning(f"SQLAlchemy 追踪启用失败: {str(e)}")

    def instrument_redis(self):
        """为 Redis 客户端添加追踪"""
        try:
            RedisInstrumentor().instrument()
            logger.info("Redis 追踪已启用")
        except Exception as e:
            logger.warning(f"Redis 追踪启用失败: {str(e)}")

    def instrument_requests(self):
        """为 requests 库添加追踪"""
        try:
            RequestsInstrumentor().instrument()
            logger.info("Requests 追踪已启用")
        except Exception as e:
            logger.warning(f"Requests 追踪启用失败: {str(e)}")

    def instrument_httpx(self):
        """为 httpx 库添加追踪"""
        try:
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX 追踪已启用")
        except Exception as e:
            logger.warning(f"HTTPX 追踪启用失败: {str(e)}")

    def create_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """创建 span"""
        if not self.tracer:
            return None

        span = self.tracer.start_span(name)

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        return span

    def record_exception(self, span, exception: Exception):
        """记录异常到 span"""
        if span:
            span.record_exception(exception)

    def set_span_status(self, span, status: str):
        """设置 span 状态"""
        if span:
            from opentelemetry.trace import Status, StatusCode

            if status == "error":
                span.set_status(Status(StatusCode.ERROR))
            elif status == "ok":
                span.set_status(Status(StatusCode.OK))


# 全局追踪器实例
_jaeger_tracer: Optional[JaegerTracer] = None


def initialize_jaeger_tracer(
    service_name: str = "bookstore",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
) -> JaegerTracer:
    """初始化全局追踪器"""
    global _jaeger_tracer

    _jaeger_tracer = JaegerTracer(
        service_name=service_name, jaeger_host=jaeger_host, jaeger_port=jaeger_port
    )
    _jaeger_tracer.initialize()

    return _jaeger_tracer


def get_jaeger_tracer() -> Optional[JaegerTracer]:
    """获取全局追踪器"""
    return _jaeger_tracer


class TracingContext:
    """追踪上下文管理器"""

    def __init__(self, span_name: str, attributes: Optional[Dict[str, Any]] = None):
        self.span_name = span_name
        self.attributes = attributes or {}
        self.span = None

    def __enter__(self):
        tracer = get_jaeger_tracer()
        if tracer:
            self.span = tracer.create_span(self.span_name, self.attributes)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.record_exception(exc_val)
                tracer = get_jaeger_tracer()
                if tracer:
                    tracer.set_span_status(self.span, "error")
            else:
                tracer = get_jaeger_tracer()
                if tracer:
                    tracer.set_span_status(self.span, "ok")

            self.span.end()


def trace_operation(operation_name: str):
    """装饰器：为操作添加追踪"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            tracer = get_jaeger_tracer()
            if not tracer:
                return await func(*args, **kwargs)

            with TracingContext(operation_name) as span:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if span:
                        span.record_exception(e)
                    raise

        def sync_wrapper(*args, **kwargs):
            tracer = get_jaeger_tracer()
            if not tracer:
                return func(*args, **kwargs)

            with TracingContext(operation_name) as span:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if span:
                        span.record_exception(e)
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
