import mcp
from mcp.client.streamable_http import streamablehttp_client
import json
import base64

config = {
  "githubPersonalAccessToken": "token"
}
# Encode config in base64
config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
api_key = "fkey"

# Create server URL
url = f"https://url?config={config_b64}&api_key={api_key}"
print(url)

async def main():
    # Connect to the server using HTTP client
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            # List available tools
            tools_result = await session.list_tools()
            print(f"Available tools: {', '.join([t.name for t in tools_result.tools])}")
            result = await session.call_tool("search_code", {
                "per_page":10,
                "q": "bubble sort language:python"
            })
            print(result)
