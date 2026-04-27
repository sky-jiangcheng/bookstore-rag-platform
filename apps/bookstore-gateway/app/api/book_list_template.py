"""
书单模板管理API
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.api.auth_management import get_current_active_user, get_current_user_optional
from app.models.auth import User
from app.core.logging_config import get_logger
from app.models import BookListTemplate
from app.models.auth import User
from app.utils.database import get_db

router = APIRouter()
logger = get_logger(__name__)


# ==================== 请求/响应模型 ====================


class BookListTemplateRequest(BaseModel):
    """创建/更新书单模板请求"""

    name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    description: str = Field(..., description="模板描述")
    book_count: int = Field(default=10, ge=1, le=100, description="推荐书籍数量")
    budget: int = Field(default=500, ge=0, le=100000, description="预算范围")
    difficulty: Optional[str] = Field(None, description="难度等级")
    goals: List[str] = Field(default_factory=list, description="阅读目标")
    categories: Optional[List[dict]] = Field(None, description="分类需求")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    constraints: List[str] = Field(default_factory=list, description="约束条件")
    parsed_requirements: Optional[dict] = Field(None, description="预设解析结果")
    is_public: bool = Field(default=False, description="是否公开")
    tags: List[str] = Field(default_factory=list, description="标签")


class BookListTemplateResponse(BaseModel):
    """书单模板响应"""

    id: int
    name: str
    description: str
    user_id: int
    book_count: int
    budget: int
    difficulty: Optional[str]
    goals: List[str]
    categories: Optional[List[dict]]
    keywords: List[str]
    constraints: List[str]
    parsed_requirements: Optional[dict]
    usage_count: int
    like_count: int
    share_count: int
    is_public: bool
    is_active: bool
    is_system: bool
    tags: List[str]
    thumbnail: Optional[str]
    cover_image: Optional[str]
    created_at: str
    updated_at: str


# ==================== 书单模板CRUD接口 ====================


@router.post("/api/v1/booklist/templates", response_model=BookListTemplateResponse)
async def create_template(
    request: BookListTemplateRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建书单模板
    """
    try:
        template = BookListTemplate(
            name=request.name,
            description=request.description,
            user_id=current_user.id,
            book_count=request.book_count,
            budget=request.budget,
            difficulty=request.difficulty,
            goals=request.goals,
            categories=request.categories,
            keywords=request.keywords,
            constraints=request.constraints,
            parsed_requirements=request.parsed_requirements,
            is_public=request.is_public,
            tags=request.tags,
            is_active=True,
            is_system=False,
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        logger.info(
            "创建书单模板成功",
            template_id=template.id,
            user_id=current_user.id,
            template_name=template.name,
        )

        return BookListTemplateResponse(**template.to_dict())

    except Exception as e:
        logger.error(f"创建书单模板失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/api/v1/booklist/templates", response_model=List[BookListTemplateResponse])
async def get_templates(
    is_public: Optional[bool] = Query(None, description="是否公开"),
    is_system: Optional[bool] = Query(None, description="是否系统模板"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    获取书单模板列表（支持未登录访问公开模板）
    """
    try:
        query = db.query(BookListTemplate).filter(BookListTemplate.is_active == True)

        # 过滤条件
        if is_public is not None:
            query = query.filter(BookListTemplate.is_public == is_public)
        if is_system is not None:
            query = query.filter(BookListTemplate.is_system == is_system)

        # 如果已登录，用户可以看到自己的模板或公开模板
        # 如果未登录，只能看到公开模板和系统模板
        if current_user:
            query = query.filter(
                (BookListTemplate.user_id == current_user.id) | (BookListTemplate.is_public == True)
            )
        else:
            query = query.filter(BookListTemplate.is_public == True)

        # 搜索
        if search:
            query = query.filter(BookListTemplate.name.contains(search))

        # 排序：系统模板优先，然后按使用次数
        templates = (
            query.order_by(BookListTemplate.is_system.desc(), BookListTemplate.usage_count.desc())
            .limit(50)
            .all()
        )

        return [BookListTemplateResponse(**template.to_dict()) for template in templates]

    except Exception as e:
        logger.error(f"获取书单模板列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/api/v1/booklist/templates/{template_id}", response_model=BookListTemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取书单模板详情
    """
    template = (
        db.query(BookListTemplate)
        .filter(
            BookListTemplate.id == template_id,
            BookListTemplate.is_active == True,
        )
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 权限检查：只能查看自己的模板或公开模板
    if template.user_id != current_user.id and not template.is_public:
        raise HTTPException(status_code=403, detail="无权访问此模板")

    # 增加使用次数
    template.usage_count += 1
    db.commit()

    return BookListTemplateResponse(**template.to_dict())


@router.put("/api/v1/booklist/templates/{template_id}", response_model=BookListTemplateResponse)
async def update_template(
    template_id: int,
    request: BookListTemplateRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新书单模板
    """
    template = (
        db.query(BookListTemplate)
        .filter(
            BookListTemplate.id == template_id,
            BookListTemplate.user_id == current_user.id,
        )
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    try:
        # 更新字段
        template.name = request.name
        template.description = request.description
        template.book_count = request.book_count
        template.budget = request.budget
        template.difficulty = request.difficulty
        template.goals = request.goals
        template.categories = request.categories
        template.keywords = request.keywords
        template.constraints = request.constraints
        template.parsed_requirements = request.parsed_requirements
        template.is_public = request.is_public
        template.tags = request.tags
        template.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(template)

        logger.info(
            "更新书单模板成功",
            template_id=template.id,
            user_id=current_user.id,
        )

        return BookListTemplateResponse(**template.to_dict())

    except Exception as e:
        logger.error(f"更新书单模板失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/api/v1/booklist/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除书单模板
    """
    template = (
        db.query(BookListTemplate)
        .filter(
            BookListTemplate.id == template_id,
            BookListTemplate.user_id == current_user.id,
        )
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    try:
        # 软删除
        template.is_active = False
        template.updated_at = datetime.utcnow()

        db.commit()

        logger.info(
            "删除书单模板成功",
            template_id=template.id,
            user_id=current_user.id,
        )

        return {"message": "删除成功"}

    except Exception as e:
        logger.error(f"删除书单模板失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ==================== 互动接口 ====================


@router.post("/api/v1/booklist/templates/{template_id}/like")
async def like_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    点赞书单模板
    """
    template = (
        db.query(BookListTemplate)
        .filter(
            BookListTemplate.id == template_id,
            BookListTemplate.is_active == True,
        )
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    try:
        template.like_count += 1
        db.commit()

        return {"message": "点赞成功", "like_count": template.like_count}

    except Exception as e:
        logger.error(f"点赞书单模板失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@router.post("/api/v1/booklist/templates/{template_id}/share")
async def share_template(
    template_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    分享书单模板
    """
    template = (
        db.query(BookListTemplate)
        .filter(
            BookListTemplate.id == template_id,
            BookListTemplate.is_active == True,
        )
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    try:
        template.share_count += 1
        db.commit()

        # 返回分享链接
        host = request.headers.get("host", "localhost:8000")
        scheme = request.url.scheme
        share_link = f"{scheme}://{host}/booklist/template/{template_id}"

        return {"message": "分享成功", "share_count": template.share_count, "share_link": share_link}

    except Exception as e:
        logger.error(f"分享书单模板失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


# ==================== 初始化系统模板 ====================


async def init_system_templates(db: Session):
    """
    初始化系统预设模板
    """
    system_templates = [
        {
            "name": "Python入门学习",
            "description": "适合初学者的Python编程书籍，包含基础语法、实战项目、进阶话题等",
            "book_count": 10,
            "budget": 500,
            "difficulty": "beginner",
            "goals": ["学习编程语言"],
            "keywords": ["Python", "编程", "入门", "基础", "实战"],
            "categories": None,
            "constraints": [],
            "tags": ["编程", "Python", "入门"],
            "is_public": True,
            "is_system": True,
        },
        {
            "name": "数据分析入门",
            "description": "数据分析基础书籍，涵盖统计学、Python数据分析工具、可视化等内容",
            "book_count": 8,
            "budget": 400,
            "difficulty": "beginner",
            "goals": ["数据分析"],
            "keywords": ["数据分析", "统计", "Python", "Pandas", "可视化"],
            "categories": None,
            "constraints": [],
            "tags": ["数据分析", "统计", "可视化"],
            "is_public": True,
            "is_system": True,
        },
        {
            "name": "机器学习进阶",
            "description": "适合有一定基础的读者，涵盖算法原理、框架使用、项目实战等",
            "book_count": 12,
            "budget": 800,
            "difficulty": "advanced",
            "goals": ["机器学习"],
            "keywords": ["机器学习", "深度学习", "算法", "TensorFlow", "PyTorch"],
            "categories": None,
            "constraints": [],
            "tags": ["机器学习", "AI", "深度学习"],
            "is_public": True,
            "is_system": True,
        },
        {
            "name": "Web开发全栈",
            "description": "Web前端和后端开发书籍，包含HTML/CSS/JavaScript、框架、数据库等",
            "book_count": 15,
            "budget": 600,
            "difficulty": "intermediate",
            "goals": ["Web开发"],
            "keywords": ["Web", "前端", "后端", "JavaScript", "Vue", "React"],
            "categories": None,
            "constraints": [],
            "tags": ["Web开发", "前端", "后端"],
            "is_public": True,
            "is_system": True,
        },
    ]

    for template_data in system_templates:
        existing = (
            db.query(BookListTemplate)
            .filter(BookListTemplate.name == template_data["name"], BookListTemplate.is_system == True)
            .first()
        )

        if not existing:
            template = BookListTemplate(
                user_id=1,  # 系统管理员ID
                **template_data,
            )
            db.add(template)

    db.commit()
    logger.info("系统模板初始化完成")
