"""
Configuration settings for the Chime Dashboard application.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database Configuration
    DATABASE_URL: str = "mysql://root:123456@127.0.0.1:3306/chime_dashboard"
    
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-here-please-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8小時 (原本30分鐘)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30     # 30天 (原本7天)
    
    # File Storage Configuration
    UPLOAD_DIR: str = "./storage/uploads"
    MAX_FILE_SIZE: int = 104857600  # 100MB
    ALLOWED_EXTENSIONS: str = "wav,mp3,txt"
    
    # AI Configuration
    LLM_API_URL: str = "http://192.168.50.123:11434/api/generate"
    LLM_MODEL_NAME: str = "qwen3:8b"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = False
    
    # CORS Configuration
    CORS_ORIGINS: str = "*"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    @property
    def allowed_extensions_list(self) -> list[str]:
        """Get allowed file extensions as a list."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()