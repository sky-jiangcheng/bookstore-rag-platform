from typing import List, Optional

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.filter_model import FilterCategory, FilterKeyword
from app.schemas.filter_schema import (
    FilterCategoryCreate,
    FilterCategoryResponse,
    FilterCategoryUpdate,
    FilterDocumentImport,
    FilterKeywordBatchCreate,
    FilterKeywordCreate,
    FilterKeywordResponse,
)
from app.services.filter_service import FilterService
from app.utils.database import get_db

router = APIRouter(prefix="/api/v1/filters", tags=["filters"])
filter_service = FilterService()

# 配置日志
logger = logging.getLogger(__name__)


@router.get("/categories", response_model=List[FilterCategoryResponse])
async def get_filter_categories(
    is_active: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取屏蔽类别列表"""
    query = db.query(FilterCategory)
    if is_active is not None:
        query = query.filter(FilterCategory.is_active == is_active)
    if name:
        query = query.filter(FilterCategory.name.like(f"%{name}%"))
    categories = query.all()
    return categories


@router.post("/categories", response_model=FilterCategoryResponse)
async def create_filter_category(
    category: FilterCategoryCreate, db: Session = Depends(get_db)
):
    """创建屏蔽类别"""
    # 检查是否已存在同名类别
    existing = (
        db.query(FilterCategory).filter(FilterCategory.name == category.name).first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="类别名称已存在")

    db_category = FilterCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/categories/{category_id}", response_model=FilterCategoryResponse)
async def update_filter_category(
    category_id: int, category: FilterCategoryUpdate, db: Session = Depends(get_db)
):
    """更新屏蔽类别"""
    db_category = (
        db.query(FilterCategory).filter(FilterCategory.id == category_id).first()
    )
    if not db_category:
        raise HTTPException(status_code=404, detail="类别不存在")

    # 检查名称是否与其他类别冲突
    if category.name and category.name != db_category.name:
        existing = (
            db.query(FilterCategory)
            .filter(
                FilterCategory.name == category.name, FilterCategory.id != category_id
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="类别名称已存在")

    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/categories/{category_id}")
async def delete_filter_category(category_id: int, db: Session = Depends(get_db)):
    """删除屏蔽类别"""
    db_category = (
        db.query(FilterCategory).filter(FilterCategory.id == category_id).first()
    )
    if not db_category:
        raise HTTPException(status_code=404, detail="类别不存在")

    db.delete(db_category)
    db.commit()
    return {"message": "类别删除成功"}


@router.get(
    "/categories/{category_id}/keywords", response_model=List[FilterKeywordResponse]
)
async def get_filter_keywords(
    category_id: int,
    is_active: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取指定类别的屏蔽关键词"""
    # 检查类别是否存在
    category = db.query(FilterCategory).filter(FilterCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="类别不存在")

    query = db.query(FilterKeyword).filter(FilterKeyword.category_id == category_id)
    if is_active is not None:
        query = query.filter(FilterKeyword.is_active == is_active)
    if keyword:
        query = query.filter(FilterKeyword.keyword.like(f"%{keyword}%"))

    keywords = query.all()
    return keywords


@router.post("/categories/{category_id}/keywords", response_model=FilterKeywordResponse)
async def create_filter_keyword(
    category_id: int, keyword: FilterKeywordCreate, db: Session = Depends(get_db)
):
    """为类别添加屏蔽关键词"""
    # 检查类别是否存在
    category = db.query(FilterCategory).filter(FilterCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="类别不存在")

    # 检查关键词是否已存在
    existing = (
        db.query(FilterKeyword)
        .filter(
            FilterKeyword.category_id == category_id,
            FilterKeyword.keyword == keyword.keyword,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="关键词已存在")

    db_keyword = FilterKeyword(
        category_id=category_id, keyword=keyword.keyword, is_active=keyword.is_active
    )
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword


@router.post("/categories/{category_id}/keywords/batch", response_model=dict)
async def batch_create_filter_keywords(
    category_id: int,
    batch_data: FilterKeywordBatchCreate,
    db: Session = Depends(get_db),
):
    """批量为类别添加屏蔽关键词"""
    # 检查类别是否存在
    category = db.query(FilterCategory).filter(FilterCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="类别不存在")

    created_count = 0
    existing_count = 0

    for keyword in batch_data.keywords:
        # 检查关键词是否已存在
        existing = (
            db.query(FilterKeyword)
            .filter(
                FilterKeyword.category_id == category_id,
                FilterKeyword.keyword == keyword,
            )
            .first()
        )
        if not existing:
            db_keyword = FilterKeyword(
                category_id=category_id, keyword=keyword, is_active=1
            )
            db.add(db_keyword)
            created_count += 1
        else:
            existing_count += 1

    db.commit()
    return {
        "created": created_count,
        "existing": existing_count,
        "total": len(batch_data.keywords),
    }


@router.delete("/keywords/{keyword_id}")
async def delete_filter_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """删除屏蔽关键词"""
    db_keyword = db.query(FilterKeyword).filter(FilterKeyword.id == keyword_id).first()
    if not db_keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    db.delete(db_keyword)
    db.commit()
    return {"message": "关键词删除成功"}


@router.post("/import/document", response_model=dict)
async def import_filter_document(
    import_data: FilterDocumentImport, db: Session = Depends(get_db)
):
    """导入屏蔽词文档"""
    import traceback

    try:
        # 解析文档
        parsed_data = filter_service.parse_filter_document(import_data.content)

        if not parsed_data:
            raise HTTPException(status_code=400, detail="文档解析失败")

        # 验证解析结果
        is_valid, error_msg = filter_service.validate_filter_data(parsed_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        logger.info(f"开始导入: {len(parsed_data)} 个类别")

        # 导入类别和关键词
        category_count = 0
        keyword_count = 0
        existing_category_count = 0
        existing_keyword_count = 0

        for category_name, keywords in parsed_data.items():
            logger.info(f"处理类别: {category_name}，包含 {len(keywords)} 个关键词")

            # 查找或创建类别
            try:
                existing_category = (
                    db.query(FilterCategory)
                    .filter(FilterCategory.name == category_name)
                    .first()
                )

                if existing_category:
                    category = existing_category
                    existing_category_count += 1
                    logger.info(f"类别已存在: {category_name}")
                else:
                    category = FilterCategory(
                        name=category_name,
                        description=f"从文档导入的{category_name}类别",
                        is_active=1,
                    )
                    db.add(category)
                    db.commit()
                    # 不使用refresh，直接使用category对象
                    category_count += 1
                    logger.info(f"创建类别: {category_name}")

                # 添加关键词
                batch_size = 100
                batch_keywords = []

                for i, keyword in enumerate(keywords):
                    try:
                        existing_keyword = (
                            db.query(FilterKeyword)
                            .filter(
                                FilterKeyword.category_id == category.id,
                                FilterKeyword.keyword == keyword,
                            )
                            .first()
                        )

                        if not existing_keyword:
                            batch_keywords.append(
                                FilterKeyword(
                                    category_id=category.id,
                                    keyword=keyword,
                                    is_active=1,
                                )
                            )
                            keyword_count += 1
                        else:
                            existing_keyword_count += 1

                        # 批量提交
                        if len(batch_keywords) >= batch_size:
                            db.add_all(batch_keywords)
                            db.commit()
                            batch_keywords = []
                            logger.info(f"批量提交 {batch_size} 个关键词")
                    except Exception as keyword_error:
                        logger.error(f"处理关键词 '{keyword}' 时出错: {str(keyword_error)}")
                        continue

                # 提交剩余的关键词
                if batch_keywords:
                    db.add_all(batch_keywords)
                    db.commit()
                    logger.info(f"提交剩余的 {len(batch_keywords)} 个关键词")

            except Exception as category_error:
                logger.error(f"处理类别 '{category_name}' 时出错: {str(category_error)}")
                db.rollback()
                continue

        logger.info(f"导入完成: 创建了 {category_count} 个类别，{keyword_count} 个关键词")

        return {
            "message": "文档导入成功",
            "categories_created": category_count,
            "categories_existing": existing_category_count,
            "keywords_created": keyword_count,
            "keywords_existing": existing_keyword_count,
            "total_categories": category_count + existing_category_count,
            "total_keywords": keyword_count + existing_keyword_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
