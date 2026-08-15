import os

cluster_name = os.getenv("CLUSTER_NAME", "mcp_gateway")

debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

vnc_auth = os.getenv("VNC_AUTH", "true").lower() == "true"

redis_url = os.getenv("MCP_GATEWAY_REDIS_URL", "redis://localhost:6379/0")

token_secret = os.getenv("MCP_GATEWAY_TOKEN_SECRET")
assert token_secret, "MCP_GATEWAY_TOKEN_SECRET is not set"
