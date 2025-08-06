"""
Analysis-related Pydantic schemas.
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field
from ..models.analysis import SentimentType


class AnalysisBase(BaseModel):
    """Base analysis schema."""
    transcript: Optional[str] = None
    sentiment: SentimentType
    feedback_category: Optional[str] = None
    feedback_summary: Optional[str] = None
    product_names: Optional[List[str]] = None


class AnalysisCreate(AnalysisBase):
    """Schema for creating analysis result."""
    file_id: str


class AnalysisUpdate(BaseModel):
    """Schema for updating analysis result."""
    transcript: Optional[str] = None
    sentiment: Optional[SentimentType] = None
    feedback_category: Optional[str] = None
    feedback_summary: Optional[str] = None
    product_names: Optional[List[str]] = None


class AnalysisResponse(AnalysisBase):
    """Schema for analysis response."""
    id: str
    file_id: str
    analysis_time: datetime
    created_at: datetime
    
    # File information
    filename: Optional[str] = None
    uploader_name: Optional[str] = None
    upload_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm method to handle JSON fields properly."""
        import json
        
        # Get base data
        data = {
            'id': obj.id,
            'file_id': obj.file_id,
            'analysis_time': obj.analysis_time,
            'created_at': obj.created_at,
            'transcript': obj.transcript,
            'sentiment': obj.sentiment,
            'feedback_category': obj.feedback_category,
            'feedback_summary': obj.feedback_summary,
        }
        
        # Handle JSON product_names field
        if obj.product_names and obj.product_names != 'null':
            if isinstance(obj.product_names, str):
                try:
                    data['product_names'] = json.loads(obj.product_names)
                except json.JSONDecodeError:
                    data['product_names'] = []
            elif isinstance(obj.product_names, list):
                data['product_names'] = obj.product_names
            else:
                data['product_names'] = []
        else:
            # Handle null, None, or string "null" cases
            data['product_names'] = []
        
        return cls(**data)


class AnalysisListResponse(BaseModel):
    """Schema for analysis list response."""
    analyses: List[AnalysisResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AnalysisFilterParams(BaseModel):
    """Schema for analysis filtering parameters."""
    product_names: Optional[List[str]] = None
    feedback_categories: Optional[List[str]] = None
    sentiments: Optional[List[SentimentType]] = None
    uploaders: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AnalysisStatistics(BaseModel):
    """Schema for analysis statistics."""
    total_analyses: int
    sentiment_distribution: dict[str, int]
    product_distribution: dict[str, int]
    category_distribution: dict[str, int]
    daily_trend: List[dict[str, Any]]
    top_products: List[dict[str, Any]]
    recent_analyses: List[AnalysisResponse]


class DashboardData(BaseModel):
    """Schema for dashboard data."""
    total_files: int
    total_analyses: int
    sentiment_chart: dict[str, Any]
    product_chart: dict[str, Any]
    category_chart: dict[str, Any]
    trend_chart: dict[str, Any]
    feedback_trend_chart: dict[str, Any]