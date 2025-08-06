"""
File service for file management operations.
"""
import os
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..repositories.file import FileRepository
from ..models.file import VoiceFile, FileStatus, FileFormat
from ..schemas.file import FileCreate, FileUpdate
from ..schemas.common import PaginationParams, PaginatedResponse
from ..config import settings
from ..ai.speech_to_text import speech_service


class FileService:
    """File management service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_repo = FileRepository(db)
    
    def get_file(self, file_id: str) -> Optional[VoiceFile]:
        """Get file by ID."""
        return self.file_repo.get_with_uploader(file_id)
    
    def get_files(
        self,
        pagination: PaginationParams,
        status: Optional[FileStatus] = None,
        format: Optional[FileFormat] = None,
        uploaded_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get files with pagination and filtering."""
        files = self.file_repo.get_multi_with_uploader(
            skip=pagination.offset,
            limit=pagination.page_size,
            status=status,
            format=format,
            uploaded_by=uploaded_by
        )
        
        total = self.file_repo.count_with_filters(
            status=status,
            format=format,
            uploaded_by=uploaded_by
        )
        
        return PaginatedResponse.create(
            items=files,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
    
    def create_file_record(self, file_data: FileCreate) -> VoiceFile:
        """Create file record in database."""
        file_dict = file_data.dict()
        
        # Calculate duration for audio files
        if file_data.file_format in [FileFormat.WAV, FileFormat.MP3]:
            duration = speech_service.get_audio_duration(file_data.file_path)
            file_dict["duration"] = duration
        
        return self.file_repo.create(file_dict)
    
    def update_file(self, file_id: str, file_data: FileUpdate) -> Optional[VoiceFile]:
        """Update file information."""
        file_obj = self.file_repo.get(file_id)
        if not file_obj:
            return None
        
        update_dict = file_data.dict(exclude_unset=True)
        return self.file_repo.update(file_obj, update_dict)
    
    def delete_file(self, file_id: str, remove_physical: bool = True) -> bool:
        """Delete file and optionally remove physical file."""
        file_obj = self.file_repo.get(file_id)
        if not file_obj:
            return False
        
        # Remove physical file if requested
        if remove_physical and os.path.exists(file_obj.file_path):
            try:
                os.remove(file_obj.file_path)
            except Exception:
                # Log error but continue with database deletion
                pass
        
        # Delete from database
        self.file_repo.delete(file_id)
        return True
    
    def update_file_status(self, file_id: str, status: FileStatus) -> Optional[VoiceFile]:
        """Update file processing status."""
        return self.file_repo.update_status(file_id, status)
    
    def get_pending_files(self) -> List[VoiceFile]:
        """Get files pending analysis."""
        return self.file_repo.get_pending_files()
    
    def search_files(self, query: str, pagination: PaginationParams) -> Dict[str, Any]:
        """Search files by filename."""
        files = self.file_repo.search_files(
            query,
            skip=pagination.offset,
            limit=pagination.page_size
        )
        
        # Simplified count for search results
        total = len(files)
        
        return PaginatedResponse.create(
            items=files,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
    
    def validate_file_format(self, filename: str) -> bool:
        """Validate if file format is supported."""
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext[1:] in settings.allowed_extensions_list
    
    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size."""
        return file_size <= settings.MAX_FILE_SIZE
    
    def generate_file_id(self) -> str:
        """Generate unique file ID."""
        return str(uuid.uuid4())
    
    def get_file_statistics(self) -> Dict[str, Any]:
        """Get file statistics."""
        total_files = self.file_repo.count()
        
        # Count by status
        status_counts = {}
        for status in FileStatus:
            files = self.file_repo.get_by_status(status)
            status_counts[status.value] = len(files)
        
        # Count by format
        format_counts = {}
        for format in FileFormat:
            files = self.file_repo.count_with_filters(format=format)
            format_counts[format.value] = files
        
        return {
            "total_files": total_files,
            "status_distribution": status_counts,
            "format_distribution": format_counts
        }