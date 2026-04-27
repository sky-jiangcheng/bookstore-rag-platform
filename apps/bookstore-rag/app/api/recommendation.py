import logging
from fastapi import APIRouter, Depends
from typing import Optional
from fastapi import Query
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.models import BookInfo
from app.models.auth import User
from app.services.filter_service import book_filter_service
from app.utils.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/new")
async def get_new_recommendations(
    limit: int = 20,
    exclude_filter_tags: Optional[str] = Query(None, description="排除的筛选标签，逗号分隔，如: education,children"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        # 解析排除标签
        excluded_tags = []
        if exclude_filter_tags:
            excluded_tags = [tag.strip() for tag in exclude_filter_tags.split(",") if tag.strip()]

        # 简单的推荐逻辑：按折扣和库存排序，获取更多数据用于过滤
        recommendations = (
            db.query(BookInfo)
            .filter(BookInfo.stock > 0, BookInfo.discount > 0)
            .order_by(BookInfo.discount.desc(), BookInfo.stock.asc())
            .limit(limit * 2)  # 获取更多数据用于过滤
            .all()
        )

        result = []
        for book in recommendations:
            try:
                # 获取图书的筛选标签
                book_tags = book.filter_tags if book.filter_tags else []

                # 如果图书标签在排除列表中，跳过
                if excluded_tags and book_filter_service.should_filter_book(book_tags, excluded_tags):
                    continue

                # 计算推荐指数，确保在0-1之间
                discount_score = float(book.discount) if book.discount else 0
                stock_score = 1.0 / (book.stock / 100 + 1)  # 库存越少分数越高，最大为1
                recommendation_score = discount_score * 0.7 + stock_score * 0.3

                result.append(
                    {
                        "book_id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "price": float(book.price) if book.price else 0,
                        "discount": float(book.discount) if book.discount else 0,
                        "stock": book.stock,
                        "recommendation_score": recommendation_score,
                        "filter_tags": book_tags,
                        "matched_keywords": book.matched_keywords if book.matched_keywords else [],
                    }
                )

                # 达到数量限制
                if len(result) >= limit:
                    break
            except Exception as e:
                logger.error(f"Error processing book {book.id}: {str(e)}")
                continue

        logger.info(f"Returned {len(result)} new recommendations with filters: {excluded_tags}")
        return {
            "recommendations": result,
            "count": len(result),
            "excluded_tags": excluded_tags,
        }
    except Exception as e:
        logger.error(f"Error getting new recommendations: {str(e)}")
        return {"recommendations": [], "count": 0, "excluded_tags": []}
