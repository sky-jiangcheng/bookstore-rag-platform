"""配置模块

管理应用的所有配置信息，包括数据库、向量数据库、Redis、AI模型、缓存、JWT和上传配置
配置以 config.yml 为主，并允许环境变量覆盖敏感项，便于本地和部署环境切换。

Author: System
Date: 2026-01-31
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 数据库配置
from app.utils.config_loader import config_loader

DATABASE_URL = config_loader.get_database_url()

# 向量数据库配置 - 统一从config.yml读取
vector_config = config_loader.get_vector_config()
VECTOR_DB_URL = vector_config.get("url", "lancedb://./.lancedb")
VECTOR_DIMENSION = int(vector_config.get("dimension", 1536))  # 使用1536维（Gemini embeddings）

# Qdrant向量数据库配置
rag_config_data = config_loader.get_rag_config()
vector_db_config = rag_config_data.get("vector_db", {})
QDRANT_HOST = vector_db_config.get("host", "localhost")
QDRANT_PORT = int(vector_db_config.get("port", 6333))

# Redis配置
cache_config = config_loader.get_cache_config()
REDIS_URL = cache_config.get("url", "redis://localhost:6379/0")

def _create_engine(database_url: str):
    """根据数据库类型创建引擎。"""
    engine_kwargs = {}

    if database_url.startswith("sqlite:"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 3600

    return create_engine(database_url, **engine_kwargs)


# 创建数据库引擎和会话
engine = _create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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

# 安全检查：SECRET_KEY 不能为空
import os
import sys

# 允许通过环境变量覆盖配置文件中的 SECRET_KEY
SECRET_KEY = os.environ.get("SECRET_KEY", SECRET_KEY)

if not SECRET_KEY:
    # 在生产环境中必须设置 SECRET_KEY
    env = os.environ.get("ENVIRONMENT", "development")
    if env.lower() in ("production", "prod", "staging"):
        print("ERROR: SECRET_KEY must be set in production environment!", file=sys.stderr)
        print("Set it via config.yml (jwt.secret_key) or environment variable SECRET_KEY", file=sys.stderr)
        sys.exit(1)
    else:
        # 开发环境使用默认密钥（不安全，仅用于开发）
        SECRET_KEY = "dev-secret-key-change-in-production"
        print("WARNING: Using default SECRET_KEY for development. This is NOT secure for production!", file=sys.stderr)

# 上传配置
upload_config = config_loader.get_upload_config()
MAX_UPLOAD_SIZE = int(upload_config.get("max_size", 10 * 1024 * 1024))
