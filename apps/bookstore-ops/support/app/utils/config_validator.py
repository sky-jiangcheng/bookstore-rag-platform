"""配置验证器模块

负责验证配置文件的完整性和一致性，检测配置冲突和问题

Author: System
Date: 2026-01-31
"""
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigValidator:
    """配置验证器"""

    def __init__(self, config_dir=None):
        if config_dir is None:
            # 默认为backend/config目录
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)

        self.config_file = self.config_dir / "config.yml"

    def validate_config(self):
        """验证配置文件的完整性和一致性

        Returns:
            bool: 配置是否有效
        """
        if not self.config_file.exists():
            logger.error(f"配置文件不存在: {self.config_file}")
            return False

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"读取配置文件失败: {str(e)}")
            return False

        # 验证所有环境的配置
        environments = ["development", "testing", "production"]
        all_valid = True

        for env in environments:
            if env not in config:
                logger.warning(f"环境配置不存在: {env}")
                continue

            env_config = config[env]
            if not self._validate_environment_config(env, env_config):
                all_valid = False

        return all_valid

    def _validate_environment_config(self, env, env_config):
        """验证单个环境的配置

        Args:
            env: 环境名称
            env_config: 环境配置

        Returns:
            bool: 配置是否有效
        """
        logger.info(f"验证 {env} 环境配置...")

        # 验证模块配置
        if "modules" not in env_config:
            logger.error(f"{env} 环境缺少 modules 配置")
            return False

        modules_config = env_config["modules"]
        valid = True

        # 验证必要的模块配置
        required_modules = ["database", "llm", "rag", "vector", "admin", "api", "jwt"]
        for module in required_modules:
            if module not in modules_config:
                logger.error(f"{env} 环境缺少 {module} 配置")
                valid = False

        # 验证向量服务配置
        if "vector" in modules_config:
            if not self._validate_vector_config(env, modules_config["vector"]):
                valid = False

        # 验证RAG服务配置
        if "rag" in modules_config:
            if not self._validate_rag_config(env, modules_config["rag"]):
                valid = False

        # 验证RAG配置与向量服务配置的一致性
        if "rag" in modules_config and "vector" in modules_config:
            if not self._validate_rag_vector_consistency(env, modules_config["rag"], modules_config["vector"]):
                valid = False

        # 验证数据库配置
        if "database" in modules_config:
            if not self._validate_database_config(env, modules_config["database"]):
                valid = False

        # 验证LLM服务配置
        if "llm" in modules_config:
            if not self._validate_llm_config(env, modules_config["llm"]):
                valid = False

        return valid

    def _validate_vector_config(self, env, vector_config):
        """验证向量服务配置

        Args:
            env: 环境名称
            vector_config: 向量服务配置

        Returns:
            bool: 配置是否有效
        """
        valid = True

        # 验证必要的配置项
        if "default_provider" not in vector_config:
            logger.warning(f"{env} 环境缺少 vector.default_provider 配置")

        if "default_dimension" not in vector_config:
            logger.warning(f"{env} 环境缺少 vector.default_dimension 配置")

        if "providers" not in vector_config:
            logger.error(f"{env} 环境缺少 vector.providers 配置")
            valid = False
        else:
            providers = vector_config["providers"]
            # 验证至少有一个本地提供商
            if "local" not in providers:
                logger.warning(f"{env} 环境缺少 vector.providers.local 配置，建议添加作为回退方案")

        return valid

    def _validate_rag_config(self, env, rag_config):
        """验证RAG服务配置

        Args:
            env: 环境名称
            rag_config: RAG服务配置

        Returns:
            bool: 配置是否有效
        """
        valid = True

        # 验证必要的配置项
        if "vector_db" not in rag_config:
            logger.error(f"{env} 环境缺少 rag.vector_db 配置")
            valid = False

        if "embedding" not in rag_config:
            logger.error(f"{env} 环境缺少 rag.embedding 配置")
            valid = False

        return valid

    def _validate_rag_vector_consistency(self, env, rag_config, vector_config):
        """验证RAG配置与向量服务配置的一致性

        Args:
            env: 环境名称
            rag_config: RAG服务配置
            vector_config: 向量服务配置

        Returns:
            bool: 配置是否一致
        """
        valid = True

        # 验证向量维度一致性
        if "embedding" in rag_config:
            rag_dimensions = rag_config["embedding"].get("dimensions")
            vector_dimension = vector_config.get("default_dimension")
            vector_dimension_alt = vector_config.get("dimension")

            # 使用实际使用的向量维度
            actual_vector_dimension = vector_dimension or vector_dimension_alt

            if rag_dimensions and actual_vector_dimension:
                if rag_dimensions != actual_vector_dimension:
                    logger.error(f"{env} 环境中 RAG 配置的向量维度 ({rag_dimensions}) 与向量服务配置的维度 ({actual_vector_dimension}) 不一致")
                    valid = False

        # 验证模型一致性
        if "embedding" in rag_config:
            rag_model = rag_config["embedding"].get("model")
            default_provider = vector_config.get("default_provider")
            providers = vector_config.get("providers", {})

            if rag_model and default_provider:
                provider_config = providers.get(default_provider, {})
                vector_model = provider_config.get("model")

                if vector_model and rag_model != vector_model:
                    logger.warning(f"{env} 环境中 RAG 配置的模型 ({rag_model}) 与向量服务配置的模型 ({vector_model}) 不一致")

        return valid

    def _validate_database_config(self, env, database_config):
        """验证数据库配置

        Args:
            env: 环境名称
            database_config: 数据库配置

        Returns:
            bool: 配置是否有效
        """
        valid = True

        if "type" not in database_config:
            logger.error(f"{env} 环境缺少 database.type 配置")
            valid = False

        db_type = database_config.get("type")
        if db_type == "mysql":
            required_fields = ["host", "port", "database", "user"]
            for field in required_fields:
                if field not in database_config.get("mysql", {}):
                    logger.error(f"{env} 环境缺少 database.mysql.{field} 配置")
                    valid = False

        elif db_type == "sqlite":
            if "url" not in database_config.get("sqlite", {}):
                logger.error(f"{env} 环境缺少 database.sqlite.url 配置")
                valid = False

        return valid

    def _validate_llm_config(self, env, llm_config):
        """验证LLM服务配置

        Args:
            env: 环境名称
            llm_config: LLM服务配置

        Returns:
            bool: 配置是否有效
        """
        valid = True

        if "default_service" not in llm_config:
            logger.warning(f"{env} 环境缺少 llm.default_service 配置")

        if "service_priority" not in llm_config:
            logger.warning(f"{env} 环境缺少 llm.service_priority 配置")

        return valid

    def check_config_consistency(self):
        """检查所有环境配置的一致性

        Returns:
            bool: 配置是否一致
        """
        logger.info("检查配置一致性...")

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"读取配置文件失败: {str(e)}")
            return False

        environments = ["development", "testing", "production"]
        present_envs = [env for env in environments if env in config]

        if len(present_envs) < 2:
            logger.warning("环境配置不足，无法进行一致性检查")
            return True

        # 检查配置结构一致性
        base_env = present_envs[0]
        base_config = config[base_env]

        for env in present_envs[1:]:
            current_config = config[env]
            if not self._check_config_structure(base_config, current_config, f"{base_env} vs {env}"):
                return False

        logger.info("配置一致性检查通过")
        return True

    def _check_config_structure(self, base_config, current_config, context):
        """检查两个配置结构的一致性

        Args:
            base_config: 基础配置
            current_config: 当前配置
            context: 上下文信息

        Returns:
            bool: 配置结构是否一致
        """
        if isinstance(base_config, dict) and isinstance(current_config, dict):
            base_keys = set(base_config.keys())
            current_keys = set(current_config.keys())

            missing_keys = base_keys - current_keys
            if missing_keys:
                logger.warning(f"{context} 缺少配置键: {missing_keys}")

            extra_keys = current_keys - base_keys
            if extra_keys:
                logger.warning(f"{context} 存在额外配置键: {extra_keys}")

            # 递归检查嵌套结构
            for key in base_keys & current_keys:
                if not self._check_config_structure(base_config[key], current_config[key], f"{context}.{key}"):
                    return False

        return True


# 创建全局配置验证器实例
config_validator = ConfigValidator()
