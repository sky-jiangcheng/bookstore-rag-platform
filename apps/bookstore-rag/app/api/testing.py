"""
测试API接口
用于测试各个模块的功能，支持模块独立调用和测试

安全警告：这些端点仅用于开发和测试环境，生产环境应禁用或添加严格认证
"""
import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Header

from app.core.service_registry import get_service
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.vector_service import VectorService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/testing", tags=["测试"])


def check_testing_enabled():
    """检查测试端点是否启用"""
    app_env = os.getenv("APP_ENV", "development").lower()
    if app_env in ("production", "prod", "staging"):
        raise HTTPException(
            status_code=404,
            detail="Testing endpoints are disabled in production"
        )
    return True


async def get_current_user_for_testing(authorization: str = Header(None)):
    """获取当前用户用于测试端点认证"""
    check_testing_enabled()
    
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required for testing endpoints"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )
    
    token = authorization[7:]
    user = AuthService.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is disabled"
        )
    
    return user


@router.get("/llm/providers", dependencies=[Depends(get_current_user_for_testing)])
async def get_llm_providers():
    """
    获取可用的LLM提供商列表
    需要认证
    """
    try:
        llm_service = get_service("llm_service")
        providers = llm_service.get_available_providers()
        return {"providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/chat", dependencies=[Depends(get_current_user_for_testing)])
async def llm_chat(messages: List[Dict[str, str]], provider: str = "mock", **kwargs):
    """
    测试LLM聊天完成功能
    需要认证

    Args:
        messages: 聊天消息列表
        provider: LLM提供商
        **kwargs: 其他参数
    """
    try:
        llm_service = get_service("llm_service")
        # 切换到指定的提供商
        llm_service.switch_provider(provider)
        # 执行聊天完成
        response = llm_service.chat_completion(messages, **kwargs)
        return {"response": response, "provider": provider}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/parse", dependencies=[Depends(get_current_user_for_testing)])
async def llm_parse(user_input: str):
    """
    测试LLM解析用户请求功能
    需要认证

    Args:
        user_input: 用户输入的需求
    """
    try:
        llm_service = get_service("llm_service")
        result = llm_service.parse_user_request(user_input)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/classify", dependencies=[Depends(get_current_user_for_testing)])
async def llm_classify(book_info: Dict[str, Any]):
    """
    测试LLM分类书籍功能
    需要认证

    Args:
        book_info: 书籍信息
    """
    try:
        llm_service = get_service("llm_service")
        categories = llm_service.classify_book_categories(book_info)
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/analyze", dependencies=[Depends(get_current_user_for_testing)])
async def llm_analyze(book_info: Dict[str, Any]):
    """
    测试LLM分析书籍阅读水平功能
    需要认证

    Args:
        book_info: 书籍信息
    """
    try:
        llm_service = get_service("llm_service")
        analysis = llm_service.analyze_reading_level(book_info)
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/describe", dependencies=[Depends(get_current_user_for_testing)])
async def llm_describe(book_info: Dict[str, Any]):
    """
    测试LLM生成书籍语义描述功能
    需要认证

    Args:
        book_info: 书籍信息
    """
    try:
        llm_service = get_service("llm_service")
        description = llm_service.generate_book_description(book_info)
        return {"description": description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector/model", dependencies=[Depends(get_current_user_for_testing)])
async def get_vector_model_info():
    """
    获取向量模型信息
    需要认证
    """
    try:
        vector_service = get_service("vector_service")
        model_info = vector_service.get_model_info()
        return model_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vector/get", dependencies=[Depends(get_current_user_for_testing)])
async def get_vector(text: str, summary: str = None):
    """
    测试获取文本向量功能
    需要认证

    Args:
        text: 文本内容
        summary: 文本摘要（可选）
    """
    try:
        vector_service = get_service("vector_service")
        vector = vector_service.get_vector(text, summary)
        return {"vector": vector.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services", dependencies=[Depends(get_current_user_for_testing)])
async def get_available_services():
    """
    获取可用的服务列表
    需要认证
    """
    try:
        from app.core.dependency_injection import service_container

        services = list(service_container.services.keys())
        return {"services": services}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
