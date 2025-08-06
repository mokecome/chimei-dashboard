"""
FastAPI dependencies for authentication and authorization.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User, UserRole
from ..repositories.user import UserRepository
from .security import verify_token
from .permissions import PermissionChecker

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    # Get user email from token
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    # Get user from database
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(email)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for get_current_user).
    """
    return current_user


def require_permission(action: str, resource: str):
    """
    Dependency factory for requiring specific permissions.
    """
    def permission_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not PermissionChecker.check_permission(current_user.role, action, resource):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions for {action}:{resource}"
            )
        return current_user
    
    return permission_dependency


def require_role(required_role: UserRole):
    """
    Dependency factory for requiring specific user role.
    """
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role.value}"
            )
        return current_user
    
    return role_dependency


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_manager_or_above(current_user: User = Depends(get_current_user)) -> User:
    """
    Require manager role or above.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access or above required"
        )
    return current_user