"""
结构化日志系统

使用 structlog 实现 JSON 格式的结构化日志
"""

import logging
import json
import sys
from typing import Dict, Any, Optional
import structlog
from datetime import datetime
import uuid

# 初始化 structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


class RequestIdFilter(logging.Filter):
    """请求 ID 日志过滤器"""
    
    def filter(self, record):
        # 从线程本地变量或上下文中获取请求 ID
        request_id = getattr(record, 'request_id', None) or str(uuid.uuid4())
        record.request_id = request_id
        return True


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', None),
        }
        
        # 添加额外字段
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ('name', 'msg', 'args', 'created', 'filename', 'funcName',
                               'levelname', 'levelno', 'lineno', 'module', 'msecs',
                               'message', 'pathname', 'process', 'processName', 'relativeCreated',
                               'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info'):
                    if not key.startswith('_'):
                        log_data[key] = value
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True
) -> None:
    """
    设置日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径 (可选)
        json_format: 是否使用 JSON 格式
    """
    
    # 创建根日志记录器
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 添加请求 ID 过滤器
    request_id_filter = RequestIdFilter()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.addFilter(request_id_filter)
    
    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
        )
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定）
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.addFilter(request_id_filter)
            
            if json_format:
                file_handler.setFormatter(JSONFormatter())
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
                )
                file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"无法创建日志文件: {str(e)}")


def get_logger(name: str) -> Any:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, operation: str, **context_data):
        self.operation = operation
        self.context_data = context_data
        self.request_id = str(uuid.uuid4())
        self.logger = get_logger(__name__)
    
    def __enter__(self):
        self.logger.info(
            f"{self.operation} 开始",
            request_id=self.request_id,
            **self.context_data
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(
                f"{self.operation} 失败",
                request_id=self.request_id,
                exception_type=exc_type.__name__,
                exception_message=str(exc_val),
            )
        else:
            self.logger.info(
                f"{self.operation} 完成",
                request_id=self.request_id,
            )
    
    def log_event(self, event: str, **event_data):
        """记录事件"""
        self.logger.info(
            event,
            request_id=self.request_id,
            **event_data
        )
    
    def log_warning(self, warning: str, **warning_data):
        """记录警告"""
        self.logger.warning(
            warning,
            request_id=self.request_id,
            **warning_data
        )
    
    def log_error(self, error: str, **error_data):
        """记录错误"""
        self.logger.error(
            error,
            request_id=self.request_id,
            **error_data
        )


# 便捷函数

def log_operation(operation: str, **context_data):
    """装饰器：为操作添加日志"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with LogContext(operation, **context_data) as ctx:
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with LogContext(operation, **context_data) as ctx:
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_performance(threshold_ms: float = 1000):
    """装饰器：记录性能指标"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            import time
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start) * 1000
                logger = get_logger(func.__module__)
                
                if duration_ms > threshold_ms:
                    logger.warning(
                        f"{func.__name__} 执行时间超过阈值",
                        function=func.__name__,
                        duration_ms=duration_ms,
                        threshold_ms=threshold_ms,
                    )
                else:
                    logger.debug(
                        f"{func.__name__} 执行完成",
                        function=func.__name__,
                        duration_ms=duration_ms,
                    )
        
        def sync_wrapper(*args, **kwargs):
            import time
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start) * 1000
                logger = get_logger(func.__module__)
                
                if duration_ms > threshold_ms:
                    logger.warning(
                        f"{func.__name__} 执行时间超过阈值",
                        function=func.__name__,
                        duration_ms=duration_ms,
                        threshold_ms=threshold_ms,
                    )
                else:
                    logger.debug(
                        f"{func.__name__} 执行完成",
                        function=func.__name__,
                        duration_ms=duration_ms,
                    )
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
