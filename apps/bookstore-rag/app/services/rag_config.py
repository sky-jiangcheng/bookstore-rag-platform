"""
RAG核心服务配置
"""
import logging
from typing import Any, Dict

from app.core.constants import EmbeddingModelDimensions, RAGConstants
from app.utils.config_loader import config_loader

logger = logging.getLogger(__name__)


class RAGConfig:
    """RAG配置管理类"""

    def _infer_model_dimension(self, model_name: str) -> int:
        """根据模型名称推断维度"""
        return EmbeddingModelDimensions.get_dimension(
            model_name, 
            default=RAGConstants.DEFAULT_EMBEDDING_DIMENSION
        )

    def __init__(self):
        self._config_cache = {}
        self._load_default_config()

    def _load_default_config(self):
        """
        加载默认配置

        配置优先级（从高到低）：
        1. 数据库中的 SystemConfig 表（运行时动态配置）
        2. config.yml 中的配置文件
        3. 代码中的默认值

        所有配置统一从config.yml读取，不再依赖环境变量。
        迁移时只需修改config.yml即可，无需设置环境变量。
        """
        # 从YAML配置文件中读取所有配置
        openai_config = config_loader.get_openai_config()
        rag_config_data = config_loader.get_rag_config()
        vector_config_data = config_loader.get_vector_config()

        # 嵌入模型配置 - 统一从config.yml读取
        embedding_config = rag_config_data.get("embedding", {})
        embedding_model_name = embedding_config.get("model", RAGConstants.DEFAULT_EMBEDDING_MODEL)

        self._config_cache = {
            "embedding_model": {
                "model_name": embedding_model_name,
                "dimension": vector_config_data.get(
                    "dimensions", 
                    self._infer_model_dimension(embedding_model_name)
                ),
                "max_length": embedding_config.get("max_length", RAGConstants.DEFAULT_EMBEDDING_MAX_LENGTH),
                "device": embedding_config.get("device", RAGConstants.DEFAULT_EMBEDDING_DEVICE),
            },
            "vector_db": {
                "host": rag_config_data.get("vector_db", {}).get("host", RAGConstants.DEFAULT_QDRANT_HOST),
                "port": rag_config_data.get("vector_db", {}).get("port", RAGConstants.DEFAULT_QDRANT_PORT),
                "collection": rag_config_data.get("vector_db", {}).get("collection", RAGConstants.DEFAULT_QDRANT_COLLECTION),
                "timeout": rag_config_data.get("vector_db", {}).get("timeout", RAGConstants.DEFAULT_QDRANT_TIMEOUT),
                "provider": vector_config_data.get("type", "qdrant"),
                "url": rag_config_data.get("vector_db", {}).get("url"),
                "api_key": rag_config_data.get("vector_db", {}).get("api_key"),
            },
            "llm_config": {
                "provider": config_loader.get_default_ai_service(),
                "model": openai_config.get("model", "gpt-3.5-turbo"),
                "temperature": openai_config.get("temperature", 0.7),
                "max_tokens": openai_config.get("max_tokens", 2000),
                "api_key": openai_config.get("api_key", ""),
                "base_url": openai_config.get("base_url", "https://api.openai.com/v1"),
            },
            "search_params": {
                "top_k": rag_config_data.get("search", {}).get("top_k", RAGConstants.DEFAULT_SEARCH_TOP_K),
                "score_threshold": rag_config_data.get("search", {}).get("score_threshold", RAGConstants.DEFAULT_SEARCH_SCORE_THRESHOLD),
                "rerank_top_k": rag_config_data.get("search", {}).get("rerank_top_k", RAGConstants.DEFAULT_SEARCH_RERANK_TOP_K),
                "max_candidates": rag_config_data.get("search", {}).get("max_candidates", RAGConstants.DEFAULT_SEARCH_MAX_CANDIDATES),
            },
            "cache_config": {
                "ttl_seconds": rag_config_data.get("cache", {}).get("ttl_seconds", RAGConstants.DEFAULT_CACHE_TTL_SECONDS),
                "max_size": rag_config_data.get("cache", {}).get("max_size", RAGConstants.DEFAULT_CACHE_MAX_SIZE),
                "enable_cache": rag_config_data.get("cache", {}).get("enable", RAGConstants.DEFAULT_CACHE_ENABLED),
            },
            "book_processing": {
                "batch_size": rag_config_data.get("processing", {}).get("batch_size", RAGConstants.DEFAULT_BATCH_SIZE),
                "max_description_length": rag_config_data.get("processing", {}).get("max_description_length", RAGConstants.DEFAULT_MAX_DESCRIPTION_LENGTH),
                "auto_generate_description": rag_config_data.get("processing", {}).get("auto_generate", RAGConstants.DEFAULT_AUTO_GENERATE_DESCRIPTION),
            },
        }

    @property
    def embedding_model(self) -> Dict[str, Any]:
        """嵌入模型配置"""
        return self._config_cache["embedding_model"]

    @property
    def vector_db(self) -> Dict[str, Any]:
        """向量数据库配置"""
        return self._config_cache["vector_db"]

    @property
    def llm_config(self) -> Dict[str, Any]:
        """LLM配置"""
        return self._config_cache["llm_config"]

    @property
    def search_params(self) -> Dict[str, Any]:
        """搜索参数配置"""
        return self._config_cache["search_params"]

    @property
    def cache_config(self) -> Dict[str, Any]:
        """缓存配置"""
        return self._config_cache["cache_config"]


# 全局配置实例
rag_config = RAGConfig()
