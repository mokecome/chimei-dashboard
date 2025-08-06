"""
Label-related Pydantic schemas.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class LabelBase(BaseModel):
    """Base label schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class ProductLabelCreate(LabelBase):
    """Schema for creating a product label."""
    pass


class ProductLabelUpdate(BaseModel):
    """Schema for updating a product label."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProductLabelResponse(LabelBase):
    """Schema for product label response."""
    id: int
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackCategoryCreate(LabelBase):
    """Schema for creating a feedback category."""
    pass


class FeedbackCategoryUpdate(BaseModel):
    """Schema for updating a feedback category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FeedbackCategoryResponse(LabelBase):
    """Schema for feedback category response."""
    id: int
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LabelBatchCreate(BaseModel):
    """Schema for batch creating labels."""
    labels: list[str] = Field(..., min_items=1, max_items=200)


class LabelBatchResponse(BaseModel):
    """Schema for batch label creation response."""
    successful_labels: list[str]
    failed_labels: list[dict]
    total_labels: int
    successful_count: int
    failed_count: int