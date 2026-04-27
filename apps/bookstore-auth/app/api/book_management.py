import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.models import BookInfo
from app.models.auth import User
from app.utils.database import get_db

router = APIRouter()

# 配置日志
logger = logging.getLogger(__name__)


# 图书管理API
@router.get("/books")
async def get_books(
    title: Optional[str] = Query(None, description="图书标题"),
    author: Optional[str] = Query(None, description="作者"),
    publisher: Optional[str] = Query(None, description="出版社"),
    barcode: Optional[str] = Query(None, description="条码"),
    min_stock: Optional[int] = Query(None, ge=0, description="最小库存"),
    max_stock: Optional[int] = Query(None, ge=0, description="最大库存"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取图书列表，支持分页和多条件筛选
    """
    try:
        # 构建查询
        query = db.query(BookInfo)

        # 应用筛选条件
        if title:
            query = query.filter(BookInfo.title.like(f"%{title}%"))
        if author:
            query = query.filter(BookInfo.author.like(f"%{author}%"))
        if publisher:
            query = query.filter(BookInfo.publisher.like(f"%{publisher}%"))
        if barcode:
            query = query.filter(BookInfo.barcode.like(f"%{barcode}%"))
        if min_stock is not None:
            query = query.filter(BookInfo.stock >= min_stock)
        if max_stock is not None:
            query = query.filter(BookInfo.stock <= max_stock)

        # 计算总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        books = query.order_by(BookInfo.id.desc()).offset(offset).limit(limit).all()

        # 转换结果
        result = []
        for book in books:
            result.append(
                {
                    "id": book.id,
                    "barcode": book.barcode,
                    "title": book.title,
                    "author": book.author,
                    "publisher": book.publisher,
                    "series": book.series,
                    "price": float(book.price) if book.price else None,
                    "stock": book.stock,
                    "discount": float(book.discount) if book.discount else 0,
                    "created_at": book.created_at,
                    "updated_at": book.updated_at,
                }
            )

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except Exception as e:
        logger.error(f"Error getting books: {str(e)}")
        raise HTTPException(status_code=500, detail="获取图书列表失败")


@router.get("/books/{book_id}")
async def get_book_detail(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取图书详情
    """
    try:
        book = db.query(BookInfo).filter(BookInfo.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="图书不存在")

        return {
            "id": book.id,
            "barcode": book.barcode,
            "title": book.title,
            "author": book.author,
            "publisher": book.publisher,
            "series": book.series,
            "price": float(book.price) if book.price else None,
            "stock": book.stock,
            "discount": float(book.discount) if book.discount else 0,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting book detail: {str(e)}")
        raise HTTPException(status_code=500, detail="获取图书详情失败")


@router.put("/books/{book_id}")
async def update_book(
    book_id: int,
    book_data: dict = Body(..., description="图书信息"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新图书信息
    """
    try:
        book = db.query(BookInfo).filter(BookInfo.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="图书不存在")

        # 更新字段
        update_fields = [
            "title",
            "author",
            "publisher",
            "series",
            "price",
            "discount",
            "barcode",
        ]
        for field in update_fields:
            if field in book_data:
                setattr(book, field, book_data[field])

        # 特殊处理库存
        if "stock" in book_data:
            book.stock = book_data["stock"]

        db.commit()
        db.refresh(book)

        return {
            "id": book.id,
            "barcode": book.barcode,
            "title": book.title,
            "stock": book.stock,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
            "message": "图书信息更新成功",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating book: {str(e)}")
        raise HTTPException(status_code=500, detail="更新图书信息失败")


@router.put("/books/{book_id}/stock")
async def update_book_stock(
    book_id: int,
    stock_data: dict = Body(..., description="库存数据"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新图书库存
    """
    try:
        book = db.query(BookInfo).filter(BookInfo.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="图书不存在")

        # 检查库存数据
        if "stock" not in stock_data:
            raise HTTPException(status_code=400, detail="缺少库存数据")

        stock = stock_data["stock"]
        if not isinstance(stock, int) or stock < 0:
            raise HTTPException(status_code=400, detail="库存必须是非负整数")

        # 更新库存
        book.stock = stock
        db.commit()
        db.refresh(book)

        return {
            "id": book.id,
            "title": book.title,
            "stock": book.stock,
            "updated_at": book.updated_at,
            "message": "库存更新成功",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating book stock: {str(e)}")
        raise HTTPException(status_code=500, detail="更新库存失败")


@router.delete("/books/{book_id}")
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除图书（谨慎使用）
    """
    try:
        book = db.query(BookInfo).filter(BookInfo.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="图书不存在")

        db.delete(book)
        db.commit()

        return {"message": "图书删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting book: {str(e)}")
        raise HTTPException(status_code=500, detail="删除图书失败")
