import asyncio
import json
import os
import tempfile
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests
from mcp.server import FastMCP

import logging

logger = logging.getLogger(__name__)


def is_url(path_or_url: str) -> bool:
    """
    Check if the given string is a URL.

    Args:
        path_or_url: String to check

    Returns:
        bool: True if the string is a URL, False otherwise
    """
    parsed = urlparse(path_or_url)
    return bool(parsed.scheme and parsed.netloc)


def get_file_from_source(
    source: str,
    allowed_mime_prefixes: List[str] = None,
    max_size_mb: float = 100.0,
    timeout: int = 60,
    type: str = "image",
) -> Tuple[str, str, bytes]:
    """
    Unified function to get file content from a URL or local path with validation.

    Args:
        source: URL or local file path
        allowed_mime_prefixes: List of allowed MIME type prefixes (e.g., ['audio/', 'video/'])
        max_size_mb: Maximum allowed file size in MB
        timeout: Timeout for URL requests in seconds

    Returns:
        Tuple[str, str, bytes]: (file_path, mime_type, file_content)
        - For URLs, file_path will be a temporary file path
        - For local files, file_path will be the original path

    Raises:
        ValueError: When file doesn't exist, exceeds size limit, or has invalid MIME type
        IOError: When file cannot be read
        requests.RequestException: When URL request fails
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    temp_file = None

    try:
        if is_url(source):
            # Handle URL
            logger.info(f"Downloading file from URL: {source}")
            response = requests.get(source, stream=True, timeout=timeout)
            response.raise_for_status()

            # Check Content-Length if available
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_size_bytes:
                raise ValueError(f"File size exceeds limit of {max_size_mb}MB")

            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            file_path = temp_file.name

            # Download content in chunks to avoid memory issues
            content = bytearray()
            downloaded_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                downloaded_size += len(chunk)
                if downloaded_size > max_size_bytes:
                    raise ValueError(f"File size exceeds limit of {max_size_mb}MB")
                temp_file.write(chunk)
                content.extend(chunk)

            temp_file.close()

            # Get MIME type
            if type == "audio":
                mime_type = "audio/mpeg"
            elif type == "image":
                mime_type = "image/jpeg"
            elif type == "video":
                mime_type = "video/mp4"


            # For URLs where magic fails, try to use Content-Type header
            if mime_type == "application/octet-stream":
                content_type = response.headers.get("Content-Type", "").split(";")[0]
                if content_type:
                    mime_type = content_type
        else:
            # Handle local file
            file_path = os.path.abspath(source)

            # Check if file exists
            if not os.path.exists(file_path):
                raise ValueError(f"File not found: {file_path}")

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > max_size_bytes:
                raise ValueError(f"File size exceeds limit of {max_size_mb}MB")

            # Get MIME type
            if type == "audio":
                mime_type = "audio/mpeg"
            elif type == "image":
                mime_type = "image/jpeg"
            elif type == "video":
                mime_type = "video/mp4"

            # Read file content
            with open(file_path, "rb") as f:
                content = f.read()

        # Validate MIME type if allowed_mime_prefixes is provided
        if allowed_mime_prefixes:
            if not any(
                mime_type.startswith(prefix) for prefix in allowed_mime_prefixes
            ):
                allowed_types = ", ".join(allowed_mime_prefixes)
                raise ValueError(
                    f"Invalid file type: {mime_type}. Allowed types: {allowed_types}"
                )

        return file_path, mime_type, content

    except Exception as e:
        # Clean up temporary file if an error occurs
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise e