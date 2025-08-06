"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...schemas.user import LoginRequest, TokenResponse, RefreshTokenRequest, UserResponse, ChangePasswordRequest
from ...schemas.common import SuccessResponse
from ...services.auth_service import AuthService
from ...core.dependencies import get_current_user
from ...models.user import User
from ...config import settings

router = APIRouter()


@router.post("/login")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用戶登錄
    
    - **email**: 用戶郵箱
    - **password**: 用戶密碼
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    email = login_data.get_email()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username is required"
        )
    user = auth_service.authenticate_user(email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token, refresh_token = auth_service.create_tokens(user)
    
    token_data = TokenResponse(
        token=access_token,
        refreshToken=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )
    
    return {
        "message": "Login successful",
        "data": token_data.model_dump()
    }


@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    刷新訪問令牌
    
    - **refresh_token**: 刷新令牌
    """
    auth_service = AuthService(db)
    
    # Refresh access token
    access_token = auth_service.refresh_access_token(refresh_data.refresh_token)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用戶登出
    
    注意: 這是一個簡單的登出端點。在生產環境中，您可能需要實現令牌黑名單機制。
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    獲取當前用戶信息
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密碼
    
    - **current_password**: 當前密碼
    - **new_password**: 新密碼
    """
    auth_service = AuthService(db)
    
    # Change password
    success = auth_service.change_password(
        current_user,
        password_data.current_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    return {"message": "Password changed successfully"}