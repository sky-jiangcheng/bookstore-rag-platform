"""
书单模板模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON

from app.utils.database import Base


class BookListTemplate(Base):
    """书单模板"""

    __tablename__ = "book_list_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    user_id = Column(Integer, nullable=False, comment="创建用户ID")

    # 模板参数
    book_count = Column(Integer, default=10, comment="推荐书籍数量")
    budget = Column(Integer, default=500, comment="预算范围")
    difficulty = Column(String(50), comment="难度等级")

    # JSON字段存储复杂参数
    goals = Column(JSON, comment="阅读目标列表")
    categories = Column(JSON, comment="分类需求")
    keywords = Column(JSON, comment="关键词列表")
    constraints = Column(JSON, comment="约束条件")

    # 预设解析结果
    parsed_requirements = Column(JSON, comment="预设的解析结果")

    # 统计信息
    usage_count = Column(Integer, default=0, comment="使用次数")
    like_count = Column(Integer, default=0, comment="点赞数")
    share_count = Column(Integer, default=0, comment="分享数")

    # 状态
    is_public = Column(Boolean, default=False, comment="是否公开")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_system = Column(Boolean, default=False, comment="是否系统模板")

    # 标签
    tags = Column(JSON, comment="标签列表")

    # 元数据
    thumbnail = Column(String(500), comment="缩略图URL")
    cover_image = Column(String(500), comment="封面图URL")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "user_id": self.user_id,
            "book_count": self.book_count,
            "budget": self.budget,
            "difficulty": self.difficulty,
            "goals": self.goals or [],
            "categories": self.categories or [],
            "keywords": self.keywords or [],
            "constraints": self.constraints or [],
            "parsed_requirements": self.parsed_requirements,
            "usage_count": self.usage_count,
            "like_count": self.like_count,
            "share_count": self.share_count,
            "is_public": self.is_public,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "tags": self.tags or [],
            "thumbnail": self.thumbnail,
            "cover_image": self.cover_image,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
