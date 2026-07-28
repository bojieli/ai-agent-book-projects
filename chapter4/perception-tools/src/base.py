"""
Base models and utilities for perception tools MCP server.
"""
import logging
import os
import tempfile
import traceback
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

import requests
from pydantic import BaseModel, Field


class ActionResponse(BaseModel):
    """Standard response format for all perception tool actions."""
    
    success: bool = Field(default=False, description="Whether the action was successfully executed")
    message: Any = Field(default=None, description="The execution result of the action")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the action")


class DocumentMetadata(BaseModel):
    """Metadata for document processing operations."""
    
    file_name: str = Field(description="Original file name")
    file_size: int = Field(description="File size in bytes")
    file_type: str = Field(description="Document file type/extension")
    absolute_path: str = Field(description="Absolute path to the document file")
    page_count: int | None = Field(default=None, description="Number of pages in document")
    processing_time: float | None = Field(default=None, description="Time taken to process")
    output_format: str = Field(description="Format of the extracted content")


def is_url(path_or_url: str) -> bool:
    """
    Check if the given string is a URL.
    
    Args:
        path_or_url: String to check
        
    Returns:
        True if the string is a URL, False otherwise
    """
    parsed = urlparse(path_or_url)
    return bool(parsed.scheme and parsed.netloc)


def validate_file_path(file_path: str) -> Path:
    """
    Validate and resolve file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Resolved Path object
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path).expanduser().resolve()
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    
    return path


def download_file_from_url(
    url: str,
    timeout: int = 60,
    max_size_mb: float = 100.0
) -> tuple[str, bytes]:
    """
    Download file from URL to temporary location.
    
    Args:
        url: URL to download from
        timeout: Request timeout in seconds
        max_size_mb: Maximum file size in MB
        
    Returns:
        Tuple of (temp_file_path, content)
        
    Raises:
        ValueError: If file size exceeds limit
        requests.RequestException: If download fails
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    # Best-effort size pre-check. Many hosts refuse HEAD (presigned S3/GCS URLs
    # sign the verb and return 403; CDN/WAF-fronted endpoints often return 405),
    # so a failed HEAD must not abort a download that GET can serve -- the
    # streaming loop below enforces max_size_bytes either way.
    try:
        head_response = requests.head(url, timeout=timeout, allow_redirects=True)
        head_response.raise_for_status()
        content_length = head_response.headers.get("content-length")
    except requests.RequestException:
        content_length = None

    if content_length and int(content_length) > max_size_bytes:
        raise ValueError(
            f"File size ({int(content_length) / (1024 * 1024):.2f} MB) "
            f"exceeds maximum allowed size ({max_size_mb} MB)"
        )

    try:
        # Download the file
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Read content with size checking
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            if len(content) + len(chunk) > max_size_bytes:
                raise ValueError(f"File size exceeds maximum allowed size ({max_size_mb} MB)")
            content += chunk
        
        # Create temporary file
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or "downloaded_file"
        suffix = Path(filename).suffix or ".tmp"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        return temp_path, content
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to download file from URL: {e}")
    except ValueError:
        # Documented in the docstring; must not be rewrapped as IOError.
        raise
    except Exception as e:
        raise IOError(f"Error downloading file: {e}")
