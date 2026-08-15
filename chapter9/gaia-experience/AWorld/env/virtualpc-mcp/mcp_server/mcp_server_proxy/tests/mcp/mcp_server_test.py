import asyncio
import json
import logging
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mcp_client import mcp_client, progress_callback
from core.test_data import tool_test_cases

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

load_dotenv()

read_arg = lambda e: (os.getenv(f"URL_{e}"), os.getenv(f"TOKEN_{e}"))

url, token = read_arg("REMOTE")
# url, token = read_arg("GW_DEBUG")
# url, token = read_arg("MCP_DEBUG")

async def main():
    async for session in mcp_client(url, token):
        ls = await session.list_tools()
        assert ls and ls.tools, "list_tools return null"
        tools = ls.tools
        logger.info(f"list_tools return:\n  - {'\n  - '.join([t.name for t in tools])}")
        t = tools[0]
        assert t.name, "tool.name is null"
        assert t.inputSchema, "tool.inputSchema is null"
        assert t.outputSchema, "tool.outputSchema is null"
        
        for t in tool_test_cases:
            tool_name = t["tool_name"]
            args = t["args"]
            logger.info(f"call tool: {tool_name}")
            result = await session.call_tool(tool_name, args, progress_callback=progress_callback)
            logger.info(f"tool result: {result.content[0].text[:300]}")
            
        input("Press Enter to continue...")

if __name__ == "__main__":
    asyncio.run(main())
