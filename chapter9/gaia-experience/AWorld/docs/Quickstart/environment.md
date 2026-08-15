# Environment

Mainly providing MCP servers in an independent environment to support high concurrency applications of MCP servers.

## Add MCP Servers

If you only use the built-in MCP servers, you only need to deploy them.

If there is a new MCP server and you want to use it independently, you can use the same directory structure
as [gaia-mcp-server](../../env/gaia-mcp-server), and refer to the code structure and implementation of
[hello_world](../../env/gaia-mcp-server/mcp_servers/hello_world).

```
your_mcp_server/
  .dockerignore
  Dockfile
  mcp_servers/
    .env
    .gitignore
    mcp_config.py
    build_mcp_tool_schema.py
    init_env.sh
    your_tool/
      src/
      .python-version
      pyproject.toml
```

The `mcp_config` variable in `mcp_config.py` is a standard MCP configuration structure.

Before deployment, it is necessary to run `build_mcp_tool_schema.py` to generate `mcp_tool_schema.json`.

`.env` is the environment configuration file for MCP servers.

## Depolyment

### Local Docker Deployment

#### Prerequisites

Ensure Docker and Docker Compose are properly installed and operational:

```bash
# Verify Docker installation
docker --version
docker compose --version

# Verify Docker daemon is running
docker ps
docker compose ps
```

**Step 1: Launch VirtualPC MCP Server**

```bash
sh run-docker.sh
```

Monitor the terminal output for any errors during startup.

**Step 2: Connect to VirtualPC MCP Server**

Use the following configuration to connect to the VirtualPC MCP Server:

```json
{
  "virtualpc-mcp-server": {
    "type": "streamable-http",
    "url": "http://localhost:8000/mcp",
    "headers": {
      "Authorization": "Bearer your token",
      "MCP_SERVERS": "readweb-server,browser-server"
    },
    "timeout": 6000,
    "sse_read_timeout": 6000,
    "client_session_timeout_seconds": 6000
  }
}
```

**Note**: The Bearer token is your own. The `MCP_SERVERS` header specifies the MCP server
scope for your current connection, which should be a subset of server names defined in
`mcp_servers/mcp_config.py`.

### Kubernetes Cluster Deployment

For production deployments and RL training scenarios, Kubernetes cluster deployment is recommended.
Detailed instructions will be provided in future updates.