"""File validation utilities"""

import os
import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def validate_audio_file(file_path: Union[str, Path], settings) -> bool:
    """
    Validate that an audio file exists and meets requirements
    
    Args:
        file_path: Path to the audio file
        settings: Application settings object
        
    Returns:
        True if file is valid
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported or file is too large
    """
    file_path = Path(file_path)
    
    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    # Check if it's a file (not directory)
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Check file extension
    file_extension = file_path.suffix.lower()
    if file_extension not in settings.supported_formats:
        raise ValueError(
            f"Unsupported file format: {file_extension}. "
            f"Supported formats: {', '.join(settings.supported_formats)}"
        )
    
    # Check file size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > settings.allowed_file_size_mb:
        raise ValueError(
            f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed "
            f"size ({settings.allowed_file_size_mb} MB)"
        )
    
    # Check file permissions
    if not os.access(file_path, os.R_OK):
        raise ValueError(f"Cannot read file: {file_path}")
    
    logger.info(f"Audio file validation passed: {file_path}")
    return True


def validate_output_path(output_path: Union[str, Path]) -> bool:
    """
    Validate that an output path is writable
    
    Args:
        output_path: Path to validate
        
    Returns:
        True if path is valid and writable
        
    Raises:
        ValueError: If path is not writable
    """
    output_path = Path(output_path)
    
    # Check if parent directory exists and is writable
    parent_dir = output_path.parent
    if not parent_dir.exists():
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Cannot create output directory {parent_dir}: {str(e)}")
    
    # Check if directory is writable
    if not os.access(parent_dir, os.W_OK):
        raise ValueError(f"Output directory is not writable: {parent_dir}")
    
    # If file already exists, check if it's writable
    if output_path.exists() and not os.access(output_path, os.W_OK):
        raise ValueError(f"Cannot write to existing file: {output_path}")
    
    logger.debug(f"Output path validation passed: {output_path}")
    return True


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters
    
    Args:
        filename: Original filename
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
    """
    # Characters that are not allowed in filenames
    invalid_chars = '<>:"/\\|?*'
    
    # Replace invalid characters with underscore
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Truncate if too long, but preserve file extension if present
    if len(sanitized) > max_length:
        if '.' in sanitized:
            name, ext = sanitized.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            sanitized = name[:max_name_length] + '.' + ext
        else:
            sanitized = sanitized[:max_length]
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = "file"
    
    return sanitized
