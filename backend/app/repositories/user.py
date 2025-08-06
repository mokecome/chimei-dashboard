"""
User repository for user-related database operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..models.user import User, UserRole
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository with user-specific operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users only."""
        return (
            self.db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def search_users(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by name or email."""
        return (
            self.db.query(User)
            .filter(
                or_(
                    User.name.contains(query),
                    User.email.contains(query)
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role."""
        return (
            self.db.query(User)
            .filter(User.role == role)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def count_active_users(self) -> int:
        """Count active users."""
        return self.db.query(User).filter(User.is_active == True).count()
    
    def email_exists(self, email: str, exclude_id: Optional[str] = None) -> bool:
        """Check if email already exists."""
        query = self.db.query(User).filter(User.email == email)
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None