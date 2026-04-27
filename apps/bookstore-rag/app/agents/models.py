"""
智能体数据模型
独立于 AgentScope 的数据结构定义
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class RequirementAnalysis:
    """需求分析结果数据类"""
    target_audience: Dict[str, str]
    categories: List[Dict[str, Any]]
    keywords: List[str]
    constraints: Dict[str, Any]
    confidence: float
    needs_clarification: bool
    clarification_questions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "target_audience": self.target_audience,
            "categories": self.categories,
            "keywords": self.keywords,
            "constraints": self.constraints,
            "confidence": self.confidence,
            "needs_clarification": self.needs_clarification,
            "clarification_questions": self.clarification_questions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementAnalysis":
        """从字典创建实例"""
        return cls(**data)


@dataclass
class BookCandidate:
    """书籍候选"""
    book_id: int
    title: str
    author: str
    publisher: str
    price: float
    stock: int
    category: str
    relevance_score: float
    source: str  # vector, database, popular


@dataclass
class BookListResult:
    """书单结果"""
    books: List[BookCandidate]
    reasoning_chain: List[Dict[str, Any]]
    quality_score: float
    total_price: float
    confidence: float
    category_distribution: Dict[str, int]


@dataclass
class UserPreference:
    """用户偏好数据类"""
    user_id: str
    preferred_categories: List[str]
    avoided_categories: List[str]
    preferred_authors: List[str]
    avoided_authors: List[str]
    preferred_price_range: Optional[Dict[str, float]] = None
    average_budget: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class BookListHistory:
    """书单历史记录"""
    user_id: str
    session_id: str
    requirement: Dict[str, Any]
    booklist: BookListResult
    feedback: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


@dataclass
class ReflectionResult:
    """自我反思结果"""
    needs_improvement: bool
    issues: List[str]
    improvement_plan: Dict[str, Any]
    reflection_summary: str
    quality_breakdown: Dict[str, float]
