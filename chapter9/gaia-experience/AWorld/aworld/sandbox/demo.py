import asyncio

from aworld.sandbox import Sandbox, SandboxEnvType


# Define an asynchronous function to call asynchronous methods
async def run_async_tasks(sand_box):
    tools = await sand_box.mcpservers.list_tools()
    print(f"Tools: {tools}")
    return tools

if __name__ == "__main__":
    # 只使用memory服务器
    mcp_servers = ["memory","amap-amap-sse"]
    mcp_config = {
      "mcpServers": {
        "memory": {
          "type": "stdio",
          "command": "npx",
          "args": [
            "-y",
            "@modelcontextprotocol/server-memory"
          ]
        }

      }
    }
    sand_box = Sandbox(mcp_servers=mcp_servers, mcp_config=mcp_config,env_type=SandboxEnvType.SUPERCOMPUTER)
    print(f"Sandbox ID: {sand_box.sandbox_id}")
    print(f"Status: {sand_box.status}")
    print(f"Timeout: {sand_box.timeout}")
    print(f"Metadata: {sand_box.metadata}")
    print(f"Environment Type: {sand_box.env_type}")
    print(f"MCP Servers: {sand_box.mcp_servers}")
    print(f"MCP Config: {sand_box.mcp_config}")
    
    # Use asyncio to run asynchronous methods
    asyncio.run(run_async_tasks(sand_box))
    
    print(f"MCP Servers-new: {sand_box.mcp_servers}")
    print(f"MCP Config-new: {sand_box.mcp_config}")
