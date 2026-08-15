import logging
from fastapi.responses import StreamingResponse
import httpx

logger = logging.getLogger(__name__)


async def proxy_pass_lines(
    client: httpx.AsyncClient, method: str, url: str, headers: dict, content: bytes
) -> StreamingResponse:
    stream_response_context = client.stream(
        method=method,
        url=url,
        headers=headers,
        content=content,
    )

    stream_response = await stream_response_context.__aenter__()

    content_type = stream_response.headers.get("content-type", "")
    response_headers = dict(stream_response.headers)
    status_code = stream_response.status_code

    async def stream_lines():
        try:
            async for line in stream_response.aiter_lines():
                yield f"{line}\n"
        finally:
            await stream_response_context.__aexit__(None, None, None)
            await client.__aexit__(None, None, None)

    return StreamingResponse(
        content=stream_lines(),
        status_code=status_code,
        headers=response_headers,
        media_type=content_type,
    )


async def proxy_pass_bytes(
    client: httpx.AsyncClient, method: str, url: str, headers: dict, content: bytes
) -> StreamingResponse:
    stream_response_context = client.stream(
        method=method,
        url=url,
        headers=headers,
        content=content,
    )

    stream_response = await stream_response_context.__aenter__()

    content_type = stream_response.headers.get("content-type", "")
    response_headers = dict(stream_response.headers)
    status_code = stream_response.status_code

    async def stream_bytes():
        try:
            async for chunk in stream_response.aiter_raw(chunk_size=1024):
                yield chunk
        finally:
            await stream_response_context.__aexit__(None, None, None)

    return StreamingResponse(
        content=stream_bytes(),
        status_code=status_code,
        headers=response_headers,
        media_type=content_type,
    )
