import json
import logging
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Union, Literal

import chardet
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pydantic.fields import FieldInfo
from waybackpy import WaybackMachineCDXServerAPI

from mcp.server import FastMCP
from mcp.types import TextContent
from pydantic import Field, BaseModel

from base import ActionResponse

load_dotenv()
workspace = Path.home()
user_agent = "AWorld/1.0"
default_timeout = 30
max_content_length = 8192


class ArchivedVersion(BaseModel):
    """Individual archived version with structured data."""

    timestamp: str
    url: str
    status_code: str
    digest: str
    length: str
    mime_type: str


class WaybackMetadata(BaseModel):
    """Metadata for Wayback Machine operation results."""

    url: str
    operation: str  # 'list_versions', 'get_content', 'save_page'
    timestamp: str | None = None
    total_versions: int | None = None
    date_range: dict[str, str | None] | None = None
    content_length: int | None = None
    text_extracted: bool = False
    truncated: bool = False
    execution_time: float | None = None
    error_type: str | None = None
    user_agent: str = (
        "AWorld/1.0 (https://github.com/inclusionAI/AWorld; qintong.wqt@antgroup.com)"
    )


mcp = FastMCP(
    "wayback-server",
    instructions="""
MCP service for Wayback Machine operations.

    Provides comprehensive Wayback Machine functionality including:
    - Listing archived versions of URLs with flexible filtering
    - Fetching content from specific archived snapshots
    - LLM-friendly content formatting and text extraction
    - Robust error handling and detailed logging
    - Multiple output formats (markdown, JSON, text)
""",
)


@mcp.tool(
    description="""
List available archived versions of a URL from the Wayback Machine.

        This function queries the Wayback Machine CDX API to retrieve all available
        archived snapshots for a given URL, with optional date range filtering.
"""
)
async def list_archived_versions(
    url: str = Field(
        description="The URL of the website to check for archived versions"
    ),
    limit: int = Field(
        default=10, description="Maximum number of versions to return (0 for all)"
    ),
    from_date: str | None = Field(
        default=None, description="Start date filter (YYYYMMDDhhmmss)"
    ),
    to_date: str | None = Field(
        default=None, description="End date filter (YYYYMMDDhhmmss)"
    ),
    output_format: str = Field(
        default="markdown", description="Output format: 'markdown', 'json', or 'text'"
    ),
) -> Union[str, TextContent]:
    start_time = time.time()

    # Handle FieldInfo objects
    if isinstance(url, FieldInfo):
        url = url.default
    if isinstance(limit, FieldInfo):
        limit = limit.default
    if isinstance(from_date, FieldInfo):
        from_date = from_date.default
    if isinstance(to_date, FieldInfo):
        to_date = to_date.default
    if isinstance(output_format, FieldInfo):
        output_format = output_format.default

    try:
        # Validate parameters
        url, _ = _validate_wayback_parameters(url)

        logging.info(f"Listing archived versions for: {url}")

        # Query Wayback Machine CDX API
        cdx_api = WaybackMachineCDXServerAPI(url, user_agent=user_agent)
        all_snapshots = list(cdx_api.snapshots())

        # Apply date filtering
        if from_date or to_date:
            snapshots = [
                s
                for s in all_snapshots
                if (not from_date or s.timestamp >= from_date)
                and (not to_date or s.timestamp <= to_date)
            ]
        else:
            snapshots = all_snapshots

        if not snapshots:
            action_response = ActionResponse(
                success=False,
                message="No archived versions found for the specified URL and date range.",
                metadata=WaybackMetadata(
                    url=url,
                    operation="list_versions",
                    total_versions=0,
                    date_range={"from_date": from_date, "to_date": to_date},
                    execution_time=time.time() - start_time,
                    error_type="no_results",
                ).model_dump(),
            )
            return TextContent(
                type="text",
                text=json.dumps(
                    action_response.model_dump()
                ),  # Empty string instead of None
                **{"metadata": {}},  # Pass as additional fields
            )

        # Convert to structured format
        versions = [
            ArchivedVersion(
                timestamp=snapshot.timestamp,
                url=snapshot.archive_url,
                status_code=snapshot.statuscode,
                digest=snapshot.digest,
                length=snapshot.length,
                mime_type=snapshot.mimetype,
            )
            for snapshot in snapshots
        ]

        # Apply limit
        if limit > 0 and len(versions) > limit:
            versions = versions[:limit]

        # Format output
        query_info = {
            "url": url,
            "from_date": from_date,
            "to_date": to_date,
            "total_found": len(snapshots),
        }

        if output_format == "json":
            message = [version.model_dump() for version in versions]
        else:
            message = _format_versions_for_llm(versions, query_info)

        execution_time = time.time() - start_time
        logging.info(
            f"Found {len(versions)} archived versions in {execution_time:.2f}s"
        )

        action_response = ActionResponse(
            success=True,
            message=message,
            metadata=WaybackMetadata(
                url=url,
                operation="list_versions",
                total_versions=len(snapshots),
                date_range={"from_date": from_date, "to_date": to_date},
                execution_time=execution_time,
            ).model_dump(),
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        error_msg = f"Failed to list archived versions: {str(e)}"
        logging.info(error_msg)
        logging.error(f"Error in mcp_list_archived_versions: {traceback.format_exc()}")

        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata=WaybackMetadata(
                url=url or "unknown",
                operation="list_versions",
                execution_time=time.time() - start_time,
                error_type=type(e).__name__,
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
Fetch content from a specific archived page version.

        This function retrieves the content of a specific archived snapshot from the
        Wayback Machine, with options for text extraction and content truncation.
"""
)
async def get_archived_content(
    url: str = Field(
        description="The URL of the website to fetch archived content from"
    ),
    timestamp: str = Field(
        description="The timestamp of the desired version (YYYYMMDDhhmmss)"
    ),
    extract_text_only: bool = Field(
        default=True, description="Extract only text content, removing HTML tags"
    ),
    truncate_content: bool = Field(
        default=False, description="Truncate content to manageable length for LLMs"
    ),
    output_format: str = Field(
        default="markdown", description="Output format: 'markdown', 'json', or 'text'"
    ),
) -> Union[str, TextContent]:
    start_time = time.time()

    # Handle FieldInfo objects
    if isinstance(url, FieldInfo):
        url = url.default
    if isinstance(timestamp, FieldInfo):
        timestamp = timestamp.default
    if isinstance(extract_text_only, FieldInfo):
        extract_text_only = extract_text_only.default
    if isinstance(truncate_content, FieldInfo):
        truncate_content = truncate_content.default
    if isinstance(output_format, FieldInfo):
        output_format = output_format.default

    try:
        # Validate parameters
        url, timestamp = _validate_wayback_parameters(url, timestamp)

        logging.info(f"Fetching archived content: {url} at {timestamp}")

        # Query Wayback Machine for closest snapshot
        cdx_api = WaybackMachineCDXServerAPI(url, user_agent=user_agent)
        snapshot = cdx_api.near(wayback_machine_timestamp=timestamp)

        if not snapshot or not snapshot.archive_url:
            action_response = ActionResponse(
                success=False,
                message=f"No archived version found for {url} at timestamp {timestamp}",
                metadata=WaybackMetadata(
                    url=url,
                    operation="get_content",
                    timestamp=timestamp,
                    execution_time=time.time() - start_time,
                    error_type="no_snapshot",
                ).model_dump(),
            )
            return TextContent(
                type="text",
                text=json.dumps(
                    action_response.model_dump()
                ),  # Empty string instead of None
                **{"metadata": {}},  # Pass as additional fields
            )

        # Fetch content
        response = requests.get(snapshot.archive_url, timeout=default_timeout)
        response.raise_for_status()
        content = response.text
        original_length = len(content)

        # Extract text if requested
        if extract_text_only:
            soup = BeautifulSoup(content, "html.parser")
            content = soup.get_text(separator=" ", strip=True)

        # Truncate if requested
        truncated = False
        if truncate_content and len(content) > max_content_length:
            content = content[:max_content_length] + "..."
            truncated = True

        # Prepare content data
        content_data = {
            "url": url,
            "timestamp": timestamp,
            "fetched_timestamp": snapshot.timestamp,
            "content": content,
            "original_content_length": original_length,
            "truncated": truncated,
            "extract_text_only": extract_text_only,
        }

        # Format output
        if output_format == "json":
            message = content_data
        elif output_format == "text":
            message = content
        else:  # markdown
            message = _format_content_for_llm(content_data, output_format)

        execution_time = time.time() - start_time
        logging.info(f"Retrieved {len(content):,} characters in {execution_time:.2f}s")

        action_response = ActionResponse(
            success=True,
            message=message,
            metadata=WaybackMetadata(
                url=url,
                operation="get_content",
                timestamp=snapshot.timestamp,
                content_length=len(content),
                text_extracted=extract_text_only,
                truncated=truncated,
                execution_time=execution_time,
            ).model_dump(),
        )
        output_dict = {
            "artifact_type": "MARKDOWN",
            "artifact_data": json.dumps(
                action_response.model_dump()
            )
        }
        return TextContent(
            type="text",
            text=json.dumps(
                action_response.model_dump()
            ),  # Empty string instead of None
            **{"metadata": output_dict},  # Pass as additional fields
        )

    except Exception as e:
        error_msg = f"Failed to fetch archived content: {str(e)}"
        logging.info(error_msg)
        logging.error(f"Error in mcp_get_archived_content: {traceback.format_exc()}")

        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata=WaybackMetadata(
                url=url or "unknown",
                operation="get_content",
                timestamp=timestamp or "unknown",
                execution_time=time.time() - start_time,
                error_type=type(e).__name__,
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
Get Wayback Machine service capabilities and configuration.
"""
)
async def get_wayback_capabilities() -> Union[str, TextContent]:
    capabilities = {
        "service": "Wayback Machine MCP Server",
        "version": "1.0.0",
        "description": "Interact with the Internet Archive's Wayback Machine",
        "operations": {
            "list_versions": "List archived versions of URLs with date filtering",
            "get_content": "Fetch content from specific archived snapshots",
        },
        "features": {
            "date_filtering": True,
            "text_extraction": True,
            "content_truncation": True,
            "multiple_formats": ["markdown", "json", "text"],
            "error_handling": True,
            "logging": True,
        },
        "configuration": {
            "user_agent": user_agent,
            "default_timeout": default_timeout,
            "max_content_length": max_content_length,
        },
        "limits": {
            "max_content_length": max_content_length,
            "request_timeout": default_timeout,
        },
    }

    message = f"""# Wayback Machine Service Capabilities

            ## Service Information
            - **Service:** {capabilities["service"]}
            - **Version:** {capabilities["version"]}
            - **Description:** {capabilities["description"]}

            ## Available Operations
            - **List Versions:** {capabilities["operations"]["list_versions"]}
            - **Get Content:** {capabilities["operations"]["get_content"]}
            - **Save Page:** {capabilities["operations"]["save_page"]}

            ## Features
            - **Date Filtering:** {capabilities["features"]["date_filtering"]}
            - **Text Extraction:** {capabilities["features"]["text_extraction"]}
            - **Content Truncation:** {capabilities["features"]["content_truncation"]}
            - **Output Formats:** {", ".join(capabilities["features"]["multiple_formats"])}
            - **Error Handling:** {capabilities["features"]["error_handling"]}
            - **Logging:** {capabilities["features"]["logging"]}

            ## Configuration
            - **User Agent:** {capabilities["configuration"]["user_agent"]}
            - **Default Timeout:** {capabilities["configuration"]["default_timeout"]} seconds
            - **Max Content Length:** {capabilities["configuration"]["max_content_length"]:,} characters

            ## Limits
            - **Max Content Length:** {capabilities["limits"]["max_content_length"]:,} characters
            - **Request Timeout:** {capabilities["limits"]["request_timeout"]} seconds
            """

    action_response = ActionResponse(
        success=True, message=message, metadata=capabilities
    )
    output_dict = {
        "artifact_type": "MARKDOWN",
        "artifact_data": json.dumps(
            action_response.model_dump()
        )
    }
    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump()),  # Empty string instead of None
        **{"metadata": output_dict},  # Pass as additional fields
    )


def _format_versions_for_llm(versions: list[ArchivedVersion], query_info: dict) -> str:
    """Format archived versions list for LLM consumption.

    Args:
        versions: List of archived versions
        query_info: Query information including URL and filters

    Returns:
        Formatted string suitable for LLM consumption
    """
    if not versions:
        return f"No archived versions found for URL: {query_info.get('url', 'Unknown')}"

    output_parts = [
        f"# Wayback Machine Archives for {query_info.get('url', 'Unknown')}",
        f"\nFound **{len(versions)}** archived versions",
    ]

    if query_info.get("from_date") or query_info.get("to_date"):
        date_filter = []
        if query_info.get("from_date"):
            date_filter.append(f"From: {query_info['from_date']}")
        if query_info.get("to_date"):
            date_filter.append(f"To: {query_info['to_date']}")
        output_parts.append(f"\n**Date Filter:** {' | '.join(date_filter)}")

    output_parts.append("\n## Available Versions:")

    for i, version in enumerate(versions[:10], 1):  # Show first 10
        timestamp_formatted = _format_timestamp(version.timestamp)
        output_parts.append(
            f"\n{i}. **{timestamp_formatted}**\n"
            f"   - Archive URL: {version.url}\n"
            f"   - Status: {version.status_code} | Size: {version.length} bytes\n"
            f"   - Type: {version.mime_type}"
        )

    if len(versions) > 10:
        output_parts.append(f"\n... and {len(versions) - 10} more versions")

    return "\n".join(output_parts)


def _format_content_for_llm(content_data: dict, output_format: str = "markdown") -> str:
    """Format archived content for LLM consumption.

    Args:
        content_data: Content data dictionary
        output_format: Format type ('markdown', 'json', 'text')

    Returns:
        Formatted string suitable for LLM consumption
    """
    if output_format == "json":
        return json.dumps(content_data, indent=2)

    elif output_format == "text":
        return content_data.get("content", "")

    else:  # markdown (default)
        output_parts = [
            f"# Archived Content from {content_data.get('url', 'Unknown')}",
            f"\n**Requested Timestamp:** {content_data.get('timestamp', 'Unknown')}",
            f"**Actual Timestamp:** {_format_timestamp(content_data.get('fetched_timestamp', ''))}",
            f"**Content Length:** {content_data.get('original_content_length', 0):,} characters",
        ]

        if content_data.get("truncated"):
            output_parts.append(
                f"**Note:** Content truncated to {max_content_length:,} characters"
            )

        if content_data.get("extract_text_only"):
            output_parts.append("**Note:** Text-only extraction applied")

        output_parts.extend(
            ["\n## Content:", "\n---\n", content_data.get("content", ""), "\n---"]
        )

        return "\n".join(output_parts)


def _format_timestamp(timestamp: str) -> str:
    """Format Wayback Machine timestamp to human-readable format.

    Args:
        timestamp: Wayback timestamp (YYYYMMDDhhmmss)

    Returns:
        Human-readable timestamp
    """
    try:
        if len(timestamp) >= 14:
            dt = datetime.strptime(timestamp[:14], "%Y%m%d%H%M%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        return timestamp
    except (ValueError, TypeError):
        return timestamp or "Unknown"


def _validate_wayback_parameters(
    url: str, timestamp: str = None
) -> tuple[str, str | None]:
    """Validate and normalize Wayback Machine parameters.

    Args:
        url: URL to validate
        timestamp: Optional timestamp to validate

    Returns:
        Tuple of (validated_url, validated_timestamp)

    Raises:
        ValueError: If parameters are invalid
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    validated_timestamp = None
    if timestamp:
        timestamp = timestamp.strip()
        if len(timestamp) < 8:
            raise ValueError("Timestamp must be at least 8 characters (YYYYMMDD)")
        validated_timestamp = timestamp

    return url, validated_timestamp


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(override=True)
    logging.info("Starting wayback-server MCP server!")
    mcp.run(transport="stdio")
