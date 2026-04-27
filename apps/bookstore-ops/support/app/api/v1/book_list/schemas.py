"""
书单推荐 - 请求/响应数据模型

所有数据模型统一定义在这里，便于维护和版本管理
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 共享数据模型 ====================


class CategoryRequirement(BaseModel):
    """分类需求"""

    category: str = Field(..., description="分类名称")
    percentage: float = Field(..., ge=0, le=100, description="百分比")
    count: int = Field(..., ge=0, description="需要数量")


class ParsedRequirements(BaseModel):
    """解析后的需求（统一格式）"""

    target_audience: Optional[str] = Field(None, description="目标受众，如：大学生、中学生")
    cognitive_level: Optional[str] = Field(None, description="认知水平，如：大学生、中学生")
    categories: List[CategoryRequirement] = Field(default_factory=list, description="分类需求列表")
    keywords: List[str] = Field(default_factory=list, description="提取的关键词")
    constraints: List[str] = Field(default_factory=list, description="约束条件")
    exclude_textbooks: bool = Field(default=True, description="是否排除教材")
    min_cognitive_level: Optional[str] = Field(None, description="最低认知水平要求")


class BookRecommendation(BaseModel):
    """推荐书籍"""

    book_id: int
    barcode: str
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    price: Optional[float] = None
    stock: int
    category: Optional[str] = None
    cognitive_level: Optional[str] = None
    difficulty_level: Optional[int] = None
    match_score: float
    remark: Optional[str] = None


# ==================== 步骤1：需求解析 ====================


class ParseRequirementsRequest(BaseModel):
    """需求解析请求"""

    user_input: str = Field(
        ...,
        description="用户原始输入",
        min_length=5,
        max_length=1000,
        examples=["大学生书单，战争20%历史10%经济15%"],
    )
    use_history: bool = Field(
        default=True, description="是否使用用户历史反馈优化解析"
    )


class ParseRequirementsResponse(BaseModel):
    """需求解析响应"""

    request_id: str = Field(..., description="请求ID，用于后续交互")
    session_id: int = Field(..., description="会话ID")
    original_input: str = Field(..., description="用户原始输入")
    parsed_requirements: ParsedRequirements = Field(..., description="后端理解的需求")
    confidence_score: float = Field(..., ge=0, le=1, description="解析置信度")
    suggestions: List[str] = Field(default_factory=list, description="优化建议")
    needs_confirmation: bool = Field(default=True, description="是否需要用户确认")
    message: str = Field(default="需求解析完成，请确认", description="提示信息")


# ==================== 步骤2：需求细化 ====================


class RefineRequirementsRequest(BaseModel):
    """需求细化请求"""

    request_id: str = Field(..., description="原始请求ID")
    refinement_input: str = Field(
        ...,
        description="细化输入",
        min_length=1,
        max_length=500,
        examples=["增加科幻10%，减少历史到5%"],
    )
    manual_adjustments: Optional[Dict[str, Any]] = Field(
        None, description="手动调整（可选，优先级高于文本输入）"
    )


class RefineRequirementsResponse(BaseModel):
    """需求细化响应"""

    request_id: str = Field(..., description="请求ID（保持不变）")
    session_id: int = Field(..., description="会话ID")
    before_requirements: ParsedRequirements = Field(..., description="细化前的需求")
    after_requirements: ParsedRequirements = Field(..., description="细化后的需求")
    changes_summary: List[str] = Field(..., description="变更摘要")
    needs_confirmation: bool = Field(default=True, description="是否需要再次确认")
    message: str = Field(..., description="提示信息")


# ==================== 步骤3：生成书单 ====================


class GenerateBookListRequest(BaseModel):
    """生成书单请求"""

    request_id: Optional[str] = Field(None, description="请求ID（来自解析步骤）")
    requirements: Optional[ParsedRequirements] = Field(
        None, description="直接提供需求（前端页面使用）"
    )
    limit: int = Field(default=20, ge=5, le=100, description="推荐书籍数量")
    save_to_history: bool = Field(default=True, description="是否保存到历史记录")
    auto_complete: bool = Field(default=False, description="是否自动补全提示词")


class GenerateBookListResponse(BaseModel):
    """生成书单响应"""

    request_id: Optional[str] = Field(None, description="请求ID（如果有）")
    session_id: Optional[int] = Field(None, description="会话ID（如果有）")
    book_list_id: Optional[int] = Field(None, description="书单ID（如果保存）")
    requirements: ParsedRequirements = Field(..., description="最终需求")
    recommendations: List[BookRecommendation] = Field(..., description="推荐书单")
    total_count: int = Field(..., description="推荐总数")
    category_distribution: Dict[str, int] = Field(..., description="分类分布")
    generation_time_ms: int = Field(..., description="生成耗时（毫秒）")
    success: bool = Field(default=True)
    message: str = Field(..., description="响应消息")


class ValidatePromptRequest(BaseModel):
    """验证提示词请求"""
    
    prompt: str = Field(..., description="要验证的提示词")


class ValidatePromptResponse(BaseModel):
    """验证提示词响应"""
    
    valid: bool = Field(..., description="提示词是否有效")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    dimensions: Dict[str, bool] = Field(default_factory=dict, description="维度检查结果")


# ==================== 步骤4：分享书单 ====================


class ShareBookListRequest(BaseModel):
    """分享书单请求"""
    
    session_id: Optional[int] = Field(None, description="会话ID")
    book_list_id: Optional[int] = Field(None, description="书单ID")
    is_public: bool = Field(default=True, description="是否公开")


class ShareBookListResponse(BaseModel):
    """分享书单响应"""
    
    share_url: str = Field(..., description="分享链接")
    share_token: str = Field(..., description="分享令牌")
    expiration: Optional[datetime] = Field(None, description="过期时间")


# ==================== 辅助接口 ====================


class SessionInfo(BaseModel):
    """会话信息"""
    
    request_id: str
    session_id: int
    status: str
    original_input: str
    parsed_requirements: Dict[str, Any]
    refinement_count: int
    confirmation_count: int
    created_at: str
    updated_at: str


class CognitiveLevel(BaseModel):
    """认知水平"""
    
    value: str
    label: str
    level: int


class CognitiveLevelsResponse(BaseModel):
    """认知水平列表响应"""
    
    cognitive_levels: List[CognitiveLevel]


class BookListHistoryItem(BaseModel):
    """历史书单项"""
    
    id: int
    request_text: str
    parsed_requirements: Dict[str, Any]
    book_count: int
    status: str
    created_at: str


class BookListHistoryResponse(BaseModel):
    """历史书单列表响应"""
    
    items: List[BookListHistoryItem]
    total: int
    page: int
    limit: int
    pages: int
