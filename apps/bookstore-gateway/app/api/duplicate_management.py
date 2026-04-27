import logging
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.models import BookInfo
from app.models.auth import User
from app.services.log_service import LogService
from app.services.permission_service import require_permission
from app.services.vector_db_service import vector_db
from app.services.vector_service import (
    VectorService,
    clean_title,
    cosine_similarity,
    parse_embedding,
)
from app.utils.database import get_db

router = APIRouter()

# 配置日志
logger = logging.getLogger(__name__)

vector_service = VectorService(dimension=1536)
log_service = LogService()


# 请求模型
class SearchRequest(BaseModel):
    query: str
    limit: int = 20


@router.post("/search")
async def search_duplicates(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        query = request.query
        limit = request.limit

        logger.info(f"Received duplicate search request: {query}, limit: {limit}")

        # 验证参数
        if not query:
            logger.warning("Empty query received")
            return []

        # 清理查询文本
        title_clean = clean_title(query)

        # 从数据库查询候选
        logger.info(
            f"Searching candidates for: title_clean={title_clean}, query={query}"
        )

        # 首先尝试按条码精确匹配
        barcode_candidates = db.query(BookInfo).filter(BookInfo.barcode == query).all()
        logger.info(f"Barcode match candidates: {len(barcode_candidates)}")

        # 然后尝试按标题模糊匹配
        title_candidates = (
            db.query(BookInfo)
            .filter(BookInfo.title_clean.like(f"%{title_clean}%"))
            .limit(100)
            .all()
        )
        logger.info(f"Title match candidates: {len(title_candidates)}")

        # 合并去重
        like_candidates = barcode_candidates + [
            c for c in title_candidates if c not in barcode_candidates
        ]
        logger.info(f"LIKE match candidates: {len(like_candidates)}")

        # 生成查询向量
        query_vec = vector_service.get_vector(title_clean).tolist()  # 转换为列表以适应向量数据库

        # 使用向量数据库进行相似度搜索
        vector_results = []
        vector_search_results = vector_db.search_similar_books(
            query_vector=query_vec, top_k=limit, score_threshold=0.5  # 设置相似度阈值
        )

        for result in vector_search_results:
            # 根据搜索结果获取书籍信息
            book_id = result["book_id"]
            book = db.query(BookInfo).filter(BookInfo.id == book_id).first()
            if book:
                vector_results.append(
                    {
                        "book_id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "barcode": book.barcode,
                        "stock": book.stock,
                        "score": result["score"],
                    }
                )

        logger.info(
            f"Vector database search returned {len(vector_search_results)} results"
        )

        # 处理LIKE查询结果
        like_results = []
        if like_candidates:
            # 处理LIKE候选向量
            like_candidate_vectors = []
            valid_like_candidates = []

            for candidate in like_candidates:
                if candidate.embedding:
                    try:
                        vec = parse_embedding(candidate.embedding, 100)
                        like_candidate_vectors.append(vec)
                        valid_like_candidates.append(candidate)
                    except Exception as e:
                        logger.error(
                            f"Error parsing embedding for book {candidate.id}: {str(e)}"
                        )
                        pass

            if like_candidate_vectors:
                # 计算相似度
                like_candidate_mat = np.vstack(like_candidate_vectors)
                like_scores = cosine_similarity(query_vec, like_candidate_mat)

                # 过滤和排序
                for i, score in enumerate(like_scores):
                    candidate_title = valid_like_candidates[i].title
                    candidate_title_clean = valid_like_candidates[i].title_clean

                    logger.info(
                        f"LIKE Candidate {i}: title={candidate_title}, title_clean={candidate_title_clean}, score={float(score)}"
                    )

                    # 特殊情况：如果标题清理后完全匹配，直接返回
                    if candidate_title_clean == title_clean:
                        logger.info(
                            f"Exact title_clean match found: {candidate_title_clean}"
                        )
                        like_results.append(
                            {
                                "book_id": valid_like_candidates[i].id,
                                "title": valid_like_candidates[i].title,
                                "author": valid_like_candidates[i].author,
                                "barcode": valid_like_candidates[i].barcode,
                                "stock": valid_like_candidates[i].stock,
                                "score": 1.0,  # 完全匹配，设置最高分数
                            }
                        )
                    # 常规情况：根据相似度分数过滤
                    elif score > 0.7:  # 使用更高的阈值以获得更精确的结果
                        like_results.append(
                            {
                                "book_id": valid_like_candidates[i].id,
                                "title": valid_like_candidates[i].title,
                                "author": valid_like_candidates[i].author,
                                "barcode": valid_like_candidates[i].barcode,
                                "stock": valid_like_candidates[i].stock,
                                "score": float(score),
                            }
                        )

            # 按分数排序并限制数量
            like_results.sort(key=lambda x: x["score"], reverse=True)
            like_results = like_results[:limit]

        # 构造返回结果
        result = {
            "like_results": like_results,  # LIKE查询结果
            "vector_results": vector_results,  # 向量数据库相似度结果
            "summary": {
                "like_count": len(like_results),
                "vector_count": len(vector_results),
                "query": query,
            },
            "warning": "数据库中未找到相似书籍，以下结果为向量相似度推荐，仅供参考"
            if len(like_results) == 0 and len(vector_results) == 0
            else None,
        }

        # 将结果存入Redis缓存
        # import json
        # redis_client.setex(cache_key, 900, json.dumps(result, ensure_ascii=False))

        return result

    except Exception as e:
        logger.error(f"Error in duplicate search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class MergeRequest(BaseModel):
    target_book_id: int


@router.post("/merge/{book_id}")
async def merge_book(
    book_id: int,
    request: MergeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    合并两本书籍
    """
    try:
        # 获取要合并的书籍
        source_book = db.query(BookInfo).filter(BookInfo.id == book_id).first()
        target_book = (
            db.query(BookInfo).filter(BookInfo.id == request.target_book_id).first()
        )

        if not source_book or not target_book:
            raise HTTPException(status_code=404, detail="Book not found")

        # 合并库存
        target_book.stock += source_book.stock

        # 保留更完整的信息
        if not target_book.author and source_book.author:
            target_book.author = source_book.author
        if not target_book.publisher and source_book.publisher:
            target_book.publisher = source_book.publisher
        if not target_book.series and source_book.series:
            target_book.series = source_book.series
        if not target_book.price and source_book.price:
            target_book.price = source_book.price
        if not target_book.discount and source_book.discount:
            target_book.discount = source_book.discount
        if not target_book.embedding and source_book.embedding:
            target_book.embedding = source_book.embedding

        # 从向量数据库中删除源书籍的向量
        from app.services.vector_db_service import vector_db

        vector_db.delete_book_vector(book_id)

        # 删除源书籍
        db.delete(source_book)
        db.commit()

        # 记录操作日志
        operation_data = {
            "source_book_id": book_id,
            "source_book_title": source_book.title,
            "target_book_id": target_book.id,
            "target_book_title": target_book.title,
            "merged_stock": source_book.stock,
        }
        log_service.record_operation(
            operation_type="MERGE_BOOK",
            status="SUCCESS",
            entity_id=target_book.id,
            entity_type="BOOK",
            user_id=None,
            details=operation_data,
        )

        logger.info(
            f"Merged book {source_book.title} (ID: {book_id}) into {target_book.title} (ID: {target_book.id})"
        )

        return {
            "message": "Books merged successfully",
            "target_book_id": target_book.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error merging books: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/ignore/{book_id}")
async def ignore_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    忽略书籍（标记为非重复）
    """
    try:
        # 获取要忽略的书籍
        book = db.query(BookInfo).filter(BookInfo.id == book_id).first()

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # 这里可以添加忽略逻辑，例如在数据库中添加标记
        # 为了简单起见，我们只记录日志

        # 记录操作日志
        operation_data = {
            "book_id": book_id,
            "book_title": book.title,
            "barcode": book.barcode,
        }
        log_service.record_operation(
            operation_type="IGNORE_BOOK",
            status="SUCCESS",
            entity_id=book_id,
            entity_type="BOOK",
            user_id=None,
            details=operation_data,
        )

        logger.info(f"Ignored book: {book.title} (ID: {book_id})")

        return {"message": "Book ignored successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ignoring book: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
