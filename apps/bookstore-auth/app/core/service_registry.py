"""
服务注册模块
"""
import logging

from app.core.dependency_injection import service_container
from app.utils.config_loader import config_loader

logger = logging.getLogger(__name__)


def register_services():
    """
    注册所有服务
    """
    logger.info("Starting service registration")

    # 注册配置加载器
    service_container.register_singleton("config_loader", lambda: config_loader)

    # 注册LLM服务
    register_llm_services()

    # 注册RAG服务
    register_rag_services()

    # 注册向量服务
    register_vector_services()

    # 注册其他服务
    register_other_services()

    logger.info("Service registration completed")


def register_llm_services():
    """
    注册LLM相关服务
    """
    from app.services.llm_service import (GeminiProvider, LLMService,
                                          LocalLLMProvider, MockLLMProvider,
                                          OpenAIProvider)

    # 注册LLM服务
    service_container.register_singleton("llm_service", LLMService)

    # 注册各种LLM提供商
    service_container.register(
        "openai_provider", OpenAIProvider, config=config_loader.get_openai_config()
    )
    service_container.register(
        "gemini_provider", GeminiProvider, config=config_loader.get_gemini_config()
    )
    service_container.register(
        "local_llm_provider",
        LocalLLMProvider,
        config=config_loader.get_local_llm_config(),
    )
    service_container.register("mock_llm_provider", MockLLMProvider, config={})

    logger.info("LLM services registered")


def register_rag_services():
    """
    注册RAG相关服务
    """
    from app.services.gemini_service import GeminiService
    from app.services.rag_service import RAGService

    # 注册Gemini服务
    service_container.register_singleton("gemini_service", GeminiService)

    # 注册RAG服务，通过依赖注入获取其他服务
    service_container.register_singleton(
        "rag_service",
        RAGService,
        vector_db="@vector_db",
        gemini_service="@gemini_service",
        llm_service="@llm_service",
    )

    logger.info("RAG services registered with dependencies")


def register_vector_services():
    """
    注册向量相关服务
    """
    from app.services.vector_db_service import vector_db
    from app.services.vector_service import VectorService

    # 注册向量服务
    service_container.register_singleton("vector_service", VectorService)

    # 注册向量数据库服务
    service_container.register_singleton("vector_db", lambda: vector_db)

    logger.info("Vector services registered")


def register_other_services():
    """
    注册其他服务
    """
    from app.services.auth_service import AuthService
    from app.services.log_service import LogService
    from app.services.permission_service import PermissionService

    # 注册认证服务
    service_container.register_singleton("auth_service", AuthService)

    # 注册日志服务
    service_container.register_singleton("log_service", LogService)

    # 注册权限服务
    service_container.register_singleton("permission_service", PermissionService)

    logger.info("Other services registered")


def get_service(service_id: str):
    """
    获取服务实例

    Args:
        service_id: 服务ID

    Returns:
        服务实例
    """
    return service_container.resolve(service_id)
