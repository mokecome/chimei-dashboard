"""
File handling utilities.
"""
import os
import shutil
import uuid
from typing import Optional, Tuple
from ..config import settings


class FileHandler:
    """File handling utility class."""
    
    @staticmethod
    def ensure_upload_directory() -> str:
        """Ensure upload directory exists and return path."""
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        return upload_dir
    
    @staticmethod
    def generate_file_path(original_filename: str, file_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate unique file path for upload.
        
        Returns:
            Tuple of (file_id, file_path)
        """
        if not file_id:
            file_id = str(uuid.uuid4())
        
        file_ext = os.path.splitext(original_filename)[1]
        upload_dir = FileHandler.ensure_upload_directory()
        file_path = os.path.join(upload_dir, f"{file_id}{file_ext}")
        
        return file_id, file_path
    
    @staticmethod
    def save_uploaded_file(file_data: bytes, file_path: str) -> bool:
        """
        Save uploaded file data to specified path.
        
        Args:
            file_data: File content as bytes
            file_path: Target file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, "wb") as f:
                f.write(file_data)
            return True
        except Exception:
            return False
    
    @staticmethod
    def copy_file(source_path: str, target_path: str) -> bool:
        """
        Copy file from source to target.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            shutil.copy2(source_path, target_path)
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete file safely.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            bool: True if successful or file doesn't exist, False on error
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            Optional[int]: File size in bytes, None if error
        """
        try:
            return os.path.getsize(file_path)
        except Exception:
            return None
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """
        Validate file extension against allowed extensions.
        
        Args:
            filename: File name to validate
            
        Returns:
            bool: True if extension is allowed, False otherwise
        """
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext[1:] in settings.allowed_extensions_list
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """
        Validate file size against maximum allowed size.
        
        Args:
            file_size: File size in bytes
            
        Returns:
            bool: True if size is allowed, False otherwise
        """
        return file_size <= settings.MAX_FILE_SIZE
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        Get file extension from filename.
        
        Args:
            filename: File name
            
        Returns:
            str: File extension without dot
        """
        return os.path.splitext(filename)[1].lower()[1:]