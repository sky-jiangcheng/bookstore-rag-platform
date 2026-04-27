"""
需求解析相关模型

包含：
1. DemandAnalysisSession - 需求解析会话
2. PromptTemplate - 提示词模板
"""

from datetime import datetime

from sqlalchemy import (JSON, BigInteger, Column, DateTime, ForeignKey,
                        Integer, String)
from sqlalchemy.orm import relationship

from app.utils.database import Base


class DemandAnalysisSession(Base):
    """
    需求解析会话

    存储用户与系统之间的对话历史和当前需求状态
    """

    __tablename__ = "demand_analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID
    user_id = Column(BigInteger, ForeignKey("t_user.id"), nullable=False)
    dialogue_history = Column(JSON, default=list)  # 对话历史
    current_context = Column(JSON, default=dict)  # 当前需求状态
    status = Column(
        String(20), default="in_progress"
    )  # in_progress, completed, cancelled
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    user = relationship("User", backref="demand_analysis_sessions")


class PromptTemplate(Base):
    """
    提示词模板

    存储生成的书单推荐提示词模板
    """

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID
    user_id = Column(BigInteger, ForeignKey("t_user.id"), nullable=False)
    template_content = Column(JSON, nullable=False)  # 模板内容
    status = Column(String(20), default="active")  # active, inactive
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    user = relationship("User", backref="prompt_templates")
