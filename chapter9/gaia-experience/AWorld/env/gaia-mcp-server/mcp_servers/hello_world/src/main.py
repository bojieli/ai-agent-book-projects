from mcp.server.fastmcp import FastMCP
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

mcp = FastMCP(name="hello-world", log_level="DEBUG")


@mcp.tool()
async def hello_world(name: str) -> str:
    """
    Say hello to the world.
    """
    return f"Hello, {name}!"


if __name__ == "__main__":
    logger.info("Starting hello-world MCP server!")
    mcp.run(transport="stdio")
