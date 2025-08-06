"""
Helper utility functions.
"""
import uuid
import hashlib
import secrets
from typing import Union, Optional
from datetime import datetime, timezone


def generate_unique_id() -> str:
    """
    Generate a unique identifier string.
    
    Returns:
        str: Unique identifier (UUID4)
    """
    return str(uuid.uuid4())


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        str: Secure random token (hex encoded)
    """
    return secrets.token_hex(length)


def generate_hash(data: str, salt: Optional[str] = None) -> str:
    """
    Generate a hash for the given data.
    
    Args:
        data: Data to hash
        salt: Optional salt for hashing
        
    Returns:
        str: SHA-256 hash
    """
    if salt:
        data = data + salt
    return hashlib.sha256(data.encode()).hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        str: Formatted file size (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds: Union[int, float]) -> str:
    """
    Format duration in human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration (e.g., "2:30", "1:05:30")
    """
    if seconds < 0:
        return "0:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of text
        suffix: Suffix to add when truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Invalid characters for filenames
    invalid_chars = '<>:"/\\|?*'
    
    # Replace invalid characters with underscore
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: File name
        
    Returns:
        str: File extension (lowercase, without dot)
    """
    if '.' not in filename:
        return ''
    
    return filename.split('.')[-1].lower()


def is_valid_email_format(email: str) -> bool:
    """
    Basic email format validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email format is valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_current_timestamp() -> datetime:
    """
    Get current timestamp in UTC.
    
    Returns:
        datetime: Current UTC timestamp
    """
    return datetime.now(timezone.utc)


def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp to string.
    
    Args:
        timestamp: Datetime object
        format_str: Format string
        
    Returns:
        str: Formatted timestamp string
    """
    if not timestamp:
        return ""
    
    return timestamp.strftime(format_str)


def safe_int(value: Union[str, int, float], default: int = 0) -> int:
    """
    Safely convert value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        int: Converted integer or default value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Union[str, int, float], default: float = 0.0) -> float:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        float: Converted float or default value
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def chunks(lst: list, chunk_size: int):
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Yields:
        list: Chunks of the original list
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def remove_duplicates(lst: list, key: Optional[str] = None) -> list:
    """
    Remove duplicates from list while preserving order.
    
    Args:
        lst: List with potential duplicates
        key: Optional key function for complex objects
        
    Returns:
        list: List without duplicates
    """
    if not lst:
        return []
    
    seen = set()
    result = []
    
    for item in lst:
        item_key = item if key is None else getattr(item, key, None)
        if item_key not in seen:
            seen.add(item_key)
            result.append(item)
    
    return result


def deep_merge_dict(dict1: dict, dict2: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        dict: Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result