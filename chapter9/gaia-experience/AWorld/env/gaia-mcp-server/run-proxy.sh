#!/bin/sh
cd "$(dirname "$0")"

export MCP_SERVERS_PATH="$(pwd)/mcp_servers"

sh mcp_servers/init_env.sh && \

sh -c "cd ../virtualpc-mcp/mcp_server/mcp_server_proxy && uv run -m mcp_server_proxy.main"