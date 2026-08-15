import asyncio
import datetime
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from .mcp_server_proxy import MCPServerProxy


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

mcp = MCPServerProxy(
    name="MCP Server",
    stateless_http=False,
    host="0.0.0.0",
    port=4242,
    log_level="DEBUG",
)


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> Response:
    return JSONResponse(
        {
            "status": "success",
            "message": "MCP Server is healthy",
            "last_active": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f"),
        }
    )


async def main():
    logger.info("Starting MCP Server Proxy...")
    await mcp.initialize()
    await mcp.run_streamable_http_async()


if __name__ == "__main__":
    asyncio.run(main())
