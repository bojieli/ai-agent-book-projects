import logging
import traceback
from typing import Callable, Tuple
from fastapi import Request
import httpx

logger = logging.getLogger(__name__)


def get_remote_addr(request: Request) -> str:
    """Get the request remote address"""
    client_ip = request.client.host
    try:
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()
    except:
        logger.error(f"Failed to get request remote addr: {traceback.format_exc()}")

    return client_ip


async def get_mcp_operation(request: Request) -> Tuple[str, str | None, str | None]:
    """Get the MCP operation from the request
    Returns:
        Tuple[str, str | None, str | None]: (http_method, mcp_client_method, mcp_tool_method)
    """
    try:
        if request.method in ["GET", "DELETE"]:
            return request.method, None, None
        jsonrpc_body = await request.json()
        mcp_client_method = jsonrpc_body.get("method")
        mcp_tool_method = jsonrpc_body.get("params", {}).get("name")
        return request.method, mcp_client_method, mcp_tool_method
    except Exception as e:
        logger.warning(
            f"Failed to get mcp operation, remote.addr={get_remote_addr(request)} http_method={request.method}, {e}"
        )
        return request.method, None, None


async def check_container_server_health(ip: str, port: int) -> bool:
    """Check if the container server is healthy"""
    return await check_server_health(
        ip=ip,
        port=port,
        checker=lambda body: body["status"] == "success"
        and body["message"] == "Container server is healthy",
    )


async def check_server_health(
    ip: str,
    port: int,
    timeout: float = 3.0,
    checker: Callable[[dict], bool] = lambda body: body["status"] == "success",
) -> bool:
    """Check if the server is healthy"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"http://{ip}:{port}/health")
            response.raise_for_status()
            body = response.json()
            return checker(body)
    except Exception as e:
        logger.error(
            f"Failed to check server health: {ip}:{port}, {e}"
        )
        return False
