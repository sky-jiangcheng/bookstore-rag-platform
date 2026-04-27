"""
图书筛选标签管理API

提供基于配置文件的图书筛选标签查询、统计、分析等功能
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.models import BookInfo
from app.models.auth import User
from app.services.filter_service import book_filter_service
from app.utils.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/book-filters/categories")
async def get_filter_categories(
    current_user: User = Depends(get_current_active_user),
):
    """获取所有筛选分类"""
    try:
        categories = book_filter_service.get_all_categories()
        return {
            "categories": categories,
            "total": len(categories),
        }
    except Exception as e:
        logger.error(f"Error getting filter categories: {str(e)}")
        raise HTTPException(status_code=500, detail="获取筛选分类失败")


@router.get("/book-filters/categories/{category_code}")
async def get_category_detail(
    category_code: str,
    current_user: User = Depends(get_current_active_user),
):
    """获取指定分类的详细信息"""
    try:
        category_info = book_filter_service.get_category_info(category_code)
        if not category_info:
            raise HTTPException(status_code=404, detail="分类不存在")

        return category_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting category detail: {str(e)}")
        raise HTTPException(status_code=500, detail="获取分类详情失败")


@router.get("/book-filters/statistics")
async def get_filter_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取筛选统计信息"""
    try:
        # 获取所有图书的筛选标签
        books = db.query(BookInfo).filter(BookInfo.filter_tags.isnot(None)).all()

        # 统计各分类的图书数量
        stats = {code: 0 for code in book_filter_service.categories.keys()}
        total_filtered = 0

        for book in books:
            tags = book.filter_tags if book.filter_tags else []
            if tags:
                total_filtered += 1
                for tag in tags:
                    if tag in stats:
                        stats[tag] += 1

        return {
            "statistics": {
                "total_books": db.query(BookInfo).count(),
                "total_filtered_books": total_filtered,
                "category_distribution": stats,
            },
            "categories": book_filter_service.get_all_categories(),
        }
    except Exception as e:
        logger.error(f"Error getting filter statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="获取筛选统计失败")


@router.post("/book-filters/analyze")
async def analyze_book_filters(
    book_data: dict,
    current_user: User = Depends(get_current_active_user),
):
    """分析单本书的筛选标签"""
    try:
        analysis = book_filter_service.analyze_book(
            title=book_data.get("title", ""),
            author=book_data.get("author"),
            publisher=book_data.get("publisher"),
            summary=book_data.get("summary"),
        )

        return {
            "title": book_data.get("title", ""),
            "filter_tags": analysis["filter_tags"],
            "matched_keywords": analysis["matched_keywords"],
            "categories": analysis["categories"],
        }
    except Exception as e:
        logger.error(f"Error analyzing book filters: {str(e)}")
        raise HTTPException(status_code=500, detail="分析图书筛选失败")


@router.post("/book-filters/batch-analyze")
async def batch_analyze_books(
    books: List[dict],
    current_user: User = Depends(get_current_active_user),
):
    """批量分析图书的筛选标签"""
    try:
        results = []
        for book_data in books:
            analysis = book_filter_service.analyze_book(
                title=book_data.get("title", ""),
                author=book_data.get("author"),
                publisher=book_data.get("publisher"),
                summary=book_data.get("summary"),
            )

            results.append({
                "title": book_data.get("title", ""),
                "barcode": book_data.get("barcode", ""),
                "filter_tags": analysis["filter_tags"],
                "matched_keywords": analysis["matched_keywords"],
                "categories": analysis["categories"],
            })

        # 统计
        summary = book_filter_service.get_filter_summary(results)

        return {
            "results": results,
            "summary": summary,
        }
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="批量分析失败")


@router.get("/book-filters/books/by-tag")
async def get_books_by_filter_tag(
    filter_tag: str = Query(..., description="筛选标签"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """根据筛选标签查询图书"""
    try:
        # 查询包含指定标签的图书
        books = db.query(BookInfo).all()

        # 过滤包含指定标签的图书
        filtered_books = []
        for book in books:
            book_tags = book.filter_tags if book.filter_tags else []
            if filter_tag in book_tags:
                filtered_books.append(book)

        total = len(filtered_books)

        # 分页
        start = (page - 1) * limit
        end = start + limit
        paginated_books = filtered_books[start:end]

        result = []
        for book in paginated_books:
            result.append({
                "id": book.id,
                "barcode": book.barcode,
                "title": book.title,
                "author": book.author,
                "publisher": book.publisher,
                "filter_tags": book.filter_tags,
                "matched_keywords": book.matched_keywords,
                "stock": book.stock,
                "discount": float(book.discount) if book.discount else 0,
            })

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "filter_tag": filter_tag,
        }
    except Exception as e:
        logger.error(f"Error getting books by filter tag: {str(e)}")
        raise HTTPException(status_code=500, detail="查询图书失败")


@router.post("/book-filters/books/{book_id}/reanalyze")
async def reanalyze_book_filters(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """重新分析指定图书的筛选标签"""
    try:
        book = db.query(BookInfo).filter(BookInfo.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="图书不存在")

        # 重新分析筛选标签
        analysis = book_filter_service.analyze_book(
            title=book.title,
            author=book.author,
            publisher=book.publisher,
            summary=book.summary,
        )

        # 更新数据库
        book.filter_tags = analysis["filter_tags"]
        book.matched_keywords = analysis["matched_keywords"]
        db.commit()

        return {
            "id": book.id,
            "title": book.title,
            "filter_tags": analysis["filter_tags"],
            "matched_keywords": analysis["matched_keywords"],
            "categories": analysis["categories"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reanalyzing book filters: {str(e)}")
        raise HTTPException(status_code=500, detail="重新分析失败")