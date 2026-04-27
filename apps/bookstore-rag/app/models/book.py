from sqlalchemy import DECIMAL, TIMESTAMP, BigInteger, Column, Integer, String, Text, JSON
from sqlalchemy.sql import func

from app.utils.database import Base


class BookInfo(Base):
    __tablename__ = "t_book_info"
    __table_args__ = {"extend_existing": True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    barcode = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=False)
    title_clean = Column(String(512), nullable=False, index=True)
    author = Column(String(256), index=True)
    publisher = Column(String(256))
    series = Column(String(256))
    price = Column(DECIMAL(10, 2))
    stock = Column(Integer, default=0)
    discount = Column(DECIMAL(5, 4), default=0)
    summary = Column(Text)
    embedding = Column(Text)
    # 筛选标签：存储图书的分类标签，如 ["education", "children"]
    filter_tags = Column(JSON, nullable=True, default=list)
    # 筛选关键词：存储匹配到的筛选关键词，用于追溯
    matched_keywords = Column(JSON, nullable=True, default=list)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())
