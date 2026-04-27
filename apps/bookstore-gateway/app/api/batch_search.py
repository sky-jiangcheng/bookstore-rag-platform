"""
批量搜索API - 优化大批量向量检索

功能:
1. 批量书籍查询
2. 批量向量检索
3. 并发搜索优化
"""

import logging
from typing import List, Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.models import BookInfo
from app.models.auth import User
from app.services.vector_db_service import vector_db
from app.services.vector_service import VectorService, clean_title, cosine_similarity
from app.utils.database import get_db

router = APIRouter()

logger = logging.getLogger(__name__)

vector_service = VectorService(dimension=1536)


# ==================== 请求/响应模型 ====================


class BatchSearchRequest(BaseModel):
    """批量搜索请求"""

    queries: List[str]
    limit: int = 20
    score_threshold: float = 0.7


class BatchSearchResult(BaseModel):
    """批量搜索结果"""

    query: str
    results: List[dict]
    count: int


class BatchSearchResponse(BaseModel):
    """批量搜索响应"""

    results: List[BatchSearchResult]
    total_queries: int
    total_results: int


# ==================== API端点 ====================


@router.post("/batch-search", response_model=BatchSearchResponse)
async def batch_search_duplicates(
    request: BatchSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    批量查重 - 优化大批量查询

    Args:
        queries: 查询字符串列表
        limit: 每个查询返回的最大结果数
        score_threshold: 相似度阈值

    Returns:
        批量搜索结果
    """
    queries = request.queries
    limit = request.limit
    score_threshold = request.score_threshold

    logger.info(f"Received batch search request with {len(queries)} queries")

    if not queries:
        raise HTTPException(status_code=400, detail="查询列表不能为空")

    if len(queries) > 100:
        raise HTTPException(status_code=400, detail="批量查询最多支持100个")

    all_results = []
    total_results = 0

    # 批量生成查询向量
    logger.info("Generating query vectors")
    query_vectors = []
    for query in queries:
        title_clean = clean_title(query)
        query_vec = vector_service.get_vector(title_clean).tolist()
        query_vectors.append(query_vec)

    # 使用批量向量检索
    logger.info(f"Batch searching with vector DB")
    try:
        batch_results = vector_db.batch_search(
            query_vectors=query_vectors,
            top_k=limit,
            score_threshold=score_threshold,
        )

        # 处理每个查询的结果
        for idx, (query, results) in enumerate(zip(queries, batch_results)):
            formatted_results = []

            for result in results:
                book_id = result["book_id"]
                book = db.query(BookInfo).filter(BookInfo.id == book_id).first()

                if book:
                    formatted_results.append(
                        {
                            "book_id": book.id,
                            "title": book.title,
                            "author": book.author,
                            "barcode": book.barcode,
                            "stock": book.stock,
                            "score": result["score"],
                        }
                    )

            all_results.append(
                BatchSearchResult(query=query, results=formatted_results, count=len(formatted_results))
            )
            total_results += len(formatted_results)

        logger.info(
            f"Batch search completed: {len(queries)} queries, {total_results} total results"
        )

        return BatchSearchResponse(
            results=all_results,
            total_queries=len(queries),
            total_results=total_results,
        )

    except Exception as e:
        logger.error(f"Error in batch search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量搜索失败: {str(e)}")


class BatchBookIdsRequest(BaseModel):
    """批量书籍ID请求"""

    book_ids: List[int]


@router.post("/batch-books", response_model=List[dict])
async def get_batch_books(
    request: BatchBookIdsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    批量获取书籍信息

    Args:
        book_ids: 书籍ID列表

    Returns:
        书籍信息列表
    """
    book_ids = request.book_ids

    logger.info(f"Received batch books request with {len(book_ids)} IDs")

    if not book_ids:
        raise HTTPException(status_code=400, detail="书籍ID列表不能为空")

    if len(book_ids) > 500:
        raise HTTPException(status_code=400, detail="批量查询最多支持500本书籍")

    try:
        # 批量查询（使用IN子句）
        books = (
            db.query(BookInfo).filter(BookInfo.id.in_(book_ids)).all()
        )

        # 构建结果字典
        books_dict = {book.id: book for book in books}

        # 按请求顺序返回
        results = []
        for book_id in book_ids:
            book = books_dict.get(book_id)
            if book:
                results.append({
                    "book_id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "publisher": book.publisher,
                    "barcode": book.barcode,
                    "stock": book.stock,
                    "price": float(book.price) if book.price else None,
                    "discount": float(book.discount),
                })
            else:
                results.append({
                    "book_id": book_id,
                    "error": "Book not found"
                })

        logger.info(f"Batch books query completed: {len(results)} results")

        return results

    except Exception as e:
        logger.error(f"Error in batch books query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量查询失败: {str(e)}")


class BatchBookSearchRequest(BaseModel):
    """批量书籍搜索请求"""

    keywords: List[str]
    page: int = 1
    limit: int = 20


class BatchBookSearchResponse(BaseModel):
    """批量书籍搜索响应"""

    results: dict
    total_queries: int


@router.post("/batch-book-search", response_model=BatchBookSearchResponse)
async def batch_search_books(
    request: BatchBookSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    批量书籍搜索

    Args:
        keywords: 关键词列表
        page: 页码
        limit: 每页数量

    Returns:
        每个关键词的搜索结果
    """
    keywords = request.keywords
    page = request.page
    limit = request.limit

    logger.info(f"Received batch book search request with {len(keywords)} keywords")

    if not keywords:
        raise HTTPException(status_code=400, detail="关键词列表不能为空")

    if len(keywords) > 20:
        raise HTTPException(status_code=400, detail="批量搜索最多支持20个关键词")

    try:
        results = {}

        for keyword in keywords:
            query = (
                db.query(BookInfo)
                .filter(
                    BookInfo.title.like(f"%{keyword}%")
                    | BookInfo.author.like(f"%{keyword}%")
                )
                .order_by(BookInfo.id)
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )

            results[keyword] = [
                {
                    "book_id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "barcode": book.barcode,
                    "stock": book.stock,
                }
                for book in query
            ]

        logger.info(f"Batch book search completed: {len(keywords)} queries")

        return BatchBookSearchResponse(
            results=results,
            total_queries=len(keywords),
        )

    except Exception as e:
        logger.error(f"Error in batch book search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量搜索失败: {str(e)}")
