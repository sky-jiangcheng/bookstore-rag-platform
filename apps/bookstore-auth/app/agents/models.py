"""
智能体数据模型
独立于 AgentScope 的数据结构定义
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RequirementAnalysis(BaseModel):
    """需求分析结果数据类"""

    target_audience: Dict[str, str]
    categories: List[Dict[str, Any]]
    keywords: List[str]
    constraints: Dict[str, Any]
    confidence: float = Field(..., ge=0, le=1)
    needs_clarification: bool
    clarification_questions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementAnalysis":
        """从字典创建实例"""
        return cls(**data)


class BookCandidate(BaseModel):
    """书籍候选"""

    book_id: int
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    price: Optional[float] = None
    stock: int
    category: Optional[str] = None
    relevance_score: float = Field(..., ge=0, le=1)
    source: str = Field(..., pattern="^(vector|database|popular)$")  # vector, database, popular


class BookListResult(BaseModel):
    """书单结果"""

    books: List[BookCandidate]
    reasoning_chain: List[Dict[str, Any]]
    quality_score: float = Field(..., ge=0, le=1)
    total_price: float = Field(..., ge=0)
    confidence: float = Field(..., ge=0, le=1)
    category_distribution: Dict[str, int]


class UserPreference(BaseModel):
    """用户偏好数据类"""

    user_id: str
    preferred_categories: List[str]
    avoided_categories: List[str]
    preferred_authors: List[str]
    avoided_authors: List[str]
    preferred_price_range: Optional[Dict[str, float]] = None
    average_budget: Optional[float] = Field(None, ge=0)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BookListHistory(BaseModel):
    """书单历史记录"""

    user_id: str
    session_id: str
    requirement: Dict[str, Any]
    booklist: BookListResult
    feedback: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class ReflectionResult(BaseModel):
    """自我反思结果"""

    needs_improvement: bool
    issues: List[str]
    improvement_plan: Dict[str, Any]
    reflection_summary: str
    quality_breakdown: Dict[str, float]
