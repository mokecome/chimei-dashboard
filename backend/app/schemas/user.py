"""
User-related Pydantic schemas.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator
from ..models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: Optional[EmailStr] = None
    username: Optional[EmailStr] = None  # 兼容前端使用 username
    password: str
    
    @model_validator(mode='after')
    def validate_email_or_username(self):
        """確保提供 email 或 username 其中之一"""
        if not self.email and not self.username:
            raise ValueError('Either email or username is required')
        return self
    
    def get_email(self) -> str:
        """獲取郵箱，優先使用 email，如果沒有則使用 username"""
        return self.email or self.username


class TokenResponse(BaseModel):
    """Schema for token response."""
    token: str  # Changed from access_token to token
    refreshToken: str  # Changed from refresh_token to refreshToken
    token_type: str = "bearer"
    expires_in: int
    user: Optional['UserResponse'] = None  # Add user field


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)