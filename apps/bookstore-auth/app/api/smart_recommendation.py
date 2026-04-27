import logging
from typing import Optional

from bookstore_shared.rag_backend import build_rag_backend
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.auth import User
from app.services.permission_service import require_permission
from app.utils.database import get_db

router = APIRouter(prefix="/smart", tags=["智能推荐"])

# 配置日志
logger = logging.getLogger(__name__)


def get_rag_service():
    """获取可复用的 RAG 后端实例。"""
    return build_rag_backend()


rag_service = get_rag_service()


# 请求模型
class SmartRecommendationRequest(BaseModel):
    user_input: str
    limit: int = 20


# 响应模型
class SmartRecommendationResponse:
    def __init__(
        self,
        parsed_requirements,
        recommendations,
        total_count,
        recommendation_reason,
        message,
    ):
        self.parsed_requirements = parsed_requirements
        self.recommendations = recommendations
        self.total_count = total_count
        self.recommendation_reason = recommendation_reason
        self.message = message


@router.post("/recommendation")
async def get_smart_recommendation(
    request: SmartRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_RECOMMENDATIONS")),
    authorization: Optional[str] = Header(default=None),
):
    """
    智能书单推荐

    用户输入需求，系统会进行智能拆解，然后推荐书库中已存在的书籍
    """
    try:
        user_input = request.user_input
        limit = request.limit

        logger.info(
            f"Received smart recommendation request: {user_input}, limit: {limit}"
        )

        # 验证参数
        if not user_input:
            logger.warning("Empty user input received")
            raise HTTPException(status_code=400, detail="用户输入不能为空")

        if limit <= 0 or limit > 50:
            logger.warning(f"Invalid limit: {limit}")
            limit = 20  # 设置默认值

        # 使用可复用的 RAG 后端获取推荐；若配置了 RAG_SERVICE_URL，则透明切到独立服务。
        result = rag_service.get_book_recommendations(
            user_input=user_input,
            db=db,
            limit=limit,
            authorization=authorization,
        )

        logger.info(
            f"Smart recommendation completed, returned {result.get('total_count', 0)} books"
        )

        # 构建响应
        response = {
            "parsed_requirements": result.get("parsed_requirements", {}),
            "recommendations": result.get("recommendations", []),
            "total_count": result.get("total_count", 0),
            "recommendation_reason": result.get("recommendation_reason", ""),
            "message": result.get("message", "Success"),
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in smart recommendation: {str(e)}")
        import traceback

        logger.error(f"Stacktrace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")


@router.post("/chat")
async def chat_with_book_recommender(
    request: SmartRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_RECOMMENDATIONS")),
    authorization: Optional[str] = Header(default=None),
):
    """
    智能推荐聊天接口

    模拟与大模型的对话，根据用户需求推荐书籍
    """
    try:
        user_input = request.user_input
        limit = request.limit

        logger.info(
            f"Received chat recommendation request: {user_input}, limit: {limit}"
        )

        # 验证参数
        if not user_input:
            logger.warning("Empty user input received")
            raise HTTPException(status_code=400, detail="用户输入不能为空")

        # 使用可复用的 RAG 后端获取推荐
        result = rag_service.get_book_recommendations(
            user_input=user_input,
            db=db,
            limit=limit,
            authorization=authorization,
        )

        # 生成聊天响应
        recommendations = result.get("recommendations", [])
        total_count = result.get("total_count", 0)

        # 构建聊天回复
        if total_count > 0:
            # 生成推荐理由
            parsed_requirements = result.get("parsed_requirements", {})
            keywords = parsed_requirements.get("keywords", [])
            categories = parsed_requirements.get("categories", [])

            # 构建回复内容
            reply = f"根据您的需求，我为您推荐了 {total_count} 本书籍。"

            if keywords:
                reply += f" 我识别到您对 {'、'.join(keywords[:3])} 等主题感兴趣。"

            if categories:
                reply += f" 这些书籍主要属于 {'、'.join(categories)} 类别。"

            reply += " 以下是具体的推荐书单："
        else:
            reply = "抱歉，根据您的需求，我没有找到合适的书籍推荐。请尝试调整您的需求描述。"

        # 构建响应
        response = {
            "user_input": user_input,
            "reply": reply,
            "recommendations": recommendations,
            "total_count": total_count,
            "recommendation_reason": result.get("recommendation_reason", ""),
            "parsed_requirements": result.get("parsed_requirements", {}),
        }

        logger.info(f"Chat recommendation completed, returned {total_count} books")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")
