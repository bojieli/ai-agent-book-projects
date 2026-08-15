import json
import logging
import shutil
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Union
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv
from pydantic.fields import FieldInfo

from mcp.server import FastMCP
from mcp.types import TextContent
from pydantic import Field, BaseModel

from base import ActionResponse

load_dotenv()
workspace = Path.home()

default_timeout = 60 * 3  # 3 minutes timeout
max_file_size = 1024 * 1024 * 1024  # 1GB limit
supported_schemes = {"http", "https"}
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class DownloadResult(BaseModel):
    """Individual download operation result with structured data."""

    url: str
    file_path: str
    success: bool
    file_size: int | None = None
    duration: str
    timestamp: str
    error_message: str | None = None


class DownloadMetadata(BaseModel):
    """Metadata for download operation results."""

    url: str
    output_path: str
    timeout_seconds: int
    overwrite_enabled: bool
    execution_time: float | None = None
    file_size_bytes: int | None = None
    content_type: str | None = None
    status_code: int | None = None
    error_type: str | None = None
    headers_used: bool = False


mcp = FastMCP(
    "download-server",
    instructions="""
MCP service for file download operations with comprehensive controls.

    Provides secure file download capabilities including:
    - HTTP/HTTPS URL support
    - Configurable timeout controls
    - Custom headers for authentication
    - Path validation and directory creation
    - LLM-friendly result formatting
    - Error handling and logging
""",
)


@mcp.tool(
    description="""
Download a file from a URL with comprehensive options and controls.

        This tool provides secure file download capabilities with:
        - HTTP/HTTPS URL support
        - Configurable timeout controls
        - Path validation and directory creation
        - File size limits and safety checks
        - LLM-optimized result formatting
"""
)
async def download_file(
    url: str = Field(description="HTTP/HTTPS URL of the file to download"),
    output_file_path: str = Field(
        description="Local path where the file should be saved (absolute or relative to workspace)"
    ),
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite existing files (default: False)",
    ),
    timeout: int = Field(
        default=60, description="Download timeout in seconds (default: 60)"
    ),
    output_format: str = Field(
        default="markdown", description="Output format: 'markdown', 'json', or 'text'"
    ),
) -> Union[str, TextContent]:
    if isinstance(url, FieldInfo):
        url = url.default
    if isinstance(output_file_path, FieldInfo):
        output_file_path = output_file_path.default
    if isinstance(overwrite, FieldInfo):
        overwrite = overwrite.default
    if isinstance(timeout, FieldInfo):
        timeout = timeout.default
    if isinstance(output_format, FieldInfo):
        output_format = output_format.default

    try:
        # Validate URL
        url_valid, url_error = _validate_url(url)
        if not url_valid:
            action_response = ActionResponse(
                success=False,
                message=f"Invalid URL: {url_error}",
                metadata=DownloadMetadata(
                    url=url,
                    output_path=output_file_path,
                    timeout_seconds=timeout,
                    overwrite_enabled=overwrite,
                    error_type="invalid_url",
                ).model_dump(),
            )
            return TextContent(
                type="text",
                text=json.dumps(
                    action_response.model_dump()
                ),  # Empty string instead of None
                **{"metadata": {}},  # Pass as additional fields
            )

        # Resolve output path
        output_path = _resolve_output_path(output_file_path)

        # Check if file exists and overwrite setting
        if output_path.exists() and not overwrite:
            existing_size = output_path.stat().st_size
            action_response = ActionResponse(
                success=False,
                message=f"File already exists at {output_path} ({existing_size:,} bytes) and overwrite is disabled",
                metadata=DownloadMetadata(
                    url=url,
                    output_path=str(output_path),
                    timeout_seconds=timeout,
                    overwrite_enabled=overwrite,
                    file_size_bytes=existing_size,
                    error_type="file_exists",
                ).model_dump(),
            )
            return TextContent(
                type="text",
                text=json.dumps(
                    action_response.model_dump()
                ),  # Empty string instead of None
                **{"metadata": {}},  # Pass as additional fields
            )

        # Perform download
        start_time = time.time()
        result = await _download_file_async(url, output_path, timeout, headers)
        execution_time = time.time() - start_time

        # Format output
        formatted_output = _format_download_output(result, output_format)

        # Create metadata
        metadata = DownloadMetadata(
            url=url,
            output_path=str(output_path),
            timeout_seconds=timeout,
            overwrite_enabled=overwrite,
            execution_time=execution_time,
            file_size_bytes=result.file_size,
            headers_used=headers is not None,
        )

        if not result.success:
            metadata.error_type = "download_failure"

        action_response = ActionResponse(
            success=result.success,
            message=formatted_output,
            metadata=metadata.model_dump(),
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            ),
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        error_msg = f"Failed to download file: {str(e)}"
        logging.error(f"Download error: {traceback.format_exc()}")

        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata=DownloadMetadata(
                url=url,
                output_path=output_file_path,
                timeout_seconds=timeout,
                overwrite_enabled=overwrite,
                error_type="internal_error",
            ).model_dump(),
        )
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": {}},  # Pass as additional fields
        )


@mcp.tool(
    description="""
Get information about download service capabilities and configuration."""
)
async def get_download_capabilities() -> Union[str, TextContent]:
    capabilities = {
        "requests_available": requests is not None,
        "supported_schemes": list(supported_schemes),
        "supported_features": [
            "HTTP/HTTPS URL downloads",
            "Configurable timeout controls",
            "Custom headers support",
            "Path validation and directory creation",
            "File size limits and safety checks",
            "Multiple output formats (markdown, json, text)",
            "LLM-optimized result formatting",
            "Comprehensive error handling",
        ],
        "supported_formats": ["markdown", "json", "text"],
        "configuration": {
            "default_timeout": default_timeout,
            "max_file_size_bytes": max_file_size,
            "workspace": str(workspace),
        },
        "safety_features": [
            "URL validation",
            "File size limits",
            "Timeout controls",
            "Path validation",
            "Overwrite protection",
            "Error handling and logging",
        ],
    }

    max_size_mb = max_file_size / (1024 * 1024)
    formatted_info = f"""# Download Service Capabilities

            ## Status
            - **Workspace:** `{workspace}`

            ## Supported Features
            {chr(10).join(f"- {feature}" for feature in capabilities["supported_features"])}

            ## Supported URL Schemes
            {chr(10).join(f"- {scheme}://" for scheme in capabilities["supported_schemes"])}

            ## Supported Output Formats
            {chr(10).join(f"- {fmt}" for fmt in capabilities["supported_formats"])}

            ## Configuration
            - **Default Timeout:** {capabilities["configuration"]["default_timeout"]} seconds
            - **Max File Size:** {max_file_size:,} bytes ({max_size_mb:.1f} MB)

            ## Safety Features
            {chr(10).join(f"- {feature}" for feature in capabilities["safety_features"])}
            """

    action_response = ActionResponse(
        success=True,
        message=formatted_info,
        metadata=capabilities,
    )
    output_dict = {
        "artifact_type": "MARKDOWN",
        "artifact_data": json.dumps(
            action_response.model_dump()
        ),
    }
    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump()),  # Empty string instead of None
        **{"metadata": output_dict},  # Pass as additional fields
    )


def _validate_url(url: str) -> tuple[bool, str | None]:
    """Validate URL format and scheme.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parsed = urlparse(url)

        if not parsed.scheme:
            return False, "URL must include a scheme (http:// or https://)"

        if parsed.scheme.lower() not in supported_schemes:
            return (
                False,
                f"Unsupported URL scheme: {parsed.scheme}. Supported: {', '.join(supported_schemes)}",
            )

        if not parsed.netloc:
            return False, "URL must include a valid domain"

        return True, None

    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def _resolve_output_path(output_path: str) -> Path:
    """Resolve and validate output file path.

    Args:
        output_path: Output file path (absolute or relative)

    Returns:
        Resolved Path object
    """
    path = Path(output_path).expanduser()

    if not path.is_absolute():
        path = workspace / path

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    return path.resolve()


def _format_download_output(
    result: DownloadResult, output_format: str = "markdown"
) -> str:
    """Format download results for LLM consumption.

    Args:
        result: Download execution result
        output_format: Format type ('markdown', 'json', 'text')

    Returns:
        Formatted string suitable for LLM consumption
    """
    if output_format == "json":
        return json.dumps(result.model_dump(), indent=2)

    elif output_format == "text":
        output_parts = [
            f"URL: {result.url}",
            f"File Path: {result.file_path}",
            f"Status: {'SUCCESS' if result.success else 'FAILED'}",
            f"Duration: {result.duration}",
            f"Timestamp: {result.timestamp}",
        ]

        if result.file_size is not None:
            output_parts.append(f"File Size: {result.file_size:,} bytes")

        if result.error_message:
            output_parts.append(f"Error: {result.error_message}")

        return "\n".join(output_parts)

    else:  # markdown (default)
        status_emoji = "✅" if result.success else "❌"

        output_parts = [
            f"# File Download {status_emoji}",
            f"**URL:** `{result.url}`",
            f"**File Path:** `{result.file_path}`",
            f"**Status:** {'SUCCESS' if result.success else 'FAILED'}",
            f"**Duration:** {result.duration}",
            f"**Timestamp:** {result.timestamp}",
        ]

        if result.file_size is not None:
            size_mb = result.file_size / (1024 * 1024)
            output_parts.append(
                f"**File Size:** {result.file_size:,} bytes ({size_mb:.2f} MB)"
            )

        if result.error_message:
            output_parts.extend(
                ["\n## Error Details", f"```\n{result.error_message}\n```"]
            )

        return "\n".join(output_parts)


async def _download_file_async(
    url: str, output_path: Path, timeout: int, headers: dict[str, str] | None
) -> DownloadResult:
    """Download file asynchronously with comprehensive error handling.

    Args:
        url: URL to download from
        output_path: Local path to save file
        timeout: Request timeout in seconds
        headers: Optional custom headers

    Returns:
        DownloadResult with execution details
    """
    start_time = datetime.now()

    try:
        logging.info(f"📥 Starting download: {url}")

        with requests.get(
            url, stream=True, timeout=timeout, headers=headers
        ) as response:
            response.raise_for_status()

            # Check content length if available
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > max_file_size:
                raise ValueError(
                    f"File too large: {content_length} bytes (max: {max_file_size})"
                )

            # Download file
            with open(output_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)

            file_size = output_path.stat().st_size
            duration = str(datetime.now() - start_time)

            logging.info(f"✅ Download completed: {file_size:,} bytes")

            return DownloadResult(
                url=url,
                file_path=str(output_path),
                success=True,
                file_size=file_size,
                duration=duration,
                timestamp=start_time.isoformat(),
            )

    except requests.exceptions.Timeout:
        duration = str(datetime.now() - start_time)
        error_msg = f"Download timed out after {timeout} seconds"
        logging.info(f"⏰ {error_msg}")

        return DownloadResult(
            url=url,
            file_path=str(output_path),
            success=False,
            duration=duration,
            timestamp=start_time.isoformat(),
            error_message=error_msg,
        )

    except requests.exceptions.RequestException as e:
        duration = str(datetime.now() - start_time)
        error_msg = f"Request failed: {str(e)}"
        logging.info(f"❌ {error_msg}")

        return DownloadResult(
            url=url,
            file_path=str(output_path),
            success=False,
            duration=duration,
            timestamp=start_time.isoformat(),
            error_message=error_msg,
        )

    except Exception as e:
        duration = str(datetime.now() - start_time)
        error_msg = f"Unexpected error: {str(e)}"
        logging.info(f"💥 {error_msg}")

        return DownloadResult(
            url=url,
            file_path=str(output_path),
            success=False,
            duration=duration,
            timestamp=start_time.isoformat(),
            error_message=error_msg,
        )


if __name__ == "__main__":
    load_dotenv(override=True)
    logging.info("Starting download-server MCP server!")
    mcp.run(transport="stdio")
