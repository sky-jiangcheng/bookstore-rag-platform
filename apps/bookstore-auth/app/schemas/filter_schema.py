from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FilterCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="类别名称")
    description: Optional[str] = Field(None, max_length=512, description="类别描述")
    is_active: Optional[int] = Field(1, ge=0, le=1, description="是否激活")


class FilterCategoryCreate(FilterCategoryBase):
    pass


class FilterCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128, description="类别名称")
    description: Optional[str] = Field(None, max_length=512, description="类别描述")
    is_active: Optional[int] = Field(None, ge=0, le=1, description="是否激活")


class FilterCategoryResponse(FilterCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FilterKeywordBase(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=128, description="关键词")
    is_active: Optional[int] = Field(1, ge=0, le=1, description="是否激活")


class FilterKeywordCreate(FilterKeywordBase):
    pass


class FilterKeywordResponse(FilterKeywordBase):
    id: int
    category_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FilterKeywordBatchCreate(BaseModel):
    keywords: List[str] = Field(..., min_length=1, description="关键词列表")


class FilterDocumentImport(BaseModel):
    content: str = Field(..., description="屏蔽词文档内容")
