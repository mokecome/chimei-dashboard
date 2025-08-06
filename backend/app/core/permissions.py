"""
Permission management and role-based access control.
"""
from typing import List, Dict
from ..models.user import UserRole


class PermissionChecker:
    """Role-based permission checker."""
    
    # Define permissions for each role
    ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
        UserRole.ADMIN: ["*"],  # All permissions
        UserRole.MANAGER: [
            "read:*",
            "write:data", 
            "write:labels",
            "write:analysis",
            "delete:files"
        ],
        UserRole.OPERATOR: [
            "read:*",
            "write:files",
            "write:analysis"
        ],
        UserRole.VIEWER: [
            "read:*"
        ]
    }
    
    @classmethod
    def check_permission(cls, user_role: UserRole, action: str, resource: str) -> bool:
        """
        Check if a user role has permission for an action on a resource.
        
        Args:
            user_role: The user's role
            action: Action type (read, write, delete)
            resource: Resource type (files, labels, data, etc.)
            
        Returns:
            bool: True if permission is granted, False otherwise
        """
        user_permissions = cls.ROLE_PERMISSIONS.get(user_role, [])
        
        # Admin has all permissions
        if "*" in user_permissions:
            return True
        
        # Check for specific permission
        permission = f"{action}:{resource}"
        if permission in user_permissions:
            return True
        
        # Check for wildcard permissions
        action_wildcard = f"{action}:*"
        resource_wildcard = f"*:{resource}"
        
        return action_wildcard in user_permissions or resource_wildcard in user_permissions
    
    @classmethod
    def get_user_permissions(cls, user_role: UserRole) -> List[str]:
        """
        Get all permissions for a user role.
        """
        return cls.ROLE_PERMISSIONS.get(user_role, [])
    
    @classmethod
    def can_manage_users(cls, user_role: UserRole) -> bool:
        """Check if user can manage other users."""
        return user_role == UserRole.ADMIN
    
    @classmethod
    def can_upload_files(cls, user_role: UserRole) -> bool:
        """Check if user can upload files."""
        return cls.check_permission(user_role, "write", "files")
    
    @classmethod
    def can_delete_files(cls, user_role: UserRole) -> bool:
        """Check if user can delete files."""
        return cls.check_permission(user_role, "delete", "files")
    
    @classmethod
    def can_manage_labels(cls, user_role: UserRole) -> bool:
        """Check if user can manage labels."""
        return cls.check_permission(user_role, "write", "labels")
    
    @classmethod
    def can_export_data(cls, user_role: UserRole) -> bool:
        """Check if user can export data."""
        return user_role in [UserRole.ADMIN, UserRole.MANAGER]