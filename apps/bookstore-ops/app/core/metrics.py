"""
Prometheus 监控指标

用于系统可观测性，收集：
1. 请求延迟分布
2. 错误率统计
3. 熔断器状态
4. 任务队列深度
5. 缓存命中率
6. LLM API 调用统计
"""

import logging
import time
from typing import Callable, Optional

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    CollectorRegistry,
    REGISTRY,
)

logger = logging.getLogger(__name__)

# 创建指标注册表
metrics_registry = CollectorRegistry()

# ==================== 请求指标 ====================

# 请求计数器
request_count = Counter(
    'bookstore_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=metrics_registry
)

# 请求延迟直方图
request_duration = Histogram(
    'bookstore_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=metrics_registry
)

# 请求延迟摘要（用于计算分位数）
request_duration_summary = Summary(
    'bookstore_request_duration_summary_seconds',
    'HTTP request duration (summary)',
    ['method', 'endpoint'],
    registry=metrics_registry
)

# ==================== 业务指标 ====================

# 书单生成计数
booklist_generation_count = Counter(
    'bookstore_booklist_generation_total',
    'Total booklist generations',
    ['status', 'generation_method'],
    registry=metrics_registry
)

# 书单生成延迟
booklist_generation_duration = Histogram(
    'bookstore_booklist_generation_duration_seconds',
    'Booklist generation duration',
    ['generation_method'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=metrics_registry
)

# 推荐书单数量
booklist_recommendations_count = Gauge(
    'bookstore_booklist_recommendations_count',
    'Number of recommendations in booklist',
    ['cognitive_level'],
    registry=metrics_registry
)

# 需求解析计数
requirement_parsing_count = Counter(
    'bookstore_requirement_parsing_total',
    'Total requirement parsing operations',
    ['confidence_level', 'status'],
    registry=metrics_registry
)

# ==================== 服务指标 ====================

# LLM API 调用计数
llm_api_calls = Counter(
    'bookstore_llm_api_calls_total',
    'Total LLM API calls',
    ['provider', 'status'],
    registry=metrics_registry
)

# LLM API 延迟
llm_api_duration = Histogram(
    'bookstore_llm_api_duration_seconds',
    'LLM API response time',
    ['provider'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=metrics_registry
)

# 向量查询计数
vector_query_count = Counter(
    'bookstore_vector_query_total',
    'Total vector queries',
    ['status'],
    registry=metrics_registry
)

# 向量查询延迟
vector_query_duration = Histogram(
    'bookstore_vector_query_duration_seconds',
    'Vector query duration',
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
    registry=metrics_registry
)

# 数据库查询计数
db_query_count = Counter(
    'bookstore_db_query_total',
    'Total database queries',
    ['table', 'operation', 'status'],
    registry=metrics_registry
)

# 数据库查询延迟
db_query_duration = Histogram(
    'bookstore_db_query_duration_seconds',
    'Database query duration',
    ['table', 'operation'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=metrics_registry
)

# ==================== 熔断器指标 ====================

# 熔断器状态
circuit_breaker_state = Gauge(
    'bookstore_circuit_breaker_state',
    'Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)',
    ['service'],
    registry=metrics_registry
)

# 熔断器失败次数
circuit_breaker_failures = Counter(
    'bookstore_circuit_breaker_failures_total',
    'Circuit breaker failure count',
    ['service'],
    registry=metrics_registry
)

# 熔断器打开次数
circuit_breaker_opens = Counter(
    'bookstore_circuit_breaker_opens_total',
    'Circuit breaker open count',
    ['service'],
    registry=metrics_registry
)

# ==================== 缓存指标 ====================

# 缓存命中次数
cache_hits = Counter(
    'bookstore_cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=metrics_registry
)

# 缓存未命中次数
cache_misses = Counter(
    'bookstore_cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=metrics_registry
)

# 缓存大小
cache_size = Gauge(
    'bookstore_cache_size_bytes',
    'Cache size in bytes',
    ['cache_type'],
    registry=metrics_registry
)

# ==================== 异步任务指标 ====================

# 任务提交计数
task_submitted_count = Counter(
    'bookstore_tasks_submitted_total',
    'Total tasks submitted',
    ['task_type'],
    registry=metrics_registry
)

# 任务完成计数
task_completed_count = Counter(
    'bookstore_tasks_completed_total',
    'Total tasks completed',
    ['task_type', 'status'],
    registry=metrics_registry
)

# 任务处理延迟
task_processing_duration = Histogram(
    'bookstore_task_processing_duration_seconds',
    'Task processing duration',
    ['task_type'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0),
    registry=metrics_registry
)

# 队列深度
queue_depth = Gauge(
    'bookstore_queue_depth',
    'Current queue depth',
    ['queue_name'],
    registry=metrics_registry
)

# ==================== 系统指标 ====================

# 活跃对话数
active_conversations = Gauge(
    'bookstore_active_conversations',
    'Number of active conversations',
    registry=metrics_registry
)

# 用户数
active_users = Gauge(
    'bookstore_active_users',
    'Number of active users',
    registry=metrics_registry
)

# 错误计数
errors_total = Counter(
    'bookstore_errors_total',
    'Total errors',
    ['error_type', 'endpoint'],
    registry=metrics_registry
)

# 异常计数
exceptions_total = Counter(
    'bookstore_exceptions_total',
    'Total exceptions',
    ['exception_type'],
    registry=metrics_registry
)


# ==================== 便捷装饰器 ====================


def track_request_duration(method: str, endpoint: str):
    """装饰器：追踪请求延迟"""
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start
                request_duration.labels(method=method, endpoint=endpoint).observe(duration)
                request_duration_summary.labels(method=method, endpoint=endpoint).observe(duration)
        
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start
                request_duration.labels(method=method, endpoint=endpoint).observe(duration)
                request_duration_summary.labels(method=method, endpoint=endpoint).observe(duration)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_operation_duration(operation_name: str, labels: Optional[dict] = None):
    """装饰器：追踪操作延迟"""
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                logger.info(f"{operation_name} 耗时 {duration:.3f}s", extra={"duration": duration, **(labels or {})})
        
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                logger.info(f"{operation_name} 耗时 {duration:.3f}s", extra={"duration": duration, **(labels or {})})
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ==================== 指标收集器 ====================


class MetricsCollector:
    """指标收集器"""
    
    @staticmethod
    def record_request(method: str, endpoint: str, status: int, duration: float):
        """记录请求"""
        request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        request_duration.labels(method=method, endpoint=endpoint).observe(duration)
        request_duration_summary.labels(method=method, endpoint=endpoint).observe(duration)
    
    @staticmethod
    def record_booklist_generation(status: str, method: str, duration: float, count: int):
        """记录书单生成"""
        booklist_generation_count.labels(status=status, generation_method=method).inc()
        booklist_generation_duration.labels(generation_method=method).observe(duration)
        booklist_recommendations_count.labels(cognitive_level="general").set(count)
    
    @staticmethod
    def record_llm_call(provider: str, status: str, duration: float):
        """记录 LLM API 调用"""
        llm_api_calls.labels(provider=provider, status=status).inc()
        llm_api_duration.labels(provider=provider).observe(duration)
    
    @staticmethod
    def record_vector_query(status: str, duration: float):
        """记录向量查询"""
        vector_query_count.labels(status=status).inc()
        vector_query_duration.observe(duration)
    
    @staticmethod
    def record_db_query(table: str, operation: str, status: str, duration: float):
        """记录数据库查询"""
        db_query_count.labels(table=table, operation=operation, status=status).inc()
        db_query_duration.labels(table=table, operation=operation).observe(duration)
    
    @staticmethod
    def record_cache_hit(cache_type: str):
        """记录缓存命中"""
        cache_hits.labels(cache_type=cache_type).inc()
    
    @staticmethod
    def record_cache_miss(cache_type: str):
        """记录缓存未命中"""
        cache_misses.labels(cache_type=cache_type).inc()
    
    @staticmethod
    def record_task_submitted(task_type: str):
        """记录任务提交"""
        task_submitted_count.labels(task_type=task_type).inc()
    
    @staticmethod
    def record_task_completed(task_type: str, status: str, duration: float):
        """记录任务完成"""
        task_completed_count.labels(task_type=task_type, status=status).inc()
        task_processing_duration.labels(task_type=task_type).observe(duration)
    
    @staticmethod
    def record_error(error_type: str, endpoint: str):
        """记录错误"""
        errors_total.labels(error_type=error_type, endpoint=endpoint).inc()
    
    @staticmethod
    def record_exception(exception_type: str):
        """记录异常"""
        exceptions_total.labels(exception_type=exception_type).inc()
    
    @staticmethod
    def set_circuit_breaker_state(service: str, state: int):
        """设置熔断器状态"""
        circuit_breaker_state.labels(service=service).set(state)
    
    @staticmethod
    def set_active_conversations(count: int):
        """设置活跃对话数"""
        active_conversations.set(count)
    
    @staticmethod
    def set_active_users(count: int):
        """设置活跃用户数"""
        active_users.set(count)


# ==================== 指标导出 ====================


def get_metrics_summary() -> dict:
    """获取指标汇总"""
    from prometheus_client import CollectorRegistry, generate_latest
    
    return {
        'timestamp': time.time(),
        'metrics': generate_latest(metrics_registry).decode('utf-8'),
    }


def export_metrics_to_file(filepath: str):
    """导出指标到文件"""
    from prometheus_client import generate_latest
    
    with open(filepath, 'w') as f:
        f.write(generate_latest(metrics_registry).decode('utf-8'))
    
    logger.info(f"指标已导出到 {filepath}")
