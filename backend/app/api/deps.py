"""
API dependencies for dependency injection.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..core.database import get_db
from ..core.security import verify_token
from ..models.user import User
from ..repositories.user import UserRepository

# Security scheme for JWT token
security = HTTPBearer()


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
        # Verify token and get payload
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
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
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
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


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token is provided, otherwise return None.
    Used for endpoints that can work with or without authentication.
    
    Args:
        credentials: Optional JWT token from Authorization header
        db: Database session
        
    Returns:
        Optional[User]: Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        # Verify token and get payload
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        # Get user from database
        user_repo = UserRepository(db)
        user = user_repo.get(user_id)
        
        if user is None or not user.is_active:
            return None
        
        return user
        
    except Exception:
        return None


# Common dependencies for database session
def get_db_session() -> Session:
    """
    Get database session dependency.
    
    Returns:
        Session: Database session
    """
    return Depends(get_db)


# Pagination parameters
class CommonQueryParams:
    """Common query parameters for pagination and filtering."""
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        skip: int = 0
    ):
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100
            
        self.page = page
        self.page_size = page_size
        self.skip = skip or (page - 1) * page_size


def get_common_params(
    page: int = 1,
    page_size: int = 20,
    skip: int = 0
) -> CommonQueryParams:
    """
    Get common query parameters for pagination.
    
    Args:
        page: Page number (starting from 1)
        page_size: Number of items per page (max 100)
        skip: Number of items to skip (overrides page if provided)
        
    Returns:
        CommonQueryParams: Common query parameters
    """
    return CommonQueryParams(page=page, page_size=page_size, skip=skip)