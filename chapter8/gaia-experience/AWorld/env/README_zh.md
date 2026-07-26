<div align="center">

# VirtualPC MCP Server (孵化中)

*基于 Debian 的统一 MCP 工具运行时环境，具有会话级环境隔离、环境状态持久化、实时 UI 可视化、分布式架构和可扩展性*

[![License: MIT][license-image]][license-url]

</div>

<div align="center">

[English](./README.md) | [快速开始](#快速开始) | [开发](#开发) | [贡献](#贡献)

</div>

---

## 1. 概述

VirtualPC MCP Server 是一个综合性的 MCP（模型上下文协议）工具运行时环境，旨在为 AI 代理提供统一、隔离和可扩展的执行环境。基于 Debian 构建，它提供会话级环境隔离、跨多个会话的持久状态管理以及实时可视化功能。

### 1.1 特性

- **会话级环境隔离**：每个 MCP 会话在其独立的隔离环境中运行
- **多会话状态持久化**：在多个 MCP 会话之间维护环境状态
- **实时 UI 可视化**：Agent MCP 操作的实时监控和可视化
- **分布式架构**：支持本地 Docker 和 Kubernetes 集群部署
- **可扩展运行时**：模块化设计，支持无缝集成新的 MCP 工具服务器

## 2. 快速开始

本项目支持本地 Docker 部署（适用于演示和调试）和 Kubernetes 集群部署（推荐用于生产和强化学习训练）。

### 2.1 本地 Docker 部署

#### 前置要求

确保 Docker 和 Docker Compose 已正确安装并正常运行：

```bash
# 验证 Docker 安装
docker --version
docker compose --version

# 验证 Docker 守护进程是否运行
docker ps
docker compose ps
```

**步骤 1：配置环境并准备 Gaia 数据集**

1. 复制环境模板并配置您的设置：

```bash
cp ./gaia-mcp-server/mcp_servers/.env_template ./gaia-mcp-server/mcp_servers/.env
```

编辑 `./gaia-mcp-server/mcp_servers/.env` 文件，填入您的具体配置值。

2. 从 Hugging Face 下载 [gaia_dataset](https://huggingface.co/datasets/gaia-benchmark/GAIA) 并放置到 `./gaia-mcp-server/docker/gaia_dataset`

**步骤 2：启动 VirtualPC MCP Server**

```bash
sh run-docker.sh
```

监控终端输出，查看启动过程中是否有任何错误。

生成本地 Bearer token，并将打印出的值复制到下面的 `<local-debug-jwt>`。如果你修改了 `virtualpc-mcp/docker-compose.yaml` 中的 `MCP_GATEWAY_TOKEN_SECRET`，请在运行此命令前导出相同的值。

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

**步骤 3：连接到 VirtualPC MCP Server**

使用以下配置连接到 VirtualPC MCP Server：

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

**注意**：上述 Bearer token 仅用于本地测试。`MCP_SERVERS` 头部指定了当前连接的 MCP 服务器范围，应该是 `gaia-mcp-server/mcp_servers/mcp_config.py` 中定义的服务器名称的子集。

### 2.2 Kubernetes 集群部署

对于生产部署和强化学习训练场景，推荐使用 Kubernetes 集群部署。详细说明将在后续更新中提供。

## 3. 开发

### 3.1 向 VirtualPC MCP Server 添加自定义 MCP 工具

**步骤 1：开发 MCP 工具（可选）**

如果您需要开发自定义 MCP 工具并将其注册到 VirtualPC MCP Server，请在 `gaia-mcp-server/mcp_servers` 下创建您的 MCP 工具项目目录并实现 MCP 工具代码。参考 [hello_world](./gaia-mcp-server/mcp_servers/hello_world/) 目录的项目结构。

项目规范：

1. 使用 `pyproject.toml` 管理项目依赖，用于 Docker 镜像构建

**步骤 2：注册 MCP 工具**

将您开发的 MCP 工具或第三方 MCP 工具注册到 VirtualPC MCP Server。

编辑 [MCP 工具注册文件](./gaia-mcp-server/mcp_servers/mcp_config.py)：

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

**步骤 3：更新 MCP 工具模式**

> **重要**：VirtualPC MCP Server 使用预生成的工具模式数据用于 `list_tools()` 函数，因此您必须在修改 MCP 服务器配置后更新 [mcp_tool_schema.json](./gaia-mcp-server/mcp_servers/mcp_tool_schema.json)。

我们提供了一个 Python 脚本 [build_mcp_tool_schema.py](./gaia-mcp-server/mcp_servers/build_mcp_tool_schema.py) 来更新 `mcp_tool_schema.json`。在执行此脚本之前，请确保 MCP 服务器 [.env](./gaia-mcp-server/mcp_servers/.env) 文件已正确配置。

```bash
cd ./gaia-mcp-server/mcp_servers/
pip install mcp
python build_mcp_tool_schema.py
```

**步骤 4：构建 Docker 镜像并部署服务**

完成上述步骤后，构建 Docker 镜像并部署服务。

## 4. 贡献

我们欢迎社区的贡献！请参考我们的贡献指南：

- 代码风格和标准
- 拉取请求流程
- 问题报告
- 开发设置说明

## 5. 参考资料

### 致谢

- **Magentic-UI 项目**：我们已整合来自 [magentic-ui](https://github.com/microsoft/magentic-ui) 项目的 Docker Browser 源代码。特别感谢 magentic-ui 项目团队的出色工作。

### 相关项目

- [模型上下文协议 (MCP)](https://modelcontextprotocol.io/)
- [Magentic-UI](https://github.com/microsoft/magentic-ui)
- [Debian](https://www.debian.org/)

---

<div align="center">

**VirtualPC MCP Server** - 为 AI Agent 提供强大、可扩展的运行时环境

[license-image]: https://img.shields.io/badge/License-MIT-yellow.svg
[license-url]: https://opensource.org/licenses/MIT

</div>
