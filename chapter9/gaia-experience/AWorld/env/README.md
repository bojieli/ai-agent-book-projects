<div align="center">

# VirtualPC MCP Server (Incubating)

*A unified MCP tool runtime environment based on Debian with session-level environment isolation, environment state persistence, real-time UI visualization, distributed architecture, and extensibility*

[![License: MIT][license-image]][license-url]

</div>

<div align="center">

[中文版](./README_zh.md) | [Quick Start](#quick-start) | [Development](#development) | [Contributing](#contributing)

</div>

---

## 1. Overview

VirtualPC MCP Server is a comprehensive MCP (Model Context Protocol) tool runtime environment designed to provide a unified, isolated, and scalable execution environment for AI agents. Built on Debian, it offers session-level environment isolation, persistent state management across multiple sessions, and real-time visualization capabilities.

### 1.1 Features

- **Session-Level Environment Isolation**: Each MCP session operates within its own isolated environment
- **Multi-Session State Persistence**: Maintains environment state across multiple MCP sessions
- **Real-Time UI Visualization**: Live monitoring and visualization of Agent MCP operations
- **Distributed Architecture**: Supports both local Docker and Kubernetes cluster deployments
- **Extensible Runtime**: Modular design enabling seamless integration of new MCP tool servers

## 2. Quick Start

This project supports both local Docker deployment (optimal for demos and debugging) and Kubernetes cluster deployment (recommended for production and RL training).

### 2.1 Local Docker Deployment

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

**Step 1: Configure Environment and Prepare Gaia Dataset**

1. Copy the environment template and configure your settings:

```bash
cp ./gaia-mcp-server/mcp_servers/.env_template ./gaia-mcp-server/mcp_servers/.env
```

Edit `./gaia-mcp-server/mcp_servers/.env` with your specific configuration values.

2. Download the [gaia_dataset](https://huggingface.co/datasets/gaia-benchmark/GAIA) from Hugging Face and place it in `./gaia-mcp-server/docker/gaia_dataset`

**Step 2: Launch VirtualPC MCP Server**

```bash
sh run-docker.sh
```

Monitor the terminal output for any errors during startup.

Generate a local bearer token and copy the printed value into `<local-debug-jwt>` below. If you changed `MCP_GATEWAY_TOKEN_SECRET` in `virtualpc-mcp/docker-compose.yaml`, export the same value before running this command.

```bash
python - <<'PY'
import base64, hashlib, hmac, json, os, time

def part(value):
    raw = json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

signing_input = ".".join([
    part({"alg": "HS256", "typ": "JWT"}),
    part({"app": "local_debug", "version": 1, "time": time.time()}),
])
secret = os.getenv("MCP_GATEWAY_TOKEN_SECRET", "123321").encode()
signature = hmac.new(secret, signing_input.encode(), hashlib.sha256).digest()
print(f"{signing_input}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}")
PY
```

**Step 3: Connect to VirtualPC MCP Server**

Use the following configuration to connect to the VirtualPC MCP Server:

```json
{
    "virtualpc-mcp-server": {
        "type": "streamable-http",
        "url": "http://localhost:8000/mcp",
        "headers": {
            "Authorization": "Bearer <local-debug-jwt>",
            "MCP_SERVERS": "readweb-server,browser-server"
        },
        "timeout": 6000,
        "sse_read_timeout": 6000,
        "client_session_timeout_seconds": 6000
    }
}
```

**Note**: The Bearer token above is for local testing only. The `MCP_SERVERS` header specifies the MCP server scope for your current connection, which should be a subset of server names defined in `gaia-mcp-server/mcp_servers/mcp_config.py`.

### 2.2 Kubernetes Cluster Deployment

For production deployments and RL training scenarios, Kubernetes cluster deployment is recommended. Detailed instructions will be provided in future updates.

## 3. Development

### 3.1 Adding Custom MCP Tools to VirtualPC MCP Server

**Step 1: Develop MCP Tool (Optional)**

If you need to develop a custom MCP Tool and register it with VirtualPC MCP Server, create your MCP Tool project directory under `gaia-mcp-server/mcp_servers` and implement the MCP Tool code. Refer to the [hello_world](./gaia-mcp-server/mcp_servers/hello_world/) directory for the project structure.

Project specifications:

1. Use `pyproject.toml` to manage project dependencies for Docker image building

**Step 2: Register MCP Tool**

Register your developed MCP Tool or third-party MCP Tool with VirtualPC MCP Server.

Edit the [MCP Tool registration file](./gaia-mcp-server/mcp_servers/mcp_config.py):

```python
"STDIO_SERVER_DEMO": {
    "type": "stdio",
    "command": "python",
    "args": ["-m", "hello_world.main"],
    "cwd": "hello_world",
},
"{SSE/STREAMABLE-HTTP_SERVER_NAME}": {
    "type": "sse/streamable-http",
    "url": "{URL for sse/streamable-http mcp server}",
    "headers": {
        "Authorization": f"Bearer {token}"
    }
},
```

**Step 3: Update MCP Tool Schema**

> **Important**: VirtualPC MCP Server utilizes pre-generated tool schema data for the `list_tools()` function, therefore you must update [mcp_tool_schema.json](./gaia-mcp-server/mcp_servers/mcp_tool_schema.json) after modifying the MCP server configuration.

A Python script [build_mcp_tool_schema.py](./gaia-mcp-server/mcp_servers/build_mcp_tool_schema.py) is provided to update `mcp_tool_schema.json`. Before executing this script, ensure the MCP server [.env](./gaia-mcp-server/mcp_servers/.env) file is correctly configured.

```bash
cd ./gaia-mcp-server/mcp_servers/
pip install mcp
python build_mcp_tool_schema.py
```

**Step 4: Build Docker Image and Deploy Service**

After completing the above steps, build the Docker image and deploy the service.

## 4. Contributing

We welcome contributions from the community! Please refer to our contributing guidelines for:

- Code style and standards
- Pull request process
- Issue reporting
- Development setup instructions

## 5. References

### Acknowledgments

- **Magentic-UI Project**: We have incorporated Docker Browser source code from the [magentic-ui](https://github.com/microsoft/magentic-ui) project. Special thanks to the magentic-ui project team for their excellent work.

### Related Projects

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Magentic-UI](https://github.com/microsoft/magentic-ui)
- [Debian](https://www.debian.org/)

---

<div align="center">

**VirtualPC MCP Server** - Empowering AI agents with robust, scalable runtime environments

[license-image]: https://img.shields.io/badge/License-MIT-yellow.svg
[license-url]: https://opensource.org/licenses/MIT

</div>
