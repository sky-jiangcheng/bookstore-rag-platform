import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.models import BookInfo
from app.models.auth import User
from app.utils.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/new")
async def get_new_recommendations(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        # 简单的推荐逻辑：按折扣和库存排序
        recommendations = (
            db.query(BookInfo)
            .filter(BookInfo.stock > 0, BookInfo.discount > 0)
            .order_by(BookInfo.discount.desc(), BookInfo.stock.asc())
            .limit(limit)
            .all()
        )

        result = []
        for book in recommendations:
            try:
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
                    }
                )
            except Exception as e:
                logger.error(f"Error processing book {book.id}: {str(e)}")
                continue

        logger.info(f"Returned {len(result)} new recommendations")
        return result
    except Exception as e:
        logger.error(f"Error getting new recommendations: {str(e)}")
        return []
