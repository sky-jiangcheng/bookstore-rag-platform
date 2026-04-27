"""应用常量定义模块

集中管理应用中使用的常量，提高代码可读性和可维护性

Author: System
Date: 2026-02-01
"""

# ==================== 数据库常量 ====================
class DatabaseConstants:
    """数据库相关常量"""
    DEFAULT_SQLITE_URL = "sqlite:///./bookstore.db"
    DEFAULT_MYSQL_PORT = 3306
    DEFAULT_MYSQL_HOST = "localhost"
    DEFAULT_MYSQL_CHARSET = "utf8mb4"
    DEFAULT_MYSQL_DATABASE = "bookstore"
    DEFAULT_MYSQL_USER = "root"


# ==================== 向量服务常量 ====================
class VectorConstants:
    """向量服务相关常量"""
    DEFAULT_DIMENSION = 768
    DEFAULT_SIMILARITY_THRESHOLD = 0.8
    DEFAULT_PROVIDER = "openai"
    
    # 支持的向量提供商
    PROVIDER_OPENAI = "openai"
    PROVIDER_GEMINI = "gemini"
    PROVIDER_ALIYUN = "aliyun"
    PROVIDER_LOCAL = "local"


# ==================== LLM服务常量 ====================
class LLMConstants:
    """LLM服务相关常量"""
    # 支持的LLM提供商
    PROVIDER_OPENAI = "openai"
    PROVIDER_GEMINI = "gemini"
    PROVIDER_QWEN = "qwen"
    PROVIDER_ERNIE = "ernie"
    PROVIDER_ZHIPU = "zhipu"
    PROVIDER_LOCAL = "local"
    PROVIDER_MOCK = "mock"
    
    # 默认LLM配置
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 2000
    
    # OpenAI默认配置
    OPENAI_DEFAULT_MODEL = "gpt-3.5-turbo"
    OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"
    
    # Gemini默认配置
    GEMINI_DEFAULT_MODEL = "gemini-pro"
    
    # 通义千问默认配置
    QWEN_DEFAULT_MODEL = "qwen-turbo"
    QWEN_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # 文心一言默认配置
    ERNIE_DEFAULT_MODEL = "ERNIE-Bot-turbo"
    
    # 智谱GLM默认配置
    ZHIPU_DEFAULT_MODEL = "glm-4"
    ZHIPU_DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"


# ==================== RAG服务常量 ====================
class RAGConstants:
    """RAG服务相关常量"""
    # 向量数据库配置
    DEFAULT_QDRANT_HOST = "localhost"
    DEFAULT_QDRANT_PORT = 6333
    DEFAULT_QDRANT_COLLECTION = "bookstore"
    DEFAULT_QDRANT_TIMEOUT = 30
    
    # 嵌入模型配置
    DEFAULT_EMBEDDING_MODEL = "BAAI/bge-large-zh"
    DEFAULT_EMBEDDING_DIMENSION = 1024
    DEFAULT_EMBEDDING_MAX_LENGTH = 512
    DEFAULT_EMBEDDING_DEVICE = "cpu"
    
    # 搜索参数配置
    DEFAULT_SEARCH_TOP_K = 20
    DEFAULT_SEARCH_SCORE_THRESHOLD = 0.7
    DEFAULT_SEARCH_RERANK_TOP_K = 10
    DEFAULT_SEARCH_MAX_CANDIDATES = 100
    
    # 缓存配置
    DEFAULT_CACHE_TTL_SECONDS = 3600
    DEFAULT_CACHE_MAX_SIZE = 1000
    DEFAULT_CACHE_ENABLED = True
    
    # 书籍处理配置
    DEFAULT_BATCH_SIZE = 100
    DEFAULT_MAX_DESCRIPTION_LENGTH = 500
    DEFAULT_AUTO_GENERATE_DESCRIPTION = True


# ==================== 认证和安全常量 ====================
class AuthConstants:
    """认证和安全相关常量"""
    # JWT配置
    DEFAULT_ALGORITHM = "HS256"
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    MIN_SECRET_KEY_LENGTH = 32
    
    # 密码要求
    MIN_PASSWORD_LENGTH = 8
    MIN_STRONG_PASSWORD_LENGTH = 12


# ==================== API服务常量 ====================
class APIConstants:
    """API服务相关常量"""
    DEFAULT_API_HOST = "0.0.0.0"
    DEFAULT_API_PORT = 8000
    DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


# ==================== 缓存常量 ====================
class CacheConstants:
    """缓存相关常量"""
    DEFAULT_REDIS_URL = "redis://localhost:6379/0"
    DEFAULT_CACHE_TTL = 900  # 15分钟，单位秒


# ==================== 上传常量 ====================
class UploadConstants:
    """文件上传相关常量"""
    DEFAULT_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}


# ==================== 日志常量 ====================
class LogConstants:
    """日志相关常量"""
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_DIR = "logs"
    LOG_FILE = "app.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 日志级别
    LEVEL_DEBUG = "DEBUG"
    LEVEL_INFO = "INFO"
    LEVEL_WARNING = "WARNING"
    LEVEL_ERROR = "ERROR"
    LEVEL_CRITICAL = "CRITICAL"


# ==================== 环境常量 ====================
class EnvironmentConstants:
    """环境相关常量"""
    ENV_DEVELOPMENT = "development"
    ENV_TESTING = "testing"
    ENV_PRODUCTION = "production"
    
    # 环境变量键名
    ENV_KEY_APP_ENV = "APP_ENV"
    ENV_KEY_DB_HOST = "DB_HOST"
    ENV_KEY_DB_PORT = "DB_PORT"
    ENV_KEY_DB_USER = "DB_USER"
    ENV_KEY_DB_PASSWORD = "DB_PASSWORD"
    ENV_KEY_DB_NAME = "DB_NAME"


# ==================== 嵌入模型维度映射 ====================
class EmbeddingModelDimensions:
    """嵌入模型维度映射表"""
    DIMENSIONS = {
        # OpenAI
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        
        # Google Gemini
        "models/embedding-001": 768,
        "models/text-embedding-004": 768,
        
        # BGE (Beijing Academy of Artificial Intelligence)
        "BAAI/bge-small-zh": 512,
        "BAAI/bge-base-zh": 768,
        "BAAI/bge-large-zh": 1024,
        "BAAI/bge-small-en-v1.5": 384,
        "BAAI/bge-base-en-v1.5": 768,
        "BAAI/bge-large-en-v1.5": 1024,
        
        # M3E
        "m3e-base": 768,
        "m3e-large": 1024,
        
        # text2vec
        "text2vec-base-chinese": 768,
        "text2vec-large-chinese": 1024,
        
        # Multilingual-E5
        "intfloat/multilingual-e5-small": 384,
        "intfloat/multilingual-e5-base": 768,
        "intfloat/multilingual-e5-large": 1024,
        
        # GTE (Alibaba)
        "thenlper/gte-small": 384,
        "thenlper/gte-base": 768,
        "thenlper/gte-large": 1024,
        
        # 其他
        "paraphrase-multilingual-MiniLM-L12-v2": 384,
        "all-MiniLM-L6-v2": 384,
        "all-MiniLM-L12-v2": 384,
    }
    
    @classmethod
    def get_dimension(cls, model_name: str, default: int = 768) -> int:
        """获取模型维度
        
        Args:
            model_name: 模型名称
            default: 默认维度
            
        Returns:
            模型维度
        """
        # 精确匹配
        if model_name in cls.DIMENSIONS:
            return cls.DIMENSIONS[model_name]
        
        # 模糊匹配
        for pattern, dimension in cls.DIMENSIONS.items():
            if pattern.lower() in model_name.lower():
                return dimension
        
        return default


# ==================== HTTP状态码常量 ====================
class HTTPStatusConstants:
    """HTTP状态码常量"""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# ==================== 错误消息常量 ====================
class ErrorMessages:
    """错误消息常量"""
    # 认证相关
    AUTH_INVALID_CREDENTIALS = "用户名或密码错误"
    AUTH_USER_NOT_FOUND = "用户不存在"
    AUTH_USER_INACTIVE = "用户账户已被禁用"
    AUTH_TOKEN_EXPIRED = "认证令牌已过期"
    AUTH_TOKEN_INVALID = "无效的认证令牌"
    AUTH_PERMISSION_DENIED = "权限不足"
    
    # 数据库相关
    DB_CONNECTION_ERROR = "数据库连接失败"
    DB_QUERY_ERROR = "数据库查询失败"
    DB_RECORD_NOT_FOUND = "记录不存在"
    DB_DUPLICATE_ENTRY = "记录已存在"
    
    # 文件上传相关
    UPLOAD_FILE_TOO_LARGE = "文件大小超过限制"
    UPLOAD_INVALID_FORMAT = "不支持的文件格式"
    UPLOAD_NO_FILE = "未上传文件"
    
    # LLM服务相关
    LLM_API_ERROR = "LLM服务调用失败"
    LLM_INVALID_PROVIDER = "无效的LLM提供商"
    LLM_API_KEY_MISSING = "缺少API密钥"
    
    # 向量服务相关
    VECTOR_DB_CONNECTION_ERROR = "向量数据库连接失败"
    VECTOR_SEARCH_ERROR = "向量搜索失败"
    VECTOR_EMBEDDING_ERROR = "向量嵌入生成失败"
    
    # 通用错误
    INTERNAL_ERROR = "内部服务器错误"
    INVALID_INPUT = "无效的输入参数"
    OPERATION_FAILED = "操作失败"
