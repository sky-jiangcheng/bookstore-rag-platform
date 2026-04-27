"""配置加载器模块

负责加载和管理应用的配置文件，支持不同环境的配置

Author: System
Date: 2026-01-31
"""
import logging
# 加载.env文件
# 尝试从项目根目录加载.env文件
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# 获取项目根目录（backend目录的父目录）
project_root = Path(__file__).parent.parent.parent

# 构建.env文件路径
env_file = project_root / ".env"

# 加载.env文件
load_dotenv(dotenv_path=env_file)

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_dir=None):
        self._default_config_dir = Path(__file__).parent.parent.parent / "config"
        if config_dir is None:
            # 默认为backend/config目录
            self.config_dir = self._default_config_dir
        else:
            self.config_dir = Path(config_dir)

        # 环境变量，默认为development
        self.env = os.getenv("APP_ENV", "development")

        # 验证配置
        self._validate_config()

    def _resolve_env_vars(self, value):
        """解析字符串中的环境变量引用

        Args:
            value: 可能包含环境变量引用的字符串

        Returns:
            str: 解析后的字符串
        """
        import re

        if not isinstance(value, str):
            return value

        # 匹配 ${ENV_VAR} 格式的环境变量引用
        pattern = r"\$\{([^}]+)\}"

        def replace_env_var(match):
            env_var = match.group(1)
            return os.getenv(env_var, "")

        return re.sub(pattern, replace_env_var, value)

    def _resolve_config_env_vars(self, config):
        """递归解析配置中的环境变量引用

        Args:
            config: 配置对象

        Returns:
            dict: 解析后的配置对象
        """
        if isinstance(config, dict):
            return {k: self._resolve_config_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_config_env_vars(item) for item in config]
        elif isinstance(config, str):
            return self._resolve_env_vars(config)
        else:
            return config

    def _get_api_key(self, provider):
        """从环境变量获取API密钥

        Args:
            provider: 服务提供商名称

        Returns:
            str: API密钥
        """
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "aliyun": "ALIYUN_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "ernie": "ERNIE_API_KEY",
            "zhipu": "ZHIPU_API_KEY",
            "qwen": "QWEN_API_KEY",
        }

        if provider in env_vars and self._use_env_overrides():
            return os.getenv(env_vars[provider], "")
        return ""

    def _use_env_overrides(self):
        """判断是否允许使用环境变量覆盖配置"""
        try:
            return self.config_dir.resolve() == self._default_config_dir.resolve()
        except Exception:
            return False

    def _validate_config(self):
        """验证配置文件的完整性和一致性"""
        try:
            from app.utils.config_validator import config_validator

            logger.info(f"正在验证 {self.env} 环境配置...")

            # 验证配置完整性
            if not config_validator.validate_config():
                logger.warning("配置验证发现问题，请检查配置文件")

            # 验证配置一致性
            if not config_validator.check_config_consistency():
                logger.warning("配置一致性检查发现问题，请检查配置文件")

            logger.info("配置验证完成")
        except ImportError as e:
            logger.warning(f"配置验证模块导入失败: {str(e)}")
        except Exception as e:
            logger.warning(f"配置验证失败: {str(e)}")

    def load_config(self):
        """加载配置文件"""
        config_file = self.config_dir / "config.yml"

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 获取当前环境的配置
        env_config = config.get(self.env)
        if not env_config:
            raise ValueError(f"环境配置不存在: {self.env}")

        # 解析配置中的环境变量引用
        env_config = self._resolve_config_env_vars(env_config)

        return env_config

    def get_modules_config(self):
        """获取模块配置"""
        env_config = self.load_config()
        return env_config.get("modules", {})

    def load_database_config(self):
        """加载数据库配置"""
        modules_config = self.get_modules_config()
        config = modules_config.get("database", {})

        # 数据库连接串优先级最高，便于接入 Neon / Supabase / PlanetScale 等免费数据库
        database_url = os.getenv("DATABASE_URL", "")
        if database_url:
            config["database_url"] = database_url

        # 从环境变量覆盖数据库配置
        if config.get("type") == "mysql" and self._use_env_overrides():
            mysql_config = config.get("mysql", {})
            # 从环境变量获取数据库配置
            mysql_config["host"] = os.getenv(
                "DB_HOST", mysql_config.get("host", "localhost")
            )
            mysql_config["port"] = int(
                os.getenv("DB_PORT", mysql_config.get("port", 3306))
            )
            mysql_config["user"] = os.getenv(
                "DB_USER", mysql_config.get("user", "root")
            )
            mysql_config["password"] = os.getenv(
                "DB_PASSWORD", mysql_config.get("password", "")
            )
            mysql_config["database"] = os.getenv(
                "DB_NAME", mysql_config.get("database", "bookstore")
            )

        return config

    def get_database_url(self):
        """获取数据库连接URL"""
        config = self.load_database_config()

        database_url = config.get("database_url")
        if database_url:
            return database_url

        db_type = config.get("type", "sqlite")

        if db_type == "sqlite":
            return config["sqlite"]["url"]
        elif db_type == "mysql":
            mysql_config = config["mysql"]
            user = mysql_config["user"]
            password = mysql_config["password"]
            host = mysql_config["host"]
            port = mysql_config["port"]
            database = mysql_config["database"]
            charset = mysql_config["charset"]

            if password:
                return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"
            else:
                return (
                    f"mysql+pymysql://{user}@{host}:{port}/{database}?charset={charset}"
                )
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")

    def get_llm_config(self):
        """获取LLM服务配置"""
        modules_config = self.get_modules_config()
        return modules_config.get("llm", {})

    def get_rag_config(self):
        """获取RAG服务配置"""
        modules_config = self.get_modules_config()
        config = modules_config.get("rag", {})

        # 从环境变量覆盖向量数据库配置
        if "vector_db" in config and self._use_env_overrides():
            qdrant_host = os.getenv("QDRANT_HOST", "")
            qdrant_port = os.getenv("QDRANT_PORT", "")
            qdrant_url = os.getenv("QDRANT_URL", "")
            qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
            if qdrant_host:
                config["vector_db"]["host"] = qdrant_host
            if qdrant_port:
                config["vector_db"]["port"] = int(qdrant_port)
            if qdrant_url:
                config["vector_db"]["url"] = qdrant_url
            if qdrant_api_key:
                config["vector_db"]["api_key"] = qdrant_api_key

        return config

    def get_vector_config(self):
        """获取向量服务配置"""
        modules_config = self.get_modules_config()
        vector_config = modules_config.get("vector", {})

        # 从环境变量覆盖API密钥
        if "providers" in vector_config and self._use_env_overrides():
            providers = vector_config["providers"]
            for provider, config in providers.items():
                api_key = self._get_api_key(provider)
                if api_key:
                    config["api_key"] = api_key

        return vector_config

    def get_openai_config(self):
        """获取OpenAI API配置"""
        llm_config = self.get_llm_config()
        providers = llm_config.get("providers", {})
        config = providers.get("openai", {})

        # 从环境变量覆盖API密钥
        api_key = self._get_api_key("openai")
        if api_key:
            config["api_key"] = api_key

        return config

    def get_gemini_config(self):
        """获取Gemini API配置"""
        llm_config = self.get_llm_config()
        providers = llm_config.get("providers", {})
        config = providers.get("gemini", {})

        # 从环境变量覆盖API密钥
        api_key = self._get_api_key("gemini")
        if api_key:
            config["api_key"] = api_key

        return config

    def get_qwen_config(self):
        """获取通义千问API配置"""
        llm_config = self.get_llm_config()
        providers = llm_config.get("providers", {})
        config = providers.get("qwen", {})

        # 从环境变量覆盖API密钥
        api_key = self._get_api_key("qwen")
        if api_key:
            config["api_key"] = api_key

        return config

    def get_ernie_config(self):
        """获取文心一言API配置"""
        llm_config = self.get_llm_config()
        providers = llm_config.get("providers", {})
        config = providers.get("ernie", {})

        # 从环境变量覆盖API密钥
        api_key = self._get_api_key("ernie")
        if api_key:
            config["api_key"] = api_key

        # 从环境变量获取Secret Key
        secret_key = os.getenv("ERNIE_SECRET_KEY", "")
        if secret_key:
            config["secret_key"] = secret_key

        return config

    def get_zhipu_config(self):
        """获取智谱GLM API配置"""
        llm_config = self.get_llm_config()
        providers = llm_config.get("providers", {})
        config = providers.get("zhipu", {})

        # 从环境变量覆盖API密钥
        api_key = self._get_api_key("zhipu")
        if api_key:
            config["api_key"] = api_key

        return config

    def get_local_llm_config(self):
        """获取本地LLM配置"""
        llm_config = self.get_llm_config()
        providers = llm_config.get("providers", {})
        return providers.get("local", {})

    def get_default_ai_service(self):
        """获取默认AI服务"""
        llm_config = self.get_llm_config()
        return llm_config.get("default_service", "mock")

    def get_service_priority(self):
        """获取服务优先级"""
        llm_config = self.get_llm_config()
        return llm_config.get("service_priority", ["mock"])

    def get_module_config(self, module_name):
        """获取指定模块的配置"""
        modules_config = self.get_modules_config()
        return modules_config.get(module_name, {})

    def get_admin_config(self):
        """获取默认管理员账户配置"""
        modules_config = self.get_modules_config()
        return modules_config.get(
            "admin",
            {
                "username": "admin",
                "password": "",
                "email": "admin@example.com",
                "name": "超级管理员",
            },
        )

    def get_api_config(self):
        """获取API服务配置"""
        modules_config = self.get_modules_config()
        config = modules_config.get(
            "api",
            {
                "host": "0.0.0.0",
                "port": 8000,
                "cors_origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
            },
        )

        # 从环境变量覆盖CORS origins
        if self._use_env_overrides():
            cors_origins_env = os.getenv("CORS_ORIGINS", "")
            if cors_origins_env:
                cors_origins = [
                    origin.strip()
                    for origin in cors_origins_env.split(",")
                    if origin.strip()
                ]
                if cors_origins:
                    config["cors_origins"] = cors_origins
            elif self.env == "free_cloud":
                raise ValueError("CORS_ORIGINS is required when APP_ENV=free_cloud")

        return config

    def get_jwt_config(self):
        """获取JWT认证配置"""
        modules_config = self.get_modules_config()
        config = modules_config.get(
            "jwt",
            {
                "secret_key": "your-secret-key-here-change-in-production",
                "algorithm": "HS256",
                "access_token_expire_minutes": 30,
            },
        )

        # 从环境变量覆盖JWT密钥
        if self._use_env_overrides():
            secret_key = os.getenv("JWT_SECRET_KEY", "")
            if secret_key:
                config["secret_key"] = secret_key

        return config

    def get_cache_config(self):
        """获取缓存配置"""
        modules_config = self.get_modules_config()
        config = modules_config.get(
            "cache", {"ttl": 900, "url": "redis://localhost:6379/0"}
        )

        # 从环境变量覆盖缓存URL
        if self._use_env_overrides():
            redis_url = os.getenv("REDIS_URL", "") or os.getenv("UPSTASH_REDIS_URL", "")
            if redis_url:
                config["url"] = redis_url

        return config

    def get_upload_config(self):
        """获取上传配置"""
        modules_config = self.get_modules_config()
        return modules_config.get("upload", {"max_size": 10485760})  # 10MB

    def get_word2vec_config(self):
        """获取Word2Vec模型配置"""
        modules_config = self.get_modules_config()
        return modules_config.get("word2vec", {"model_path": "models/word2vec.model"})

    def get_vector_dimension(self):
        """获取向量维度配置"""
        modules_config = self.get_modules_config()
        vector_config = modules_config.get("vector", {})
        return vector_config.get("dimension", 100)

    def get_similarity_threshold(self):
        """获取相似度阈值配置"""
        modules_config = self.get_modules_config()
        vector_config = modules_config.get("vector", {})
        return vector_config.get("similarity_threshold", 0.8)


# 创建全局配置加载器实例
config_loader = ConfigLoader()
