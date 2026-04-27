"""自定义异常类模块

定义应用中使用的自定义异常，提供统一的异常处理机制

Author: System
Date: 2026-02-01
"""
from typing import Any, Dict, Optional

from app.core.constants import HTTPStatusConstants


class BookStoreBaseException(Exception):
    """书店应用基础异常类"""

    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatusConstants.INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            status_code: HTTP状态码
            details: 详细错误信息
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            异常信息字典
        """
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


# ==================== 认证和授权异常 ====================
class AuthenticationError(BookStoreBaseException):
    """认证错误"""

    def __init__(self, message: str = "认证失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, HTTPStatusConstants.UNAUTHORIZED, details)


class AuthorizationError(BookStoreBaseException):
    """授权错误"""

    def __init__(self, message: str = "权限不足", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, HTTPStatusConstants.FORBIDDEN, details)


class TokenExpiredError(AuthenticationError):
    """令牌过期错误"""

    def __init__(self, message: str = "认证令牌已过期"):
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    """无效令牌错误"""

    def __init__(self, message: str = "无效的认证令牌"):
        super().__init__(message)


class UserNotFoundError(AuthenticationError):
    """用户不存在错误"""

    def __init__(self, message: str = "用户不存在"):
        super().__init__(message)


class UserInactiveError(AuthenticationError):
    """用户账户未激活错误"""

    def __init__(self, message: str = "用户账户已被禁用"):
        super().__init__(message)


class InvalidCredentialsError(AuthenticationError):
    """无效凭证错误"""

    def __init__(self, message: str = "用户名或密码错误"):
        super().__init__(message)


# ==================== 数据库异常 ====================
class DatabaseError(BookStoreBaseException):
    """数据库错误"""

    def __init__(
        self, message: str = "数据库操作失败", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, HTTPStatusConstants.INTERNAL_SERVER_ERROR, details)


class RecordNotFoundError(DatabaseError):
    """记录不存在错误"""

    def __init__(self, message: str = "记录不存在"):
        super().__init__(message, HTTPStatusConstants.NOT_FOUND)


class DuplicateRecordError(DatabaseError):
    """重复记录错误"""

    def __init__(self, message: str = "记录已存在"):
        super().__init__(message, HTTPStatusConstants.CONFLICT)


class DatabaseConnectionError(DatabaseError):
    """数据库连接错误"""

    def __init__(self, message: str = "数据库连接失败"):
        super().__init__(message, HTTPStatusConstants.SERVICE_UNAVAILABLE)


# ==================== 文件上传异常 ====================
class FileUploadError(BookStoreBaseException):
    """文件上传错误"""

    def __init__(
        self, message: str = "文件上传失败", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, HTTPStatusConstants.BAD_REQUEST, details)


class FileTooLargeError(FileUploadError):
    """文件过大错误"""

    def __init__(self, message: str = "文件大小超过限制", max_size: Optional[int] = None):
        details = {"max_size": max_size} if max_size else None
        super().__init__(message, details)


class InvalidFileFormatError(FileUploadError):
    """无效文件格式错误"""

    def __init__(
        self, message: str = "不支持的文件格式", allowed_formats: Optional[list] = None
    ):
        details = {"allowed_formats": allowed_formats} if allowed_formats else None
        super().__init__(message, details)


class NoFileUploadedError(FileUploadError):
    """未上传文件错误"""

    def __init__(self, message: str = "未上传文件"):
        super().__init__(message)


# ==================== LLM服务异常 ====================
class LLMServiceError(BookStoreBaseException):
    """LLM服务错误"""

    def __init__(
        self, message: str = "LLM服务调用失败", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, HTTPStatusConstants.INTERNAL_SERVER_ERROR, details)


class InvalidLLMProviderError(LLMServiceError):
    """无效LLM提供商错误"""

    def __init__(self, message: str = "无效的LLM提供商", provider: Optional[str] = None):
        details = {"provider": provider} if provider else None
        super().__init__(message, details)


class LLMAPIKeyMissingError(LLMServiceError):
    """LLM API密钥缺失错误"""

    def __init__(self, message: str = "缺少API密钥", provider: Optional[str] = None):
        details = {"provider": provider} if provider else None
        super().__init__(message, details)


class LLMAPIError(LLMServiceError):
    """LLM API调用错误"""

    def __init__(self, message: str = "LLM API调用失败", error_code: Optional[str] = None):
        details = {"error_code": error_code} if error_code else None
        super().__init__(message, details)


# ==================== 向量服务异常 ====================
class VectorServiceError(BookStoreBaseException):
    """向量服务错误"""

    def __init__(
        self, message: str = "向量服务操作失败", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, HTTPStatusConstants.INTERNAL_SERVER_ERROR, details)


class VectorDBConnectionError(VectorServiceError):
    """向量数据库连接错误"""

    def __init__(self, message: str = "向量数据库连接失败"):
        super().__init__(message, None)


class VectorSearchError(VectorServiceError):
    """向量搜索错误"""

    def __init__(self, message: str = "向量搜索失败", query: Optional[str] = None):
        details = {"query": query} if query else None
        super().__init__(message, details)


class EmbeddingGenerationError(VectorServiceError):
    """向量嵌入生成错误"""

    def __init__(self, message: str = "向量嵌入生成失败", text: Optional[str] = None):
        details = {"text": text[:100] if text else None} if text else None
        super().__init__(message, details)


# ==================== RAG服务异常 ====================
class RAGServiceError(BookStoreBaseException):
    """RAG服务错误"""

    def __init__(
        self, message: str = "RAG服务操作失败", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, HTTPStatusConstants.INTERNAL_SERVER_ERROR, details)


class RequirementParsingError(RAGServiceError):
    """需求解析错误"""

    def __init__(self, message: str = "需求解析失败", user_input: Optional[str] = None):
        details = {"user_input": user_input} if user_input else None
        super().__init__(message, details)


class BookRecommendationError(RAGServiceError):
    """书籍推荐错误"""

    def __init__(
        self, message: str = "书籍推荐生成失败", requirements: Optional[Dict[str, Any]] = None
    ):
        details = {"requirements": requirements} if requirements else None
        super().__init__(message, details)


# ==================== 配置异常 ====================
class ConfigurationError(BookStoreBaseException):
    """配置错误"""

    def __init__(self, message: str = "配置错误", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, HTTPStatusConstants.INTERNAL_SERVER_ERROR, details)


class MissingConfigError(ConfigurationError):
    """缺失配置错误"""

    def __init__(self, message: str = "缺少必要配置", config_key: Optional[str] = None):
        details = {"config_key": config_key} if config_key else None
        super().__init__(message, details)


class InvalidConfigError(ConfigurationError):
    """无效配置错误"""

    def __init__(
        self,
        message: str = "配置值无效",
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
    ):
        details = (
            {"config_key": config_key, "config_value": config_value}
            if config_key
            else None
        )
        super().__init__(message, details)


# ==================== 验证异常 ====================
class ValidationError(BookStoreBaseException):
    """验证错误"""

    def __init__(
        self,
        message: str = "验证失败",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if field and not details:
            details = {"field": field}
        super().__init__(message, HTTPStatusConstants.UNPROCESSABLE_ENTITY, details)


class InvalidInputError(ValidationError):
    """无效输入错误"""

    def __init__(self, message: str = "无效的输入参数", field: Optional[str] = None):
        super().__init__(message, field)


# ==================== 业务逻辑异常 ====================
class BusinessLogicError(BookStoreBaseException):
    """业务逻辑错误"""

    def __init__(
        self, message: str = "业务逻辑错误", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, HTTPStatusConstants.BAD_REQUEST, details)


class InsufficientStockError(BusinessLogicError):
    """库存不足错误"""

    def __init__(
        self,
        message: str = "库存不足",
        book_id: Optional[int] = None,
        available: Optional[int] = None,
    ):
        details = (
            {"book_id": book_id, "available_stock": available}
            if book_id and available is not None
            else None
        )
        super().__init__(message, details)


class DuplicateBookError(BusinessLogicError):
    """重复书籍错误"""

    def __init__(self, message: str = "书籍已存在", book_title: Optional[str] = None):
        details = {"book_title": book_title} if book_title else None
        super().__init__(message, details)
