import os
import tempfile
import traceback
from pathlib import Path
from urllib.parse import urlparse

import magic
import requests


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


def get_mime_type(file_path: str, default_mime: str | None = None) -> str:
    """
    Detect MIME type of a file using python-magic if available,
    otherwise fallback to extension-based detection.

    Args:
        file_path: Path to the file
        default_mime: Default MIME type to return if detection fails

    Returns:
        str: Detected MIME type
    """
    # Try using python-magic for accurate MIME type detection
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
    except (AttributeError, IOError):
        # Fallback to extension-based detection
        extension_mime_map = {
            # Audio formats
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            # Image formats
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            # Video formats
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".mkv": "video/x-matroska",
            ".webm": "video/webm",
        }

        ext = Path(file_path).suffix.lower()
        return extension_mime_map.get(ext, default_mime or "application/octet-stream")


def get_file_from_source(
    source: str,
    max_size_mb: float = 100.0,
    timeout: int = 60,
) -> tuple[str, str, bytes]:
    """
    Unified function to get file content from a URL or local path with validation.

    Args:
        source: URL or local file path
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

    if is_url(source):
        # Handle URL source
        try:
            # Make a HEAD request first to check content length
            head_response = requests.head(source, timeout=timeout, allow_redirects=True)
            head_response.raise_for_status()

            # Check content length if available
            content_length = head_response.headers.get("content-length")
            if content_length and int(content_length) > max_size_bytes:
                raise ValueError(
                    f"File size ({int(content_length) / (1024 * 1024):.2f} MB) "
                    f"exceeds maximum allowed size ({max_size_mb} MB)"
                )

            # Download the file
            response = requests.get(source, timeout=timeout, stream=True)
            response.raise_for_status()

            # Read content with size checking
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                if len(content) + len(chunk) > max_size_bytes:
                    raise ValueError(f"File size exceeds maximum allowed size ({max_size_mb} MB)")
                content += chunk

            # Create temporary file
            parsed_url = urlparse(source)
            filename = os.path.basename(parsed_url.path) or "downloaded_file"

            # Create temporary file with proper extension
            suffix = Path(filename).suffix or ".tmp"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            # Get MIME type
            mime_type = get_mime_type(temp_path)

            return temp_path, mime_type, content

        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to download file from URL: {e}: {traceback.format_exc()}")
        except Exception as e:
            raise IOError(f"Error processing URL: {e}: {traceback.format_exc()}") from e

    else:
        # Handle local file path
        file_path = Path(source)

        # Check if file exists
        if not file_path.exists():
            raise ValueError(f"File does not exist: {source}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {source}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > max_size_bytes:
            raise ValueError(
                f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
            )

        # Read file content
        try:
            with open(file_path, "rb") as f:
                content = f.read()
        except Exception as e:
            raise IOError(f"Cannot read file {source}: {e}: {traceback.format_exc()}") from e

        # Get MIME type
        mime_type = get_mime_type(str(file_path))

        return str(file_path), mime_type, content
