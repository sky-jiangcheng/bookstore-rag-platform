"""
书单推荐会话模型

用于支持交互式书单推荐流程：
1. 用户输入模糊需求
2. 后端LLM解析并返回理解（带requestId）
3. 用户确认或细化需求
4. 生成最终书单
"""

from sqlalchemy import (JSON, TIMESTAMP, BigInteger, Column, Integer, String,
                        Text)
from sqlalchemy.sql import func

from app.utils.database import Base


class BookListSession(Base):
    """书单推荐会话表"""

    __tablename__ = "t_book_list_session"
    __table_args__ = {"extend_existing": True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    request_id = Column(
        String(64), unique=True, nullable=False, index=True, comment="请求ID（UUID）"
    )
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")

    # 用户输入
    original_input = Column(Text, nullable=False, comment="用户原始输入")
    refined_inputs = Column(JSON, comment="历次细化输入列表")

    # 后端理解（解析结果）
    parsed_requirements = Column(JSON, nullable=False, comment="解析后的需求（最新版本）")
    parsing_history = Column(JSON, comment="解析历史记录")

    # 会话状态
    status = Column(
        String(20),
        default="parsing",
        nullable=False,
        index=True,
        comment="状态：parsing(解析中), waiting_confirmation(等待确认), refining(细化中), confirmed(已确认), generating(生成中), completed(已完成), failed(失败)",
    )

    # 用户反馈
    user_feedbacks = Column(JSON, comment="用户反馈历史")
    confirmation_count = Column(Integer, default=0, comment="确认次数")
    refinement_count = Column(Integer, default=0, comment="细化次数")

    # 生成结果
    book_list_id = Column(BigInteger, comment="生成的书单ID")
    generation_params = Column(JSON, comment="最终生成参数")

    # 性能指标
    parsing_time_ms = Column(Integer, comment="解析耗时（毫秒）")
    generation_time_ms = Column(Integer, comment="生成耗时（毫秒）")
    total_time_ms = Column(Integer, comment="总耗时（毫秒）")

    # 错误信息
    error_message = Column(Text, comment="错误信息")

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    confirmed_at = Column(TIMESTAMP, comment="确认时间")
    completed_at = Column(TIMESTAMP, comment="完成时间")


class SessionFeedback(Base):
    """会话反馈表"""

    __tablename__ = "t_session_feedback"
    __table_args__ = {"extend_existing": True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    session_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False)

    # 反馈内容
    feedback_type = Column(
        String(20),
        nullable=False,
        comment="反馈类型：confirmation(确认), refinement(细化), rejection(拒绝), satisfaction(满意度)",
    )
    feedback_content = Column(Text, comment="反馈内容")
    feedback_data = Column(JSON, comment="结构化反馈数据")

    # 反馈前后对比
    before_requirements = Column(JSON, comment="反馈前的需求")
    after_requirements = Column(JSON, comment="反馈后的需求")

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now())
