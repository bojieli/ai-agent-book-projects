import json
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from .configs import mcp_servers_config_path, mcp_tool_schema_path


class MCPServerLoader:
    def __init__(self):
        pass

    def load_mcp_servers_config(self):
        mcp_config = self._load_mcp_config()
        return mcp_config.get("mcpServers", {})

    def load_mcp_tool_schema(self):
        with open(mcp_tool_schema_path, "r") as f:
            return json.load(f)

    def _load_mcp_config(self):
        path = Path(mcp_servers_config_path).resolve()
        assert path.exists(), f"MCP servers config file not found: {path}"

        spec = spec_from_file_location("mcp_servers_config", path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        mcp_config = getattr(module, "mcp_config")
        return mcp_config
