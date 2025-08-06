"""
User service for user management operations.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..repositories.user import UserRepository
from ..models.user import User, UserRole
from ..schemas.user import UserCreate, UserUpdate

from ..schemas.common import PaginationParams, PaginatedResponse


class UserService:
    """User management service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.user_repo.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.user_repo.get_by_email(email)
    
    def get_users(
        self, 
        pagination: PaginationParams,
        active_only: bool = False,
        role: Optional[UserRole] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get users with pagination and filtering.
        
        Args:
            pagination: Pagination parameters
            active_only: Filter for active users only
            role: Filter by user role
            search: Search query for name or email
            
        Returns:
            Paginated response with users
        """
        if search:
            users = self.user_repo.search_users(
                search, 
                skip=pagination.offset, 
                limit=pagination.page_size
            )
            # Note: This is simplified count, in production you'd need proper search count
            total = len(users)
        elif role:
            users = self.user_repo.get_by_role(
                role,
                skip=pagination.offset,
                limit=pagination.page_size
            )
            total = self.user_repo.count()  # Simplified
        elif active_only:
            users = self.user_repo.get_active_users(
                skip=pagination.offset,
                limit=pagination.page_size
            )
            total = self.user_repo.count_active_users()
        else:
            users = self.user_repo.get_multi(
                skip=pagination.offset,
                limit=pagination.page_size,
                order_by="created_at",
                desc_order=True
            )
            total = self.user_repo.count()
        
        return PaginatedResponse.create(
            items=users,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
    
    def create_user(self, user_data: UserCreate, created_by: str) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            created_by: ID of user creating this account
            
        Returns:
            Created user object
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        if self.user_repo.email_exists(user_data.email):
            raise ValueError("Email already exists")
        

        
        # Create user
        user_dict = {
            "email": user_data.email,
            "password_hash": user_data.password,
            "name": user_data.name,
            "role": user_data.role,
            "is_active": user_data.is_active
        }
        
        return self.user_repo.create(user_dict)
    
    def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User ID to update
            user_data: User update data
            
        Returns:
            Updated user object or None if not found
            
        Raises:
            ValueError: If email already exists for another user
        """
        user = self.user_repo.get(user_id)
        if not user:
            return None
        
        # Check email uniqueness if email is being updated
        if user_data.email and user_data.email != user.email:
            if self.user_repo.email_exists(user_data.email, exclude_id=user_id):
                raise ValueError("Email already exists")
        
        # Prepare update data
        update_dict = {}
        
        # Update fields if provided
        if user_data.email is not None:
            update_dict["email"] = user_data.email
        if user_data.name is not None:
            update_dict["name"] = user_data.name
        if user_data.role is not None:
            update_dict["role"] = user_data.role
        if user_data.is_active is not None:
            update_dict["is_active"] = user_data.is_active
        if user_data.password is not None:
            update_dict["password_hash"] = user_data.password
        
        # Update user
        return self.user_repo.update(user, update_dict)
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete user.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        user = self.user_repo.delete(user_id)
        return user is not None
    
    def deactivate_user(self, user_id: str) -> Optional[User]:
        """
        Deactivate user instead of deleting.
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            Updated user object or None if not found
        """
        user = self.user_repo.get(user_id)
        if not user:
            return None
        
        return self.user_repo.update(user, {"is_active": False})
    
    def activate_user(self, user_id: str) -> Optional[User]:
        """
        Activate user.
        
        Args:
            user_id: User ID to activate
            
        Returns:
            Updated user object or None if not found
        """
        user = self.user_repo.get(user_id)
        if not user:
            return None
        
        return self.user_repo.update(user, {"is_active": True})
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dictionary with user statistics
        """
        total_users = self.user_repo.count()
        active_users = self.user_repo.count_active_users()
        
        # Count by role
        role_counts = {}
        for role in UserRole:
            role_users = self.user_repo.get_by_role(role, limit=1000)  # Simplified
            role_counts[role.value] = len(role_users)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "role_distribution": role_counts
        }