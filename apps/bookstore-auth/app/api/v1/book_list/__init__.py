"""
书单推荐模块

包含需求解析、需求细化、书单生成等功能
"""

from app.api.v1.book_list.routes import router
from app.api.v1.book_list.schemas import (BookRecommendation,
                                          CategoryRequirement,
                                          GenerateBookListRequest,
                                          GenerateBookListResponse,
                                          ParsedRequirements,
                                          ParseRequirementsRequest,
                                          ParseRequirementsResponse,
                                          RefineRequirementsRequest,
                                          RefineRequirementsResponse,
                                          ValidatePromptRequest,
                                          ValidatePromptResponse)
from app.api.v1.book_list.services import (BookListGenerator,
                                           RequirementParser, validate_prompt)

__all__ = [
    "router",
    "BookRecommendation",
    "CategoryRequirement",
    "GenerateBookListRequest",
    "GenerateBookListResponse",
    "ParsedRequirements",
    "ParseRequirementsRequest",
    "ParseRequirementsResponse",
    "RefineRequirementsRequest",
    "RefineRequirementsResponse",
    "ValidatePromptRequest",
    "ValidatePromptResponse",
    "BookListGenerator",
    "RequirementParser",
    "validate_prompt",
]
