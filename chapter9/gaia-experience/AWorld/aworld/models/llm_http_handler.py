"""HTTP handler for LLM providers.

This module provides a generic HTTP handler for making requests to LLM providers
when direct SDK usage is not desired.
"""

import json
import asyncio
import random
import time
from typing import Any, Dict, List, Optional, Union, Generator, AsyncGenerator
import requests
from requests import HTTPError

from aworld.logs.util import logger
from aworld.utils import import_package

class LLMHTTPHandler:
    """HTTP handler for LLM providers.

    This class provides methods to make HTTP requests to LLM providers
    instead of using their SDKs directly.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 180,
        max_retries: int = 3,
    ) -> None:
        """Initialize the HTTP handler.

        Args:
            base_url: Base URL for the LLM API.
            api_key: API key for authentication.
            model_name: Name of the model to use.
            headers: Additional headers to include in requests.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
        """
        import_package("aiohttp")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries

        # Set up default headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        if headers:
            self.headers.update(headers)

    def _parse_sse_line(self, line: bytes) -> Optional[Dict[str, Any]]:
        """Parse a Server-Sent Events (SSE) line.

        Args:
            line: Raw SSE line.

        Returns:
            Parsed JSON data if successful, None otherwise.
        """
        try:
            # Remove 'data: ' prefix if present
            line_str = line.decode('utf-8').strip()
            if line_str.startswith('data: '):
                line_str = line_str[6:]

            # Skip empty lines
            if not line_str:
                return None

            return json.loads(line_str)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to parse SSE line: {line}, error: {str(e)}")
            return None

    def _make_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        stream: bool = False,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """Make a synchronous HTTP request.

        Args:
            endpoint: API endpoint to call.
            data: Request data to send.
            stream: Whether to stream the response.

        Returns:
            Response data or generator of response chunks.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)


        try:
            if stream:
                    response = requests.post(
                        url,
                        headers=request_headers,
                        json=data,
                        stream=True,
                        timeout=self.timeout,
                    )
                    response.raise_for_status()

                    def generate_chunks():
                        for line in response.iter_lines():
                            if line:
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith('data: '):
                                    line_content = line_str[6:]

                                    if line_content == "[DONE]":
                                        yield {"status": "done", "message": "Stream completed"}
                                        break
                                    elif line_content == "[REVOKE]":
                                        yield {"status": "revoke", "message": "Content should be revoked"}
                                        continue
                                    elif line_content == "[FAIL]":
                                        yield {"status": "fail", "message": "Request failed"}
                                        break
                                    elif line_content.startswith("[FAIL]_stream was reset: CANCEL"):
                                        yield {"status": "cancel", "message": "Stream was cancelled"}
                                        break

                                chunk = self._parse_sse_line(line)
                                if chunk is not None:
                                    yield chunk
                    return generate_chunks()
            else:
                response = requests.post(
                    url,
                    headers=request_headers,
                    json=data,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error in HttpHandler: {str(e)}")
            raise

    async def _make_async_request_stream(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Make an asynchronous streaming HTTP request.

        Args:
            endpoint: API endpoint to call.
            data: Request data to send.

        Yields:
            Response chunks.

        Raises:
            aiohttp.ClientError: If the request fails.
        """
        import aiohttp
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        # Create an independent session and keep it open
        session = aiohttp.ClientSession()
        try:
            response = await session.post(
                url,
                headers=request_headers,
                json=data,
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Implement async generator directly
            async for line in response.content:
                if line:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        line_content = line_str[6:]

                        if line_content == "[DONE]":
                            yield {"status": "done", "message": "Stream completed"}
                            break
                        elif line_content == "[REVOKE]":
                            yield {"status": "revoke", "message": "Content should be revoked"}
                            continue
                        elif line_content == "[FAIL]":
                            yield {"status": "fail", "message": "Request failed"}
                            break
                        elif line_content.startswith("[FAIL]_stream was reset: CANCEL"):
                            yield {"status": "cancel", "message": "Stream was cancelled"}
                            break

                    chunk = self._parse_sse_line(line)
                    if chunk is not None:
                        yield chunk
        except Exception as e:
            logger.error(f"Error in stream: {str(e)}")
            raise
        finally:
            # Ensure the session is eventually closed
            await session.close()

    async def _make_async_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an asynchronous non-streaming HTTP request.

        Args:
            endpoint: API endpoint to call.
            data: Request data to send.

        Returns:
            Response data.

        Raises:
            aiohttp.ClientError: If the request fails.
        """
        import aiohttp
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=request_headers,
                json=data,
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                return await response.json()

    def sync_call(
        self,
        data: Dict[str, Any],
        endpoint: str = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a synchronous completion request.

        Args:
            data: Request data.

        Returns:
            Response data.
        """
        logger.debug(f"sync_call request data: {data}")

        if not endpoint:
            endpoint = "chat/completions"

        retries = 0
        while retries < self.max_retries:
            try:
                response = self._make_request(endpoint, data, headers=headers)
                return response
            except Exception as e:
                last_error = e
                retries += 1
                if retries < self.max_retries:
                    logger.warning(f"Request failed, retrying ({retries}/{self.max_retries}): {str(e)}")
                    # Exponential backoff with jitter
                    backoff = min(2 ** retries + random.uniform(0, 1), 10)
                    time.sleep(backoff)
                else:
                    logger.error(f"Request failed after {self.max_retries} retries: {str(e)}")
                    raise last_error

    async def async_call(
        self,
        data: Dict[str, Any],
        endpoint: str = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an asynchronous completion request.

        Args:
            data: Request data.

        Returns:
            Response data.
        """
        import aiohttp
        logger.info(f"async_call request data: {data}")

        retries = 0
        last_error = None
        if not endpoint:
            endpoint = "chat/completions"

        while retries < self.max_retries:
            try:
                response = await self._make_async_request(endpoint, data, headers=headers)
                return response
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                retries += 1
                if retries < self.max_retries:
                    logger.warning(f"Request failed, retrying ({retries}/{self.max_retries}): {str(e)}")
                    # Exponential backoff with jitter
                    backoff = min(2 ** retries + random.uniform(0, 1), 10)
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Request failed after {self.max_retries} retries: {str(e)}")
                    raise last_error

    def sync_stream_call(
        self,
        data: Dict[str, Any],
        endpoint: str = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Make a synchronous streaming completion request.

        Args:
            data: Request data.

        Yields:
            Response chunks.
        """
        data["stream"] = True
        logger.info(f"sync_stream_call request data: {data}")
        retries = 0

        while retries < self.max_retries:
            try:
                for chunk in self._make_request(endpoint or "chat/completions", data, stream=True, headers=headers):
                    yield chunk
                return  # Exit after completing stream processing
            except Exception as e:
                last_error = e
                retries += 1
                if retries < self.max_retries:
                    logger.warning(f"Stream connection failed, retrying ({retries}/{self.max_retries}): {str(e)}")
                else:
                    logger.error(f"Stream connection failed after {self.max_retries} retries: {str(e)}")
                    raise last_error


    async def async_stream_call(
        self,
        data: Dict[str, Any],
        endpoint: str = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Make an asynchronous streaming completion request.

        Args:
            data: Request data.

        Yields:
            Response chunks.
        """
        import aiohttp
        data["stream"] = True
        logger.info(f"async_stream_call request data: {data}")

        retries = 0
        last_error = None

        while retries < self.max_retries:
            try:
                async for chunk in self._make_async_request_stream(endpoint or "chat/completions", data, headers=headers):
                    yield chunk
                return  # Exit after completing stream processing
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                retries += 1
                if retries < self.max_retries:
                    logger.warning(f"Stream connection failed, retrying ({retries}/{self.max_retries}): {str(e)}")
                    await asyncio.sleep(1)  # Wait one second before retrying
                else:
                    logger.error(f"Stream connection failed after {self.max_retries} retries: {str(e)}")
                    raise last_error
