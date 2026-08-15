"""
Streamable HTTP MCP Service Proxy

A gateway service that forwards MCP requests to bound backend MCP services
with persistent HTTP connections. Implements the streamable HTTP protocol
for Model Context Protocol (MCP) communication.
"""

import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException

from .utils.common_utils import get_remote_addr, get_mcp_operation
from .auth import check_auth
from .mcp_gateway import MCPGateway

from .routers import gateway_api, novnc_proxy_pass, dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown events"""
    # Initialize gateway
    gateway = MCPGateway()
    await gateway.startup()
    app.state.gateway = gateway
    try:
        yield
    finally:
        # Shutdown
        await gateway.shutdown()


# FastAPI application setup with lifespan
app = FastAPI(
    title="MCP",
    description="MCP Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


@app.api_route("/mcp", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def mcp_proxy(request: Request):
    """
    Main MCP proxy endpoint.
    Accepts all HTTP methods and forwards them to backend MCP servers.
    """
    if not check_auth.check_auth(request):
        logger.warning(
            f"MCP Request unauthorized! remote.addr={get_remote_addr(request)}, request.headers={request.headers}"
        )
        return Response(status_code=401, content="Unauthorized")

    try:
        gateway: MCPGateway = request.app.state.gateway
        return await gateway.handle_mcp_request(request)
    except Exception as e:
        logger.error(
            f"Request error: remote.addr={get_remote_addr(request)}, request.headers={request.headers}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error, {e}")


# NoVNC proxy pass
app.include_router(novnc_proxy_pass.router, prefix="/novnc")

# Gateway rest api
app.include_router(gateway_api.router, prefix="/api")

# Gateway dashboard
app.include_router(dashboard.router, prefix="/dashboard")


@app.get("/health")
async def health(request: Request):
    return {"status": "success", "message": "MCP Gateway is healthy"}


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
