"""
Authentication service for login, logout, and token management.
"""
from datetime import timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from ..core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from ..repositories.user import UserRepository
from ..models.user import User
from ..schemas.user import UserCreate
from ..config import settings


class AuthService:
    """Authentication service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        from ..config import settings
        import logging
        
        logger = logging.getLogger(__name__)
        
        # 調試模式下記錄詳細信息
        if settings.DEBUG:
            logger.info(f"🔍 Authentication attempt for email: {email}")
        
        user = self.user_repo.get_by_email(email)
        if not user:
            if settings.DEBUG:
                logger.warning(f"❌ User not found: {email}")
            return None
        
        if not user.is_active:
            if settings.DEBUG:
                logger.warning(f"❌ User inactive: {email}")
            return None
        
        password_valid = verify_password(password, user.password)
        if not password_valid:
            if settings.DEBUG:
                logger.warning(f"❌ Invalid password for: {email}")
            return None
        
        if settings.DEBUG:
            logger.info(f"✅ Successful authentication: {email}")
        
        return user
    
    def create_tokens(self, user: User) -> Tuple[str, str]:
        """
        Create access and refresh tokens for user.
        
        Args:
            user: User object
            
        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        return access_token, refresh_token
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New access token if successful, None otherwise
        """
        # Verify refresh token
        payload = verify_token(refresh_token)
        if not payload:
            return None
        
        # Get user email from token
        email = payload.get("sub")
        if not email:
            return None
        
        # Get user from database
        user = self.user_repo.get_by_email(email)
        if not user or not user.is_active:
            return None
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        return access_token
    
    def register_user(self, user_data: UserCreate, created_by: Optional[str] = None) -> User:
        """
        Register a new user.
        
        Args:
            user_data: User creation data
            created_by: ID of user creating this account (for admin creation)
            
        Returns:
            Created user object
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        if self.user_repo.email_exists(user_data.email):
            raise ValueError("Email already registered")
        
        # Store password directly
        password = get_password_hash(user_data.password)
        
        # Create user
        user_dict = {
            "email": user_data.email,
            "password": password,
            "name": user_data.name,
            "role": user_data.role,
            "is_active": user_data.is_active
        }
        
        return self.user_repo.create(user_dict)
    
    def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user: User object
            current_password: Current password
            new_password: New password
            
        Returns:
            True if successful, False otherwise
        """
        # Verify current password
        if not verify_password(current_password, user.password):
            return False
        
        # Store new password directly
        new_password = get_password_hash(new_password)
        
        # Update user
        self.user_repo.update(user, {"password": new_password})
        
        return True