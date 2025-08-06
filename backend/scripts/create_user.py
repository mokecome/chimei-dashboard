#!/usr/bin/env python3
"""
User creation script for Chime Dashboard.

This script allows creating new users for the system with different roles.
"""
import sys
import os
import argparse
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import engine, get_db
from app.models.user import User, UserRole
from app.utils.validators import validate_email, validate_password


def create_user(
    name: str,
    email: str,
    password: str,
    role: UserRole = UserRole.VIEWER,
    is_active: bool = True
) -> User:
    """
    Create a new user in the database.
    
    Args:
        name: User's full name
        email: User's email address
        password: User's password (will be hashed)
        role: User's role (default: VIEWER)
        is_active: Whether user is active (default: True)
        
    Returns:
        User: Created user object
        
    Raises:
        ValueError: If validation fails
        Exception: If user already exists or database error
    """
    # Validate email format
    if not validate_email(email):
        raise ValueError("Invalid email format")
    
    # Validate password
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        raise ValueError(f"Invalid password: {error_msg}")
    
    # Validate name
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")
    
    # Create database session
    db = Session(engine)
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise Exception(f"User with email {email} already exists")
        
        # Create new user
        user = User(
            name=name.strip(),
            email=email.lower(),
            role=role,
            is_active=is_active
        )
        
        # Set password (will be hashed automatically)
        user.set_password(password)
        
        # Add to database
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ User created successfully:")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role.value}")
        print(f"   Active: {user.is_active}")
        print(f"   Created: {user.created_at}")
        
        return user
        
    except Exception as e:
        db.rollback()
        raise e
        
    finally:
        db.close()


def list_users():
    """List all users in the database."""
    db = Session(engine)
    
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        
        if not users:
            print("No users found in the database.")
            return
        
        print(f"\n📋 Found {len(users)} users:")
        print("-" * 80)
        print(f"{'ID':<36} {'Name':<20} {'Email':<30} {'Role':<10} {'Active':<6} {'Created'}")
        print("-" * 80)
        
        for user in users:
            created_str = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
            print(f"{str(user.id):<36} {user.name[:19]:<20} {user.email[:29]:<30} {user.role.value:<10} {'Yes' if user.is_active else 'No':<6} {created_str}")
        
    finally:
        db.close()


def activate_user(email: str):
    """Activate a user by email."""
    db = Session(engine)
    
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User with email {email} not found")
            return
        
        if user.is_active:
            print(f"ℹ️  User {email} is already active")
            return
        
        user.is_active = True
        db.commit()
        
        print(f"✅ User {email} has been activated")
        
    finally:
        db.close()


def deactivate_user(email: str):
    """Deactivate a user by email."""
    db = Session(engine)
    
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User with email {email} not found")
            return
        
        if not user.is_active:
            print(f"ℹ️  User {email} is already inactive")
            return
        
        user.is_active = False
        db.commit()
        
        print(f"✅ User {email} has been deactivated")
        
    finally:
        db.close()


def change_user_role(email: str, new_role: str):
    """Change a user's role."""
    db = Session(engine)
    
    try:
        # Validate role
        try:
            role = UserRole(new_role.lower())
        except ValueError:
            print(f"❌ Invalid role: {new_role}")
            print(f"   Valid roles: {', '.join([r.value for r in UserRole])}")
            return
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User with email {email} not found")
            return
        
        old_role = user.role.value
        user.role = role
        db.commit()
        
        print(f"✅ User {email} role changed from {old_role} to {role.value}")
        
    finally:
        db.close()


def reset_user_password(email: str, new_password: str):
    """Reset a user's password."""
    db = Session(engine)
    
    try:
        # Validate password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            print(f"❌ Invalid password: {error_msg}")
            return
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User with email {email} not found")
            return
        
        user.set_password(new_password)
        db.commit()
        
        print(f"✅ Password for user {email} has been reset")
        
    finally:
        db.close()


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="User management script for Chime Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new admin user
  python create_user.py create "Admin User" admin@chimei.com admin123 --role admin
  
  # Create a regular operator user
  python create_user.py create "John Doe" john@chimei.com password123 --role operator
  
  # List all users
  python create_user.py list
  
  # Activate a user
  python create_user.py activate john@chimei.com
  
  # Change user role
  python create_user.py change-role john@chimei.com manager
  
  # Reset user password
  python create_user.py reset-password john@chimei.com newpassword123
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create user command
    create_parser = subparsers.add_parser('create', help='Create a new user')
    create_parser.add_argument('name', help='User full name')
    create_parser.add_argument('email', help='User email address')
    create_parser.add_argument('password', help='User password')
    create_parser.add_argument('--role', choices=['admin', 'manager', 'operator', 'viewer'], 
                              default='viewer', help='User role (default: viewer)')
    create_parser.add_argument('--inactive', action='store_true', 
                              help='Create user as inactive (default: active)')
    
    # List users command
    subparsers.add_parser('list', help='List all users')
    
    # Activate user command
    activate_parser = subparsers.add_parser('activate', help='Activate a user')
    activate_parser.add_argument('email', help='User email address')
    
    # Deactivate user command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate a user')
    deactivate_parser.add_argument('email', help='User email address')
    
    # Change role command
    role_parser = subparsers.add_parser('change-role', help='Change user role')
    role_parser.add_argument('email', help='User email address')
    role_parser.add_argument('role', choices=['admin', 'manager', 'operator', 'viewer'],
                           help='New user role')
    
    # Reset password command
    password_parser = subparsers.add_parser('reset-password', help='Reset user password')
    password_parser.add_argument('email', help='User email address')
    password_parser.add_argument('password', help='New password')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'create':
            role = UserRole(args.role.lower())
            is_active = not args.inactive
            create_user(args.name, args.email, args.password, role, is_active)
            
        elif args.command == 'list':
            list_users()
            
        elif args.command == 'activate':
            activate_user(args.email)
            
        elif args.command == 'deactivate':
            deactivate_user(args.email)
            
        elif args.command == 'change-role':
            change_user_role(args.email, args.role)
            
        elif args.command == 'reset-password':
            reset_user_password(args.email, args.password)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()