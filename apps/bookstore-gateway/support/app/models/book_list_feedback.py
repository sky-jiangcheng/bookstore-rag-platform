"""
用户满意度反馈模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.utils.database import Base


class BookListFeedback(Base):
    """书单满意度反馈"""

    __tablename__ = "book_list_feedbacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booklist_id = Column(String(100), nullable=False, comment="书单ID")
    booklist_name = Column(String(200), comment="书单名称")
    user_id = Column(Integer, nullable=False, comment="用户ID")

    # 评分
    overall_score = Column(Integer, comment="总体评分(1-5)")
    accuracy_score = Column(Integer, comment="推荐准确性(1-5)")
    price_score = Column(Integer, comment="价格合理性(1-5)")
    diversity_score = Column(Integer, comment="书籍多样性(1-5)")

    # 反馈内容
    suggestions = Column(Text, comment="改进建议")

    # 选中的书籍ID列表
    selected_books = Column(JSON, comment="选中的书籍ID列表")

    # 元数据
    book_count = Column(Integer, comment="书籍数量")
    total_price = Column(Integer, comment="总价格")
    average_score = Column(Integer, comment="平均匹配度")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "booklist_id": self.booklist_id,
            "booklist_name": self.booklist_name,
            "user_id": self.user_id,
            "overall_score": self.overall_score,
            "accuracy_score": self.accuracy_score,
            "price_score": self.price_score,
            "diversity_score": self.diversity_score,
            "suggestions": self.suggestions,
            "selected_books": self.selected_books,
            "book_count": self.book_count,
            "total_price": self.total_price,
            "average_score": self.average_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
