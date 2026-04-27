from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.database import Base


class FilterCategory(Base):
    __tablename__ = "t_filter_category"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    description = Column(String(512))
    is_active = Column(Integer, default=1)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 关系
    keywords = relationship(
        "FilterKeyword", back_populates="category", cascade="all, delete-orphan"
    )


class FilterKeyword(Base):
    __tablename__ = "t_filter_keyword"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(
        Integer, ForeignKey("t_filter_category.id"), nullable=False, index=True
    )
    keyword = Column(String(128), nullable=False, index=True)
    is_active = Column(Integer, default=1)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 关系
    category = relationship("FilterCategory", back_populates="keywords")
