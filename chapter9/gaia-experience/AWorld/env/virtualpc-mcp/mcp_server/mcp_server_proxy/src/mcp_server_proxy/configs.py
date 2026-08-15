import os
from pathlib import Path

mcp_servers_path = os.getenv(
    "MCP_SERVERS_PATH",
    str((Path(__file__).parent.parent.parent.parent / "mcp_servers").resolve()),
)

mcp_servers_config_path = os.getenv(
    "MCP_SERVERS_CONFIG_PATH", str((Path(mcp_servers_path) / "mcp_config.py").resolve())
)

mcp_tool_schema_path = os.getenv(
    "MCP_TOOL_SCHEMA_PATH",
    str((Path(mcp_servers_path) / "mcp_tool_schema.json").resolve()),
)
