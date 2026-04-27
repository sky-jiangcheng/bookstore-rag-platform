"""
书单满意度反馈API
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.core.logging_config import get_logger
from app.models import BookListFeedback
from app.models.auth import User
from app.utils.database import get_db

router = APIRouter()
logger = get_logger(__name__)


# ==================== 请求/响应模型 ====================


class BookListFeedbackRequest(BaseModel):
    """提交满意度反馈请求"""

    booklist_id: str = Field(..., description="书单ID")
    booklist_name: str = Field(..., description="书单名称")
    overall_score: int = Field(..., ge=1, le=5, description="总体评分(1-5)")
    accuracy_score: int = Field(..., ge=1, le=5, description="推荐准确性(1-5)")
    price_score: int = Field(..., ge=1, le=5, description="价格合理性(1-5)")
    diversity_score: Optional[int] = Field(None, ge=1, le=5, description="书籍多样性(1-5)")
    suggestions: Optional[str] = Field(None, description="改进建议")
    selected_books: Optional[List[int]] = Field(None, description="选中的书籍ID列表")
    book_count: Optional[int] = Field(None, description="书籍数量")
    total_price: Optional[int] = Field(
        None, description="总价格", json_schema_extra={"comment": "总价格"}
    )
    average_score: Optional[int] = Field(
        None, description="平均匹配度", json_schema_extra={"comment": "平均匹配度"}
    )


class BookListFeedbackResponse(BaseModel):
    """满意度反馈响应"""

    id: int
    booklist_id: str
    booklist_name: str
    user_id: int
    overall_score: int
    accuracy_score: int
    price_score: int
    diversity_score: Optional[int]
    suggestions: Optional[str]
    selected_books: Optional[List[int]]
    book_count: Optional[int]
    total_price: Optional[int]
    average_score: Optional[int]
    created_at: str


class FeedbackStatistics(BaseModel):
    """反馈统计数据"""

    total_feedbacks: int
    average_overall_score: float
    average_accuracy_score: float
    average_price_score: float
    average_diversity_score: Optional[float]
    score_distribution: dict


# ==================== 满意度反馈接口 ====================


@router.post("/api/v1/booklist/feedback", response_model=BookListFeedbackResponse)
async def submit_feedback(
    request: BookListFeedbackRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    提交满意度反馈
    """
    try:
        feedback = BookListFeedback(
            booklist_id=request.booklist_id,
            booklist_name=request.booklist_name,
            user_id=current_user.id,
            overall_score=request.overall_score,
            accuracy_score=request.accuracy_score,
            price_score=request.price_score,
            diversity_score=request.diversity_score,
            suggestions=request.suggestions,
            selected_books=request.selected_books,
            book_count=request.book_count,
            total_price=request.total_price,
            average_score=request.average_score,
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        logger.info(
            "提交满意度反馈成功",
            feedback_id=feedback.id,
            user_id=current_user.id,
            booklist_id=request.booklist_id,
            overall_score=request.overall_score,
        )

        return BookListFeedbackResponse(**feedback.to_dict())

    except Exception as e:
        logger.error(f"提交满意度反馈失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"提交失败: {str(e)}")


@router.get("/api/v1/booklist/feedback/statistics", response_model=FeedbackStatistics)
async def get_feedback_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取满意度统计数据
    """
    try:
        feedbacks = db.query(BookListFeedback).all()

        if not feedbacks:
            return FeedbackStatistics(
                total_feedbacks=0,
                average_overall_score=0.0,
                average_accuracy_score=0.0,
                average_price_score=0.0,
                average_diversity_score=0.0,
                score_distribution={},
            )

        # 计算平均分
        total = len(feedbacks)
        avg_overall = sum(f.overall_score for f in feedbacks) / total
        avg_accuracy = sum(f.accuracy_score for f in feedbacks) / total
        avg_price = sum(f.price_score for f in feedbacks) / total
        diversity_scores = [f.diversity_score for f in feedbacks if f.diversity_score]
        avg_diversity = sum(diversity_scores) / len(diversity_scores) if diversity_scores else None

        # 评分分布
        score_distribution = {
            "overall": {i: sum(1 for f in feedbacks if f.overall_score == i) for i in range(1, 6)},
            "accuracy": {i: sum(1 for f in feedbacks if f.accuracy_score == i) for i in range(1, 6)},
            "price": {i: sum(1 for f in feedbacks if f.price_score == i) for i in range(1, 6)},
        }

        return FeedbackStatistics(
            total_feedbacks=total,
            average_overall_score=round(avg_overall, 2),
            average_accuracy_score=round(avg_accuracy, 2),
            average_price_score=round(avg_price, 2),
            average_diversity_score=round(avg_diversity, 2) if avg_diversity else None,
            score_distribution=score_distribution,
        )

    except Exception as e:
        logger.error(f"获取满意度统计数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/api/v1/booklist/feedback", response_model=List[BookListFeedbackResponse])
async def get_feedbacks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取反馈列表（管理员）
    """
    try:
        query = db.query(BookListFeedback)

        total = query.count()
        feedbacks = (
            query.order_by(BookListFeedback.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        return [BookListFeedbackResponse(**f.to_dict()) for f in feedbacks]

    except Exception as e:
        logger.error(f"获取反馈列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/api/v1/book-list/satisfaction", response_model=BookListFeedbackResponse)
async def submit_satisfaction(
    request: BookListFeedbackRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    提交满意度反馈 (适配器别名，适配前端 /book-list/satisfaction 调用)
    """
    return await submit_feedback(request, db, current_user)
