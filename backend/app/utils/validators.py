"""
Validation utilities.
"""
import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 100:
        return False, "Password must be less than 100 characters"
    
    # Check for at least one letter and one number
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_number = bool(re.search(r'\d', password))
    
    if not (has_letter and has_number):
        return False, "Password must contain at least one letter and one number"
    
    return True, None


def validate_file_name(filename: str) -> tuple[bool, Optional[str]]:
    """
    Validate file name.
    
    Args:
        filename: File name to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not filename:
        return False, "File name cannot be empty"
    
    if len(filename) > 255:
        return False, "File name too long (max 255 characters)"
    
    # Check for invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    if re.search(invalid_chars, filename):
        return False, "File name contains invalid characters"
    
    return True, None


def validate_user_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Validate user name.
    
    Args:
        name: User name to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Name cannot be empty"
    
    if len(name.strip()) > 100:
        return False, "Name too long (max 100 characters)"
    
    return True, None


def validate_label_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Validate label name.
    
    Args:
        name: Label name to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Label name cannot be empty"
    
    if len(name.strip()) > 100:
        return False, "Label name too long (max 100 characters)"
    
    # Check for special characters that might interfere with analysis
    if any(char in name for char in ['<', '>', '"', "'"]):
        return False, "Label name contains invalid characters"
    
    return True, None