"""
Download MCP Server

This module provides MCP server functionality for downloading files from URLs.
It handles various download scenarios with proper validation, error handling,
and progress tracking.

Key features:
- File downloading from HTTP/HTTPS URLs
- Download progress tracking
- File validation
- Safe file saving

Main functions:
- mcpdownload: Downloads files from URLs to local filesystem
"""

import os
import sys
import traceback
import urllib.parse
from pathlib import Path
from typing import List, Optional

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from aworld.logs.util import logger

mcp = FastMCP("download-server")


class DownloadResult(BaseModel):
    """Download result model with file information"""

    file_path: str
    file_name: str
    file_size: int
    content_type: Optional[str] = None
    success: bool
    error: Optional[str] = None


class DownloadResults(BaseModel):
    """Download results model for multiple files"""

    results: List[DownloadResult]
    success_count: int
    failed_count: int


@mcp.tool(description="Download files from URLs and save to the local filesystem.")
def mcpdownloadfiles(
    urls: List[str] = Field(
        ..., description="The URLs of the files to download. Must be a list of URLs."
    ),
    output_dir: str = Field(
        "/tmp/mcp_downloads",
        description="Directory to save the downloaded files (default: /tmp/mcp_downloads).",
    ),
    timeout: int = Field(60, description="Download timeout in seconds (default: 60)."),
) -> str:
    """Download files from URLs and save to the local filesystem.

    Args:
        urls: The URLs of the files to download, must be a list of URLs
        output_dir: Directory to save the downloaded files
        timeout: Download timeout in seconds

    Returns:
        JSON string with download results information
    """
    results = []
    success_count = 0
    failed_count = 0

    for single_url in urls:
        result_json = _download_single_file(single_url, output_dir, "", timeout)
        result = DownloadResult.model_validate_json(result_json)
        results.append(result)

        if result.success:
            success_count += 1
        else:
            failed_count += 1

    batch_results = DownloadResults(
        results=results, success_count=success_count, failed_count=failed_count
    )

    return batch_results.model_dump_json()


def _download_single_file(
    url: str, output_dir: str, filename: str, timeout: int
) -> str:
    """Download a single file from URL and save it to the local filesystem."""
    try:
        # Validate URL
        if not url.startswith(("http://", "https://")):
            raise ValueError(
                "Invalid URL format. URL must start with http:// or https://"
            )

        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Determine filename if not provided
        if not filename:
            filename = os.path.basename(urllib.parse.urlparse(url).path)
            if not filename:
                filename = "downloaded_file"

        # Full path to save the file
        file_path = os.path.join(output_path, filename)

        logger.info(f"Downloading file from {url} to {file_path}")
        # Download the file with progress tracking
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AWorld/1.0 (https://github.com/inclusionAI/AWorld; qintong.wqt@antgroup.com) "
                "Python/requests "
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml,application/pdf;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        response = requests.get(url, headers=headers, stream=True, timeout=timeout)
        response.raise_for_status()

        # Get content type and size
        content_type = response.headers.get("Content-Type")

        # Save the file
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Get actual file size
        actual_size = os.path.getsize(file_path)

        logger.info(f"File downloaded successfully to {file_path}")

        # Create result
        result = DownloadResult(
            file_path=file_path,
            file_name=filename,
            file_size=actual_size,
            content_type=content_type,
            success=True,
            error=None,
        )

        return result.model_dump_json()

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Download error: {traceback.format_exc()}")

        result = DownloadResult(
            file_path="",
            file_name="",
            file_size=0,
            content_type=None,
            success=False,
            error=error_msg,
        )

        return result.model_dump_json()


def main():
    load_dotenv()

    print("Starting Download MCP Server...", file=sys.stderr)
    mcp.run(transport="stdio")


# Make the module callable
def __call__():
    """
    Make the module callable for uvx.
    This function is called when the module is executed directly.
    """
    main()


sys.modules[__name__].__call__ = __call__

# Run the server when the script is executed directly
if __name__ == "__main__":
    main()
