"""
书单推荐 - 辅助路由

包含会话管理、历史查询、分享等辅助功能
"""

import logging
import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.api.v1.book_list.schemas import (BookListHistoryResponse,
                                          CognitiveLevel,
                                          CognitiveLevelsResponse, SessionInfo,
                                          ShareBookListRequest,
                                          ShareBookListResponse,
                                          ValidatePromptRequest,
                                          ValidatePromptResponse)
from app.api.v1.book_list.services import validate_prompt
from app.models import BookListSession, CustomBookList
from app.models.auth import User
from app.utils.database import get_db

router = APIRouter(prefix="/api/v1/book-list", tags=["book-list"])
logger = logging.getLogger(__name__)


@router.get(
    "/session/{request_id}",
    response_model=SessionInfo,
    summary="获取会话信息",
    description="查询特定会话的详细信息",
)
async def get_session_info(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取会话信息"""
    session = (
        db.query(BookListSession)
        .filter(
            BookListSession.request_id == request_id,
            BookListSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return SessionInfo(
        request_id=session.request_id,
        session_id=session.id,
        status=session.status,
        original_input=session.original_input,
        parsed_requirements=session.parsed_requirements,
        refinement_count=session.refinement_count,
        confirmation_count=session.confirmation_count,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@router.get(
    "/cognitive-levels",
    response_model=CognitiveLevelsResponse,
    summary="获取认知水平列表",
    description="返回所有支持的认知水平选项",
)
async def get_cognitive_levels(
    current_user: User = Depends(get_current_active_user),
):
    """获取支持的认知水平列表"""
    cognitive_levels = [
        CognitiveLevel(value="儿童", label="儿童", level=1),
        CognitiveLevel(value="小学生", label="小学生", level=2),
        CognitiveLevel(value="中学生", label="中学生", level=3),
        CognitiveLevel(value="高中生", label="高中生", level=4),
        CognitiveLevel(value="大学生", label="大学生", level=5),
        CognitiveLevel(value="研究生", label="研究生", level=6),
        CognitiveLevel(value="专业人士", label="专业人士", level=7),
        CognitiveLevel(value="通用", label="通用（中等水平）", level=3),
    ]

    return CognitiveLevelsResponse(cognitive_levels=cognitive_levels)


@router.post(
    "/validate-prompt",
    response_model=ValidatePromptResponse,
    summary="验证提示词",
    description="检查提示词是否包含所有必要维度",
)
async def validate_prompt_endpoint(
    request: ValidatePromptRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    验证提示词是否包含所有必要的维度
    """
    try:
        logger.info(
            "开始验证提示词", user_id=current_user.id, prompt_length=len(request.prompt)
        )

        result = validate_prompt(request.prompt)

        logger.info(
            "提示词验证完成",
            user_id=current_user.id,
            valid=result["valid"],
            error_count=len(result["errors"]),
        )

        return ValidatePromptResponse(**result)

    except Exception as e:
        logger.error(f"提示词验证失败: {str(e)}", user_id=current_user.id, exc_info=True)
        raise HTTPException(status_code=500, detail=f"系统错误: {str(e)}")


@router.get(
    "/history",
    response_model=BookListHistoryResponse,
    summary="获取历史书单",
    description="分页查询用户的历史书单记录",
)
async def get_user_book_lists(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取用户历史书单
    """
    query = db.query(CustomBookList).filter(CustomBookList.user_id == current_user.id)

    total = query.count()
    book_lists = (
        query.order_by(CustomBookList.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return BookListHistoryResponse(
        items=[
            {
                "id": bl.id,
                "request_text": bl.request_text,
                "parsed_requirements": bl.parsed_requirements,
                "book_count": len(bl.book_list) if bl.book_list else 0,
                "status": bl.status,
                "created_at": bl.created_at.isoformat(),
            }
            for bl in book_lists
        ],
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit,
    )


@router.post(
    "/share",
    response_model=ShareBookListResponse,
    summary="分享书单",
    description="生成书单分享链接",
)
async def share_book_list(
    request: ShareBookListRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    分享书单

    生成一个可分享的链接
    """
    try:
        # 生成分享令牌
        token = str(uuid.uuid4())

        # 假设前端路由为 /share/{token}
        share_url = f"http://localhost:5173/share/{token}"

        logger.info(
            "生成书单分享链接",
            user_id=current_user.id,
            session_id=request.session_id,
            book_list_id=request.book_list_id,
            token=token,
        )

        return ShareBookListResponse(
            share_url=share_url, share_token=token, expiration=None
        )
    except Exception as e:
        logger.error(f"分享书单失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分享失败: {str(e)}")
