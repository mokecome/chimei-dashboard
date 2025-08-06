"""
Authentication core functionality.

This module consolidates authentication-related functions.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from ..config import settings
from ..core.database import get_db
from ..models.user import User, UserRole
from ..repositories.user import UserRepository
from .security import verify_password, verify_token


# Security scheme
security = HTTPBearer()


class AuthenticationError(Exception):
    """Base authentication exception."""
    pass


class InvalidCredentials(AuthenticationError):
    """Invalid credentials exception."""
    pass


class InactiveUser(AuthenticationError):
    """Inactive user exception."""
    pass


class InvalidToken(AuthenticationError):
    """Invalid token exception."""
    pass


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
        
    Raises:
        InvalidCredentials: If credentials are invalid
        InactiveUser: If user is inactive
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(email)
    
    if not user:
        raise InvalidCredentials("Invalid email or password")
    
    if not verify_password(password, user.password_hash):
        raise InvalidCredentials("Invalid email or password")
    
    if not user.is_active:
        raise InactiveUser("User account is inactive")
    
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: JWT token from Authorization header
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_repo = UserRepository(db)
        user = user_repo.get(user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_user_with_role(required_role: UserRole):
    """
    Dependency to check if current user has required role.
    
    Args:
        required_role: Required user role
        
    Returns:
        Dependency function that validates user role
    """
    def check_role(current_user: User = Depends(get_current_active_user)) -> User:
        # Admin has access to everything
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        # Check if user has the required role
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return check_role


def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user if they are an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_manager_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user if they are a manager or admin."""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return current_user


def get_operator_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user if they have operator access or higher."""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator access required"
        )
    return current_user


def check_user_permission(user: User, permission: str) -> bool:
    """
    Check if user has specific permission.
    
    Args:
        user: User object
        permission: Permission string (e.g., "read:files", "write:analysis")
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    from .permissions import has_permission
    return has_permission(user.role, permission)


def require_permission(permission: str):
    """
    Dependency to check if current user has specific permission.
    
    Args:
        permission: Required permission string
        
    Returns:
        Dependency function that validates user permission
    """
    def check_permission(current_user: User = Depends(get_current_active_user)) -> User:
        if not check_user_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return check_permission


# Token management utilities
def create_token_response(user: User) -> Dict[str, Any]:
    """
    Create token response for authenticated user.
    
    Args:
        user: Authenticated user
        
    Returns:
        dict: Token response with access and refresh tokens
    """
    from .security import create_access_token, create_refresh_token
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value
        }
    }


def validate_refresh_token(refresh_token: str, db: Session) -> User:
    """
    Validate refresh token and return user.
    
    Args:
        refresh_token: Refresh token string
        db: Database session
        
    Returns:
        User: User associated with the token
        
    Raises:
        InvalidToken: If token is invalid or user not found
    """
    try:
        payload = jwt.decode(
            refresh_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise InvalidToken("Invalid refresh token")
        
        user_repo = UserRepository(db)
        user = user_repo.get(user_id)
        
        if user is None:
            raise InvalidToken("User not found")
        
        if not user.is_active:
            raise InvalidToken("User is inactive")
        
        return user
        
    except JWTError:
        raise InvalidToken("Invalid refresh token")


# Session management
class SessionManager:
    """Manage user sessions and token blacklist."""
    
    # In-memory blacklist (in production, use Redis or database)
    _blacklist = set()
    
    @classmethod
    def blacklist_token(cls, token: str) -> None:
        """Add token to blacklist."""
        cls._blacklist.add(token)
    
    @classmethod
    def is_token_blacklisted(cls, token: str) -> bool:
        """Check if token is blacklisted."""
        return token in cls._blacklist
    
    @classmethod
    def clear_expired_tokens(cls) -> None:
        """Clear expired tokens from blacklist."""
        # In production, implement proper cleanup based on token expiration
        pass