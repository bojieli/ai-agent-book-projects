# Execution Tools MCP Server / 执行工具 MCP 服务器

> Companion code for *AI Agents in Depth*, Chapter 4 — **Experiment 4-2 ★★**. MCP execution tools with LLM approval, auto-verification, and long-output truncation/persist.  
> 配套《深入理解 AI Agent》第 4 章 **实验 4-2 ★★**。带 LLM 事前审批、自动校验、长输出截断与持久化的执行工具 MCP 服务器。

← [Chapter 4 index / 返回第 4 章目录](../README.md)

---

## English

An MCP (Model Context Protocol) server that provides comprehensive execution tools with built-in safety mechanisms for AI agents.

This project corresponds to Experiment 4-2 in the book’s “Execution Tools” section. It focuses on layered safety (input validation, permission control, LLM pre-approval), automatic syntax verification and feedback loops, and truncation plus persistence of long outputs. Recommended start: `python cli.py demo`.

### Features

#### Safety Mechanisms

1. **LLM-Based Approval**: Irreversible operations require approval from a secondary LLM before execution
2. **Result Summarization**: Execution tool outputs larger than 10,000 characters are automatically summarized by an LLM for easier processing
3. **Automatic Verification**: Operations that can be verified (e.g., syntax checking) are automatically validated

#### Tool Categories

##### File System Tools
- **file_write**: Write content to files with automatic syntax verification
- **file_edit**: Edit existing files with diff preview and verification

##### Generic Execution Tools
- **code_interpreter**: Execute Python code in a sandboxed environment with result analysis
- **virtual_terminal**: Execute shell commands with error summarization

##### External System Integration Tools
- **google_calendar_add**: Add events to Google Calendar
- **github_create_pr**: Create GitHub Pull Requests with validation

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

1. Copy `env.example` to `.env`:
```bash
cp env.example .env
```

2. Configure your environment variables:
```
# LLM Configuration (for safety checks and summarization)
PROVIDER=kimi

# API Keys (set the one for your provider)
KIMI_API_KEY=your_kimi_key
# SILICONFLOW_API_KEY=your_siliconflow_key
# DOUBAO_API_KEY=your_doubao_key
# OPENROUTER_API_KEY=your_openrouter_key

# Model (optional, defaults to provider's default)
# MODEL=kimi-k3

# Model parameters
TEMPERATURE=0.7
MAX_TOKENS=4096

# External Services (optional)
GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json
GITHUB_TOKEN=your_github_token

# Safety Settings
REQUIRE_APPROVAL_FOR_DANGEROUS_OPS=true
AUTO_SUMMARIZE_COMPLEX_OUTPUT=true
AUTO_VERIFY_CODE=true
```

**Supported Providers:**
- `siliconflow`: Qwen/Qwen3-235B-A22B-Thinking-2507
- `doubao`: doubao-seed-1-6-thinking-250715  
- `kimi`/`moonshot`: kimi-k3
- `openrouter`: google/gemini-3.5-flash (or openai/gpt-5.6-luna, anthropic/claude-sonnet-4.6)

> **Universal OpenRouter fallback**: when the configured `PROVIDER`'s key is
> missing but `OPENROUTER_API_KEY` is set, the LLM steps (approval,
> summarization, error/syntax analysis) transparently switch to `openrouter`
> via `Config.effective_provider()`. Set `MODEL` to a `provider/model` id for
> OpenRouter, e.g. `MODEL=openai/gpt-5.6-luna`.

### Usage

#### CLI entry (`cli.py`)

`cli.py` is the unified command-line entry for listing tools, calling each execution tool, and running end-to-end demos. It reuses the same tool implementations as the MCP server, so behavior matches.

```bash
# Overview and all subcommands
python cli.py --help

# List all execution tools
python cli.py list

# End-to-end offline demo (recommended first; no API key)
python cli.py demo

# Call a tool individually
python cli.py code --language python --code "print(2 ** 10)"
python cli.py shell "python3 --version"
python cli.py write --path notes.txt --content "hello" --overwrite
python cli.py edit --path notes.txt --search hello --replace world
```

Global flags (before the subcommand):

| Flag | Effect |
|------|------|
| `--provider` | Override LLM provider (`PROVIDER`) |
| `--workspace` | Override workspace directory (file ops restricted here) |
| `--no-approval` | Disable LLM pre-approval for dangerous ops |
| `--no-verify` | Disable auto syntax check for write/code |
| `--no-summarize` | Disable LLM summarization of long output (still truncates and persists) |

**Offline operation**: `list`, `demo`, and `code`/`shell`/`write`/`edit` with approval/summarize/non-Python verify off need no API key. API key is needed for: LLM pre-approval, LLM summarization of long output, non-Python syntax checks. `calendar` and `pr` also need their external credentials.

> **Warning — `--no-approval`**: this flag bypasses the LLM pre-approval check for dangerous operations. Use it only in controlled local demos (e.g. a throwaway workspace). Never combine it with real workspaces or destructive commands.
>
> **Long-output truncation and persistence**: when `code_interpreter` / `virtual_terminal` output exceeds the threshold (default 200 lines or 10000 characters), the tool keeps only the first and last 50 lines in context, writes the full output to a temp file, and returns the path in `stdout_file` / `stderr_file`. This path does **not** depend on an LLM and works offline.

#### Running the MCP Server

```bash
python server.py
```

#### Using with MCP Client

```python
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_tools():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Use file write tool
            result = await session.call_tool("file_write", {
                "path": "test.py",
                "content": "print('Hello, World!')"
            })

            # Use code interpreter
            result = await session.call_tool("code_interpreter", {
                "code": "import math\nprint(math.sqrt(16))"
            })

            # Use virtual terminal
            result = await session.call_tool("virtual_terminal", {
                "command": "ls -la"
            })


asyncio.run(use_tools())
```

#### Testing Individual Tools

```bash
# Test file operations
python test_file_tools.py

# Test execution tools
python test_execution_tools.py

# Test external integrations
python test_external_tools.py
```

### Architecture

The server implements a layered architecture:

1. **Safety Layer**: Intercepts dangerous operations and validates them
2. **Tool Layer**: Implements individual tool logic
3. **Verification Layer**: Validates outputs and provides feedback
4. **Integration Layer**: Connects to external services

### Examples

See `examples.py` for comprehensive usage examples.

---

## 中文

为 AI Agent 提供带内置安全机制的综合执行工具 MCP（Model Context Protocol）服务器。

本项目对应书中第 4 章「执行工具」一节的实验 4-2，聚焦执行工具的安全机制：
分层安全防护（输入验证、权限控制、LLM 事前审批）、自动语法验证与反馈闭环、
以及长输出的截断与持久化。推荐从 `python cli.py demo` 开始。

### 功能

#### 安全机制

1. **基于 LLM 的审批**：不可逆操作在执行前需经二级 LLM 审批
2. **结果总结**：执行工具输出超过 10,000 字符时由 LLM 自动总结，便于处理
3. **自动校验**：可校验的操作（如语法检查）自动验证

#### 工具分类

##### 文件系统工具
- **file_write**：写入文件，自动语法校验
- **file_edit**：编辑已有文件，带 diff 预览与校验

##### 通用执行工具
- **code_interpreter**：沙箱中执行 Python，带结果分析
- **virtual_terminal**：执行 shell 命令，带错误总结

##### 外部系统集成工具
- **google_calendar_add**：向 Google Calendar 添加事件
- **github_create_pr**：创建 GitHub Pull Request（带校验）

### 安装

```bash
pip install -r requirements.txt
```

### 配置

1. 复制 `env.example` 为 `.env`：
```bash
cp env.example .env
```

2. 配置环境变量：
```
# LLM Configuration (for safety checks and summarization)
PROVIDER=kimi

# API Keys (set the one for your provider)
KIMI_API_KEY=your_kimi_key
# SILICONFLOW_API_KEY=your_siliconflow_key
# DOUBAO_API_KEY=your_doubao_key
# OPENROUTER_API_KEY=your_openrouter_key

# Model (optional, defaults to provider's default)
# MODEL=kimi-k3

# Model parameters
TEMPERATURE=0.7
MAX_TOKENS=4096

# External Services (optional)
GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json
GITHUB_TOKEN=your_github_token

# Safety Settings
REQUIRE_APPROVAL_FOR_DANGEROUS_OPS=true
AUTO_SUMMARIZE_COMPLEX_OUTPUT=true
AUTO_VERIFY_CODE=true
```

**支持的 Provider：**
- `siliconflow`：Qwen/Qwen3-235B-A22B-Thinking-2507
- `doubao`：doubao-seed-1-6-thinking-250715  
- `kimi`/`moonshot`：kimi-k3
- `openrouter`：google/gemini-3.5-flash（或 openai/gpt-5.6-luna、anthropic/claude-sonnet-4.6）

> **OpenRouter 通用兜底**：当配置的 `PROVIDER` 对应 Key 缺失，但设置了
> `OPENROUTER_API_KEY` 时，LLM 步骤（审批、总结、错误/语法分析）经
> `Config.effective_provider()` 透明切换到 `openrouter`。
> 为 OpenRouter 设置 `MODEL` 为 `provider/model` 形式，例如
> `MODEL=openai/gpt-5.6-luna`。

### 使用

#### 命令行入口（`cli.py`）

`cli.py` 是统一的命令行入口，用于列出、单独调用每个执行工具，并运行端到端演示。
它复用与 MCP 服务器相同的工具实现，因此行为完全一致。

```bash
# 查看总帮助与所有子命令
python cli.py --help

# 列出所有执行工具
python cli.py list

# 端到端离线演示（推荐先看这个；无需 API key 即可运行）
python cli.py demo

# 单独调用某个工具
python cli.py code --language python --code "print(2 ** 10)"
python cli.py shell "python3 --version"
python cli.py write --path notes.txt --content "hello" --overwrite
python cli.py edit --path notes.txt --search hello --replace world
```

全局开关（放在子命令之前）：

| 开关 | 作用 |
|------|------|
| `--provider` | 覆盖 LLM 提供商（`PROVIDER`） |
| `--workspace` | 覆盖工作目录（文件操作被限制在此目录内） |
| `--no-approval` | 关闭危险操作的 LLM 事前审批 |
| `--no-verify` | 关闭写文件/代码的自动语法校验 |
| `--no-summarize` | 关闭长输出的 LLM 总结（仍会截断并持久化） |

**离线运行**：`list`、`demo` 以及关闭了审批/总结/非 Python 校验的
`code`/`shell`/`write`/`edit` 均无需 API key。需要 API key 的场景为：LLM 事前审批、
长输出的 LLM 总结、非 Python 语法校验。`calendar` 与 `pr` 还额外需要相应外部凭据。

> **警告 —— `--no-approval`**：该开关会绕过危险操作的 LLM 事前审批，仅适用于受控的本地演示（如一次性临时工作区）。切勿在真实工作区中使用，也不要与破坏性命令搭配使用。
>
> **长输出的截断与持久化**：当 `code_interpreter` / `virtual_terminal` 的输出
> 超过阈值（默认 200 行或 10000 字符）时，工具只在上下文中保留头尾各 50 行，
> 完整输出落盘到临时文件，并在返回值的 `stdout_file` / `stderr_file` 字段给出路径。
> 该机制不依赖 LLM，可离线工作。

#### 运行 MCP 服务器

```bash
python server.py
```

#### 配合 MCP 客户端

```python
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_tools():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Use file write tool
            result = await session.call_tool("file_write", {
                "path": "test.py",
                "content": "print('Hello, World!')"
            })

            # Use code interpreter
            result = await session.call_tool("code_interpreter", {
                "code": "import math\nprint(math.sqrt(16))"
            })

            # Use virtual terminal
            result = await session.call_tool("virtual_terminal", {
                "command": "ls -la"
            })


asyncio.run(use_tools())
```

#### 测试单个工具

```bash
# Test file operations
python test_file_tools.py

# Test execution tools
python test_execution_tools.py

# Test external integrations
python test_external_tools.py
```

### 架构

服务器采用分层架构：

1. **安全层**：拦截危险操作并校验
2. **工具层**：实现各工具逻辑
3. **校验层**：验证输出并反馈
4. **集成层**：对接外部服务

### 示例

更完整的用法见 `examples.py`。另见 [`EXPERIMENT.md`](EXPERIMENT.md) 中的实验说明。

---

## Notes / 说明

- Start with `python cli.py demo` (no API key).  
- 建议从 `python cli.py demo` 开始（无需 API Key）。  
- Long-output truncation/persistence works offline without LLM.  
- 长输出截断与持久化不依赖 LLM，可离线。
