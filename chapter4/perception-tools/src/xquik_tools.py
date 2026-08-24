"""Read-only X post search through the public Xquik REST API."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from base import ActionResponse
from mcp.types import TextContent

XQUIK_SEARCH_URL = "https://xquik.com/api/v1/x/tweets/search"
XQUIK_CONTRACT = "2026-04-29"


def _text_response(*, success: bool, message: Any, metadata: dict[str, Any]) -> TextContent:
    response = ActionResponse(success=success, message=message, metadata=metadata)
    return TextContent(
        type="text",
        text=json.dumps(response.model_dump(), ensure_ascii=False),
    )


def _failure(
    message: str,
    error_type: str,
    *,
    status_code: int | None = None,
    error_code: str | None = None,
    retry_after: str | None = None,
) -> TextContent:
    metadata: dict[str, Any] = {
        "provider": "Xquik",
        "error_type": error_type,
        "metered": True,
    }
    if status_code is not None:
        metadata["status_code"] = status_code
    if error_code:
        metadata["error_code"] = error_code
    if retry_after:
        metadata["retry_after"] = retry_after
    return _text_response(success=False, message=message, metadata=metadata)


def _provider_error(payload: Any) -> tuple[str | None, str]:
    if not isinstance(payload, dict):
        return None, "Xquik returned an unsuccessful response."

    error = payload.get("error")
    if isinstance(error, dict):
        code = error.get("code") or error.get("type")
        message = error.get("message")
    else:
        code = error
        message = payload.get("message")

    return (
        str(code) if code else None,
        str(message) if message else "Xquik returned an unsuccessful response.",
    )


async def search_x_posts(
    query: str,
    limit: int = 10,
    cursor: str | None = None,
    query_type: str = "Latest",
) -> TextContent:
    """Search X posts without exposing credentials as tool arguments."""
    if not query.strip():
        return _failure("Search query cannot be empty.", "invalid_parameters")
    if not 1 <= limit <= 100:
        return _failure("Limit must be between 1 and 100.", "invalid_parameters")
    if query_type not in {"Latest", "Top"}:
        return _failure(
            "Query type must be Latest or Top.",
            "invalid_parameters",
        )

    api_key = os.getenv("XQUIK_API_KEY", "").strip()
    if not api_key:
        return _failure(
            "Xquik is not configured. Set XQUIK_API_KEY first.",
            "missing_credentials",
        )

    params: dict[str, str | int] = {
        "q": query,
        "limit": limit,
        "queryType": query_type,
    }
    if cursor:
        params["cursor"] = cursor

    headers = {
        "Accept": "application/json",
        "User-Agent": "ai-agent-book-experiment/4.1",
        "x-api-key": api_key,
        "xquik-api-contract": XQUIK_CONTRACT,
    }

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=False,
        ) as client:
            response = await client.get(
                XQUIK_SEARCH_URL,
                params=params,
                headers=headers,
            )
    except httpx.TimeoutException:
        return _failure("Xquik request timed out. Retry shortly.", "timeout")
    except httpx.RequestError:
        return _failure("Xquik request failed. Check connectivity and retry.", "api_request_failed")

    try:
        payload = response.json()
    except ValueError:
        return _failure(
            "Xquik returned invalid JSON. Retry shortly.",
            "invalid_response",
            status_code=response.status_code,
        )

    if response.status_code != 200:
        error_code, message = _provider_error(payload)
        return _failure(
            message,
            "api_request_failed",
            status_code=response.status_code,
            error_code=error_code,
            retry_after=response.headers.get("retry-after"),
        )

    if not isinstance(payload, dict) or not isinstance(payload.get("tweets"), list):
        return _failure(
            "Xquik returned an unexpected response shape. Retry shortly.",
            "invalid_response",
            status_code=response.status_code,
        )

    has_next_page = payload.get("has_next_page", False)
    next_cursor = payload.get("next_cursor")
    if not isinstance(has_next_page, bool) or not (
        next_cursor is None or isinstance(next_cursor, str)
    ):
        return _failure(
            "Xquik returned invalid pagination fields. Retry shortly.",
            "invalid_response",
            status_code=response.status_code,
        )

    tweets = payload["tweets"]
    return _text_response(
        success=True,
        message={
            "query": query,
            "tweets": tweets,
            "count": len(tweets),
            "has_next_page": has_next_page,
            "next_cursor": next_cursor,
        },
        metadata={
            "provider": "Xquik",
            "status_code": response.status_code,
            "metered": True,
            "content_is_untrusted": True,
        },
    )
