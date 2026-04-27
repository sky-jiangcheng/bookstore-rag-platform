from sqlalchemy import (
    DECIMAL,
    JSON,
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Integer,
    String,
    Text,
)
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

    # RAG扩展字段
    semantic_description = Column(Text, comment="书籍语义描述")
    cognitive_level = Column(String(20), default="通用", comment="认知水平")
    difficulty_level = Column(Integer, default=5, comment="难度等级1-10")
    publication_year = Column(Integer, comment="出版年份")
    language = Column(String(20), default="中文", comment="语言")
    page_count = Column(Integer, comment="页数")
    isbn = Column(String(20), comment="ISBN号码")
    vector_id = Column(String(100), comment="向量数据库ID")

    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())


class UserBehavior(Base):
    __tablename__ = "t_user_behavior"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    book_id = Column(BigInteger, nullable=False)
    action_type = Column(
        String(20), nullable=False
    )  # view,purchase,favorite,cart,review
    rating = Column(DECIMAL(2, 1))  # 1-5分
    duration = Column(Integer)  # 阅读时长(秒)
    context = Column(JSON)  # 行为上下文信息
    created_at = Column(TIMESTAMP, server_default=func.now())


class UserProfile(Base):
    __tablename__ = "t_user_profile"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    age_group = Column(String(20))  # 年龄分组
    education_level = Column(String(50))  # 教育水平
    occupation = Column(String(100))  # 职业
    reading_preferences = Column(JSON)  # 阅读偏好分析
    cognitive_preference = Column(String(20), default="中等")  # 认知偏好
    favorite_categories = Column(JSON)  # 偏好分类及权重
    behavior_summary = Column(JSON)  # 行为统计摘要
    last_analyzed_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())


class CustomBookList(Base):
    __tablename__ = "t_custom_book_list"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    request_text = Column(Text, nullable=False)
    parsed_requirements = Column(JSON)
    book_list = Column(JSON, nullable=False)
    status = Column(
        String(20), default="pending"
    )  # pending,processing,completed,failed
    error_message = Column(Text)
    processing_time = Column(Integer)  # 毫秒
    created_at = Column(TIMESTAMP, server_default=func.now())
    completed_at = Column(TIMESTAMP)


class RAGCache(Base):
    __tablename__ = "t_rag_cache"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    query_hash = Column(String(64), nullable=False, unique=True)
    query_text = Column(Text, nullable=False)
    result = Column(JSON, nullable=False)
    hit_count = Column(Integer, default=1)
    last_hit_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())
    expires_at = Column(TIMESTAMP)


class DuplicateDetection(Base):
    __tablename__ = "t_duplicate_detection"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    query_book_id = Column(BigInteger, nullable=False)
    candidate_book_id = Column(BigInteger, nullable=False)
    similarity_score = Column(DECIMAL(5, 4), nullable=False)
    detection_method = Column(String(20), nullable=False)  # semantic,metadata,hybrid
    is_confirmed = Column(Boolean)
    confirmed_by = Column(BigInteger)
    confirmed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())


class SystemConfig(Base):
    __tablename__ = "t_system_config"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    config_key = Column(String(100), nullable=False, unique=True)
    config_value = Column(JSON, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    updated_by = Column(BigInteger)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
