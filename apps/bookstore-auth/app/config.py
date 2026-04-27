"""配置模块

管理应用的所有配置信息，包括数据库、向量数据库、Redis、AI模型、缓存、JWT和上传配置
配置以 config.yml 为主，并允许环境变量覆盖敏感项，便于本地和部署环境切换。

Author: System
Date: 2026-01-31
"""
from sqlalchemy.orm import sessionmaker

# 数据库配置 - engine 和 Base 从 database.py 导入避免重复定义
from app.utils.config_loader import config_loader
from app.utils.database import engine

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 向量数据库配置 - 统一从config.yml读取
vector_config = config_loader.get_vector_config()
VECTOR_DB_URL = vector_config.get("url", "lancedb://./.lancedb")
VECTOR_DIMENSION = int(
    vector_config.get("dimension", 100)
)  # 默认100维（OpenAI text-embedding-ada-002）

# Qdrant向量数据库配置
rag_config_data = config_loader.get_rag_config()
vector_db_config = rag_config_data.get("vector_db", {})
QDRANT_HOST = vector_db_config.get("host", "localhost")
QDRANT_PORT = int(vector_db_config.get("port", 6333))

# Redis配置
cache_config = config_loader.get_cache_config()
REDIS_URL = cache_config.get("url", "redis://localhost:6379/0")

# 管理员配置
admin_config = config_loader.get_admin_config()
ADMIN_USERNAME = admin_config.get("username", "admin")
ADMIN_PASSWORD = admin_config.get("password", "")
ADMIN_EMAIL = admin_config.get("email", "admin@example.com")
ADMIN_NAME = admin_config.get("name", "超级管理员")

# API服务配置
api_config = config_loader.get_api_config()
API_HOST = api_config.get("host", "0.0.0.0")
API_PORT = api_config.get("port", 8000)
CORS_ORIGINS = api_config.get("cors_origins", ["http://localhost:5173"])

# 向量维度和相似度配置
vector_config_full = config_loader.get_module_config("vector")
SIMILARITY_THRESHOLD = float(vector_config_full.get("similarity_threshold", 0.8))

# 缓存配置
CACHE_TTL = int(cache_config.get("ttl", 900))

# JWT配置
jwt_config = config_loader.get_jwt_config()
SECRET_KEY = jwt_config.get("secret_key", "")
ALGORITHM = jwt_config.get("algorithm", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(jwt_config.get("access_token_expire_minutes", 30))

# 上传配置
upload_config = config_loader.get_upload_config()
MAX_UPLOAD_SIZE = int(upload_config.get("max_size", 10 * 1024 * 1024))
