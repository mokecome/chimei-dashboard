"""
File repository for file-related database operations.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_

from ..models.file import VoiceFile, FileStatus, FileFormat
from ..models.user import User
from .base import BaseRepository


class FileRepository(BaseRepository[VoiceFile]):
    """File repository with file-specific operations."""
    
    def __init__(self, db: Session):
        super().__init__(VoiceFile, db)
    
    def get_with_uploader(self, file_id: str) -> Optional[VoiceFile]:
        """Get file with uploader information."""
        return (
            self.db.query(VoiceFile)
            .options(joinedload(VoiceFile.uploader))
            .filter(VoiceFile.id == file_id)
            .first()
        )
    
    def get_multi_with_uploader(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[FileStatus] = None,
        format: Optional[FileFormat] = None,
        uploaded_by: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[VoiceFile]:
        """Get multiple files with uploader information and filtering."""
        query = (
            self.db.query(VoiceFile)
            .options(joinedload(VoiceFile.uploader))
            .order_by(desc(VoiceFile.created_at))
        )
        
        # Apply filters
        if status:
            query = query.filter(VoiceFile.status == status)
        if format:
            query = query.filter(VoiceFile.file_format == format)
        if uploaded_by:
            query = query.filter(VoiceFile.uploaded_by == uploaded_by)
        if start_date:
            query = query.filter(VoiceFile.created_at >= start_date)
        if end_date:
            query = query.filter(VoiceFile.created_at <= end_date)
        
        return query.offset(skip).limit(limit).all()
    
    def count_with_filters(
        self,
        status: Optional[FileStatus] = None,
        format: Optional[FileFormat] = None,
        uploaded_by: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count files with filters."""
        query = self.db.query(VoiceFile)
        
        # Apply filters
        if status:
            query = query.filter(VoiceFile.status == status)
        if format:
            query = query.filter(VoiceFile.file_format == format)
        if uploaded_by:
            query = query.filter(VoiceFile.uploaded_by == uploaded_by)
        if start_date:
            query = query.filter(VoiceFile.created_at >= start_date)
        if end_date:
            query = query.filter(VoiceFile.created_at <= end_date)
        
        return query.count()
    
    def get_by_status(self, status: FileStatus) -> List[VoiceFile]:
        """Get files by status."""
        return (
            self.db.query(VoiceFile)
            .filter(VoiceFile.status == status)
            .order_by(desc(VoiceFile.created_at))
            .all()
        )
    
    def get_by_uploader(self, uploader_id: str, skip: int = 0, limit: int = 100) -> List[VoiceFile]:
        """Get files by uploader."""
        return (
            self.db.query(VoiceFile)
            .filter(VoiceFile.uploaded_by == uploader_id)
            .order_by(desc(VoiceFile.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update_status(self, file_id: str, status: FileStatus) -> Optional[VoiceFile]:
        """Update file status."""
        file_obj = self.get(file_id)
        if file_obj:
            file_obj.status = status
            self.db.commit()
            self.db.refresh(file_obj)
        return file_obj
    
    def get_pending_files(self) -> List[VoiceFile]:
        """Get files pending analysis."""
        return (
            self.db.query(VoiceFile)
            .filter(VoiceFile.status == FileStatus.PENDING)
            .order_by(VoiceFile.created_at)
            .all()
        )
    
    def search_files(self, query: str, skip: int = 0, limit: int = 100) -> List[VoiceFile]:
        """Search files by filename."""
        return (
            self.db.query(VoiceFile)
            .options(joinedload(VoiceFile.uploader))
            .filter(VoiceFile.original_filename.contains(query))
            .order_by(desc(VoiceFile.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )