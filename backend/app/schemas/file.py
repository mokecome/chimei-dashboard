"""
File-related Pydantic schemas.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from ..models.file import FileFormat, FileStatus
from ..models.analysis import SentimentType


class FileBase(BaseModel):
    """Base file schema."""
    filename: str
    original_filename: str
    file_format: FileFormat
    duration: Optional[float] = None


class FileCreate(FileBase):
    """Schema for creating a new file record."""
    file_path: str
    file_size: int
    uploaded_by: int


class FileUpdate(BaseModel):
    """Schema for updating a file record."""
    filename: Optional[str] = None
    status: Optional[FileStatus] = None
    duration: Optional[float] = None


class FileAnalysisResult(BaseModel):
    """Schema for analysis result embedded in file response."""
    sentiment: Optional[SentimentType] = None
    feedback_category: Optional[str] = None
    feedback_summary: Optional[str] = None
    product_names: Optional[List[str]] = None
    transcript: Optional[str] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True  # This will serialize enum values as their actual values


class FileResponse(FileBase):
    """Schema for file response."""
    id: str
    file_size: int
    status: FileStatus
    uploaded_by: int
    uploader_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    analysis_result: Optional[FileAnalysisResult] = None
    
    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """Schema for file list response with pagination."""
    files: list[FileResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    file_id: str
    filename: str
    message: str


class FileBatchUploadResponse(BaseModel):
    """Schema for batch file upload response."""
    successful_uploads: list[FileUploadResponse]
    failed_uploads: list[dict]
    total_files: int
    successful_count: int
    failed_count: int