# Comprehensive Coding Agent / 综合编码 Agent（纯 Python 实现）

> Production-ready AI coding agent (Claude + pure Python tools) implementing Chapter 2 techniques—no CLI tool dependencies.  
> 生产级 AI 编码 Agent：落地第 2 章技术，**纯 Python 工具**实现，无命令行工具依赖。

← [Chapter 5 index / 返回第 5 章目录](../README.md)

---

## English

### Overview

A production-ready AI coding agent built with Claude, implementing techniques from Chapter 2 with **pure Python tools**—no command-line dependencies required.

### Key Features

#### Pure Python Implementation

**All tools implemented without command-line dependencies:**

- ❌ No `grep`, `rg` (ripgrep), `find` commands needed
- ❌ No dependency on system utilities
- ✅ **100% pure Python** implementations
- ✅ Works on any system with Python 3.8+
- ✅ **Especially designed for Mac users** without command-line tools

#### Complete Tool Suite

**All 16 tools from tools.json fully implemented:**

**File Operations (Pure Python):**

- `Read` - File reading with image/PDF/notebook support
- `Write` - File writing with auto lint checking
- `Edit` - Search and replace editing
- `MultiEdit` - Multiple edits in one operation

**Search Tools (Pure Python, no rg/grep dependency):**

- `Grep` - **Pure Python regex search** with full ripgrep feature parity
  - Full regex support
  - Case insensitive search
  - Context lines (before/after/around)
  - Line numbers
  - Multiline mode
  - Glob filtering
  - File type filtering
  - Multiple output modes
- `Glob` - File pattern matching
- `LS` - Directory listing

**Shell Operations:**

- `Bash` - Persistent shell sessions
- `BashOutput` - Background job output
- `KillBash` - Terminate shells

**Project Management:**

- `TodoWrite` - Task list management
- `ExitPlanMode` - Plan mode exit

**Advanced:**

- `NotebookEdit` - Jupyter notebook editing
- `WebFetch` - Web content fetching (stub)
- `WebSearch` - Web search (stub)
- `Task` - Sub-agent launcher (stub)

#### System Hint Techniques (Chapter 2)

1. **Timestamps**: Every message and tool result timestamped
2. **Tool Call Counting**: Warns after 3+ repeated calls
3. **TODO List Management**: Explicit task tracking
4. **Detailed Error Information**: Rich error context
5. **System State Awareness**: Working directory, OS, Python version
6. **Environment Information**: Dynamic state in context

#### Terminal Environment

- **Persistent Shell Sessions**: Commands in same shell
- **Working Directory Tracking**: Directory changes persist
- **Background Execution**: Long-running command support

#### Auto Lint Detection

After Write/Edit/MultiEdit:

- Python syntax checking
- JavaScript/TypeScript checking
- Errors appear immediately in tool results

### Project Structure

```
coding-agent/
├── agent.py                    # Main agent implementation
├── system_state.py            # System state tracking
├── tool_registry.py           # Tool name → implementation mapping
├── tools/                     # All tool implementations
│   ├── __init__.py
│   ├── base.py               # Base tool class
│   ├── bash_tool.py          # Shell execution
│   ├── bash_output_tool.py   # Background job output
│   ├── kill_bash_tool.py     # Shell termination
│   ├── read_tool.py          # File reading
│   ├── write_tool.py         # File writing
│   ├── edit_tool.py          # File editing
│   ├── multi_edit_tool.py    # Multiple edits
│   ├── grep_tool.py          # Pure Python regex search (no rg!)
│   ├── glob_tool.py          # File pattern matching
│   ├── ls_tool.py            # Directory listing
│   ├── todo_write_tool.py    # TODO management
│   ├── exit_plan_mode_tool.py
│   ├── notebook_edit_tool.py
│   ├── web_fetch_tool.py
│   ├── web_search_tool.py
│   ├── task_tool.py
│   └── shell_session.py      # Shell session management
├── tools.json                 # Tool definitions
├── system-prompt.md          # System prompt
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

### Installation

```bash
# Navigate to project directory
cd /Users/boj/ai-agent-book/projects/week5/coding-agent

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and configure your provider
```

#### Configuration

Edit `.env` file:

```bash
# Choose your provider (anthropic, openai, or openrouter)
PROVIDER=anthropic

# Add API key for your chosen provider
ANTHROPIC_API_KEY=sk-ant-api03-...
# or
OPENROUTER_API_KEY=sk-or-v1-...
# or
OPENAI_API_KEY=sk-...

# Select model appropriate for your provider
DEFAULT_MODEL=claude-sonnet-5
```

**See [PROVIDERS.md](PROVIDERS.md) for detailed provider configuration guide.**

#### Requirements

**Core dependencies:**

- Python 3.8+
- `anthropic` - For Anthropic API
- `openai` - For OpenAI/OpenRouter API
- `python-dotenv` - For configuration

**Optional (for enhanced features):**

- `PyPDF2` - For PDF reading
- `requests`, `beautifulsoup4`, `html2text` - For WebFetch

**No command-line tools needed!** Works on macOS without Homebrew packages.

#### Supported Providers

- **Anthropic** - Direct Claude API access
- **OpenRouter** - Access to Claude, GPT, Gemini, Llama, and more
- **OpenAI** - Direct GPT API access

The agent automatically handles the different API formats for each provider.

#### OpenRouter as a universal fallback

You do **not** need a direct Anthropic or OpenAI key to run the agent. If the
requested direct provider's key is missing, the agent transparently falls back
to **OpenRouter** (via the OpenAI-compatible SDK) as long as
`OPENROUTER_API_KEY` is set:

- `PROVIDER=anthropic` **with** `ANTHROPIC_API_KEY` → Anthropic SDK, unchanged (default behavior).
- `PROVIDER=anthropic` **without** `ANTHROPIC_API_KEY` (but `OPENROUTER_API_KEY` set) → routed through OpenRouter.
- `PROVIDER=openai` **with** `OPENAI_API_KEY` → OpenAI SDK, unchanged.
- `PROVIDER=openai` **without** `OPENAI_API_KEY` (but `OPENROUTER_API_KEY` set) → routed through OpenRouter.

When falling back, the native model id is **prefixed/mapped** to an OpenRouter id:

| Requested model | OpenRouter id used |
|-----------------|--------------------|
| `claude-sonnet-*` (e.g. `claude-sonnet-5`) | `anthropic/claude-sonnet-4.6` |
| `claude-haiku-*` | `anthropic/claude-haiku-4.5` |
| `claude-opus-*` / other `claude-*` | `anthropic/claude-opus-4.8` |
| `gpt-*` / `o1-*` (e.g. `gpt-5.6-luna`) | `openai/<model>` |
| already prefixed (`vendor/model`) | passed through unchanged |

So a user with **only** an `OPENROUTER_API_KEY` can run, e.g.:

```bash
# No ANTHROPIC_API_KEY needed — falls back to OpenRouter automatically
python main.py --provider anthropic --model claude-sonnet-5 -p "..."

# gpt-5.6-luna routed through OpenRouter (no OPENAI_API_KEY needed)
python main.py --provider openai --model gpt-5.6-luna -p "..."
```

Set `PROVIDER=openrouter` explicitly (with a `vendor/model` id) if you want to
target a specific OpenRouter model without any mapping.

### Usage

#### CLI entry (`main.py`)

`main.py` is the recommended entry with a unified argparse UI. Run
`python main.py --help` for full Chinese help:

```bash
python main.py --help
```

Main flags:

| Flag | Description |
|------|------|
| (no args) | Interactive chat (default) |
| `-p, --prompt "task"` | Non-interactive: one task then exit (scripts / CI) |
| `--list-tools` | **Offline** list of registered tools (no API key) |
| `--provider {anthropic,openai,openrouter}` | Override `.env` `PROVIDER` |
| `--model NAME` | Override `.env` `DEFAULT_MODEL` |
| `--base-url URL` | Override API base URL (gateway / OpenAI-compatible) |
| `--max-iterations N` | Max agent iterations per task (default 50) |
| `--no-color` | Disable color (auto-off without TTY) |

#### Quick self-check (offline, no API key)

```bash
$ python main.py --list-tools
共 16 个工具：

  Task           Launch a new agent to handle complex, multi-step tasks autonomously.
  Bash           Executes a given bash command in a persistent shell session ...
  Glob           - Fast file pattern matching tool that works with any codebase size
  Grep           A powerful search tool built on ripgrep
  ...
```

#### End-to-end example: real coding task

With `.env` configured (see Configuration), one command creates and runs a script:

```bash
python main.py -p "创建 hello_world.py：打印 Hello, World!，包含一个按姓名问候的函数和一个 main 演示块，然后运行它验证输出。"
```

**Successful terminal structure (illustrative; turns/calls depend on model):**

```
✓ Agent initialized successfully
You: 创建 hello_world.py ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 Calling tool: Write
   ✓ Completed (call #1)
   ✓ No lint errors
   File: hello_world.py
🔧 Calling tool: Bash
   ✓ Completed (call #2)
   Output:
     Hello, World!
     Hello, Alice!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Task completed!
   Iterations: 2
   Tool calls: 2
```

> Success markers: Agent calls `Write` then `Bash`, real script output appears,
> ends with `✅ Task completed!`.
> (`quickstart.py` is a scripted version of the same task.)

#### Interactive chat (default)

```bash
python main.py
```

**Features:**

- 🎨 Color-coded output for better readability
- ⚡ Real-time streaming responses
- 🔧 Live tool execution display
- 📊 Built-in status command
- 💬 Conversation history
- 🔄 Reset command to start fresh

**In-session commands:**

- `/help` - Show help message
- `/quit` or `/exit` - Exit the CLI
- `/reset` - Reset conversation history
- `/clear` - Clear the screen
- `/status` - Show agent status (tool calls, TODOs, etc.)

#### Other example scripts (API key required)

```bash
python quickstart.py                  # basic quickstart (same task as e2e above)
python example_complex_task.py        # complex multi-step task
python example_with_system_hints.py   # system hint techniques demo
```

#### Programmatic Usage

```python
from agent import CodingAgent

agent = CodingAgent(api_key="your-key")

for event in agent.run("List all Python files"):
    if event["type"] == "text_delta":
        print(event["delta"], end="", flush=True)
    elif event["type"] == "done":
        print("\n✅ Done!")
```

### Pure Python Grep Implementation

The **Grep tool** is fully implemented in pure Python without any dependency on `grep`, `rg`, or other command-line tools. It provides all the features of ripgrep:

```python
# Example: Search for pattern in files
{
    "name": "Grep",
    "input": {
        "pattern": "def.*test",
        "path": "/path/to/search",
        "output_mode": "content",
        "-i": True,              # Case insensitive
        "-C": 3,                 # 3 lines context
        "-n": True,              # Show line numbers
        "glob": "*.py",          # Only Python files
        "multiline": False       # Single line matching
    }
}
```

**Features:**

- ✅ Full regex support (Python `re` module)
- ✅ Case insensitive search (`-i`)
- ✅ Context lines (`-A`, `-B`, `-C`)
- ✅ Line numbers (`-n`)
- ✅ Multiline mode
- ✅ Glob filtering (`glob` parameter)
- ✅ File type filtering (`type` parameter)
- ✅ Output modes: `content`, `files_with_matches`, `count`
- ✅ Head limit
- ✅ Recursive directory search
- ✅ Binary file skip
- ✅ Hidden file/directory skip

### Architecture

#### Modular Tool System

Each tool is implemented as a separate class inheriting from `BaseTool`:

```python
class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "MyTool"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Tool implementation
        return {"result": "success"}
```

#### Tool Registry

`ToolRegistry` maps tool names to implementations:

```python
registry = ToolRegistry()
tool = registry.get_tool("Grep", system_state)
result = tool.execute(params)
```

#### System State

`SystemState` tracks:

- Current working directory
- Tool call counts
- TODO list
- Shell sessions
- Environment info

#### System Hints

System hints are injected before each LLM call:

```xml
<system_hint>
# System State
Current Time: 2025-10-12 15:30:45
Working Directory: /Users/boj/coding-agent
OS: Darwin
Python: Python 3.11.5

# Tool Call Statistics
- Grep: 2 calls
- Write: 1 calls

# Current TODO List
✅ [1] Search for files (completed)
🔄 [2] Implement feature (in_progress)
⬜ [3] Write tests (pending)
</system_hint>
```

### Design Principles

#### 1. Pure Python Implementation

**Why:** Maximum portability and compatibility

- Works on any system with Python
- No Homebrew, apt, or other package managers needed
- Consistent behavior across platforms

#### 2. Modular Tool Architecture

**Why:** Maintainability and extensibility

- Each tool is self-contained
- Easy to add new tools
- Easy to test individually
- Clear separation of concerns

#### 3. No Command-Line Dependencies

**Why:** Reliability and control

- **Grep**: Pure Python regex search
- **Glob**: Python's `pathlib.glob()`
- **LS**: Python's `os` and `pathlib`
- No subprocess calls for core functionality
- Full control over behavior

#### 4. System Hints for Self-Awareness

**Why:** Better agent behavior

- Prevents infinite loops (tool call counting)
- Maintains task focus (TODO tracking)
- Provides environmental context
- Enables self-monitoring

### Comparison with Chapter 2

| Technique | Status | Implementation |
|-----------|--------|----------------|
| Standard OpenAI Tool Format | ✅ | Anthropic SDK |
| Streaming Tool Calls | ✅ | Real-time JSON delta parsing |
| Parallel Tool Calls | ✅ | Multiple tools per response |
| Pure Python Tools | ✅ | **No command-line dependencies** |
| Grep without rg | ✅ | **Pure Python regex search** |
| Timestamps | ✅ | All messages/tools |
| Tool Call Counting | ✅ | Warns at 3+ |
| TODO List | ✅ | TodoWrite tool |
| System State | ✅ | Working dir, OS, Python |
| Persistent Shell | ✅ | Shell sessions |
| Auto Lint Detection | ✅ | After Write/Edit/MultiEdit |

### Configuration (`.env`)

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional
DEFAULT_MODEL=claude-sonnet-5
MAX_ITERATIONS=50
MAX_TOKENS=8192
```

### Adding New Tools

1. Create tool file in `tools/`:

```python
# tools/my_tool.py
from .base import BaseTool

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "MyTool"
    
    def _execute_impl(self, params):
        # Implementation
        return {"result": "success"}
```

2. Register in `tools/__init__.py`:

```python
from .my_tool import MyTool

__all__ = [..., 'MyTool']
```

3. Add to `tool_registry.py`:

```python
self._tools = {
    ...,
    "MyTool": MyTool,
}
```

4. Add definition to `tools.json`

### Troubleshooting

#### "No module named 'tools'"

Make sure you're running from the project directory:

```bash
cd /Users/boj/ai-agent-book/projects/week5/coding-agent
python agent.py
```

#### Grep not finding files

Check:

- Path is correct
- Pattern is valid regex
- Glob pattern matches files
- Files contain searchable text (not binary)

#### Shell commands fail

Ensure:

- Bash is available on `PATH` on macOS/Linux
- PowerShell is available on `PATH` on Windows (`cmd.exe` is used as a fallback)
- Working directory exists
- Commands use the native shell syntax and are properly quoted

### Testing

Comprehensive test suite with 130+ tests covering all tool features.

#### Run Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=tools --cov-report=html

# Run specific tool tests
pytest tests/test_grep_tool.py
pytest tests/test_bash_tool.py

# Verbose output
pytest -v
```

#### Test Coverage

- **130+ tests** across 14 test files
- **2,200+ lines** of test code
- **All major features** from tools.json tested
- **Integration tests** for tool chaining and system hints

See [tests/README.md](tests/README.md) for detailed test documentation.

### Learning Path

1. **Start with examples**: Run `python main.py` (interactive CLI)
2. **Run quickstart**: `python quickstart.py`
3. **Explore system hints**: `python example_with_system_hints.py`
4. **Study Grep implementation**: See `tools/grep_tool.py`
5. **Run tests**: `pytest -v` to see all features in action
6. **Read Chapter 2**: Understand the theory
7. **Add custom tools**: Extend the system

### References

- Chapter 2: Context Engineering (AI Agent Book)
- Tools specification: `tools.json`
- System prompt: `system-prompt.md`
- Anthropic Claude API: https://docs.anthropic.com/

### Key Advantages

1. **No Dependencies on External Tools**
   - Pure Python implementation
   - Works without rg, grep, find, etc.
   - Perfect for Mac users without Homebrew

2. **Modular Architecture**
   - Each tool is a separate file
   - Easy to understand and modify
   - Clear separation of concerns

3. **Production Ready**
   - Comprehensive error handling
   - Auto lint detection
   - System hints for reliability
   - Streaming support for UX

4. **Educational Value**
   - Learn how tools work internally
   - Understand pure Python file operations
   - See regex search implementation
   - Study agent architecture patterns

### License

MIT

### Contributing

This is an educational implementation. Feel free to adapt and extend!

---

**Built with pure Python for maximum portability and learning! 🐍✨**

---

## 中文

### 概述

基于 Claude 的生产级 AI 编码 Agent，落地第 2 章相关技术，全部工具为**纯 Python 实现**——**不依赖**任何命令行工具。

### 核心特性

#### 纯 Python 实现

**全部工具均无命令行依赖：**

- ❌ 不需要 `grep`、`rg`（ripgrep）、`find`
- ❌ 不依赖系统工具
- ✅ **100% 纯 Python**
- ✅ 任意 Python 3.8+ 环境可跑
- ✅ **尤其适合**未装命令行工具的 Mac 用户

#### 完整工具集

**`tools.json` 中的 16 个工具均已实现：**

**文件操作（纯 Python）：**

- `Read` - 读文件（含图像/PDF/Notebook）
- `Write` - 写文件（自动 lint）
- `Edit` - 查找替换编辑
- `MultiEdit` - 一次多处编辑

**搜索工具（纯 Python，无 rg/grep）：**

- `Grep` - **纯 Python 正则搜索**，功能对齐 ripgrep
  - 完整正则
  - 大小写不敏感
  - 上下文行（前/后/环绕）
  - 行号
  - 多行模式
  - Glob 过滤
  - 文件类型过滤
  - 多种输出模式
- `Glob` - 文件模式匹配
- `LS` - 目录列表

**Shell：**

- `Bash` - 持久 shell 会话
- `BashOutput` - 后台任务输出
- `KillBash` - 终止 shell

**项目管理：**

- `TodoWrite` - 任务列表
- `ExitPlanMode` - 退出计划模式

**进阶：**

- `NotebookEdit` - Jupyter 编辑
- `WebFetch` - 抓取网页（stub）
- `WebSearch` - 网页搜索（stub）
- `Task` - 子 Agent 启动（stub）

#### 系统提示（System Hint）技术（第 2 章）

1. **时间戳**：消息与工具结果均打时间戳
2. **工具调用计数**：重复调用 ≥3 次告警
3. **TODO 列表**：显式任务跟踪
4. **详细错误信息**：丰富错误上下文
5. **系统状态感知**：工作目录、OS、Python 版本
6. **环境信息**：动态写入上下文

#### 终端环境

- **持久 Shell 会话**：同一 shell 内连续命令
- **工作目录跟踪**：`cd` 等变更可保持
- **后台执行**：支持长时命令

#### 自动 Lint

Write/Edit/MultiEdit 之后：

- Python 语法检查
- JavaScript/TypeScript 检查
- 错误直接出现在工具结果中

### 项目结构

```
coding-agent/
├── agent.py                    # Main agent implementation
├── system_state.py            # System state tracking
├── tool_registry.py           # Tool name → implementation mapping
├── tools/                     # All tool implementations
│   ├── __init__.py
│   ├── base.py               # Base tool class
│   ├── bash_tool.py          # Shell execution
│   ├── bash_output_tool.py   # Background job output
│   ├── kill_bash_tool.py     # Shell termination
│   ├── read_tool.py          # File reading
│   ├── write_tool.py         # File writing
│   ├── edit_tool.py          # File editing
│   ├── multi_edit_tool.py    # Multiple edits
│   ├── grep_tool.py          # Pure Python regex search (no rg!)
│   ├── glob_tool.py          # File pattern matching
│   ├── ls_tool.py            # Directory listing
│   ├── todo_write_tool.py    # TODO management
│   ├── exit_plan_mode_tool.py
│   ├── notebook_edit_tool.py
│   ├── web_fetch_tool.py
│   ├── web_search_tool.py
│   ├── task_tool.py
│   └── shell_session.py      # Shell session management
├── tools.json                 # Tool definitions
├── system-prompt.md          # System prompt
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

### 安装

```bash
# Navigate to project directory
cd /Users/boj/ai-agent-book/projects/week5/coding-agent

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and configure your provider
```

#### 配置

编辑 `.env`：

```bash
# Choose your provider (anthropic, openai, or openrouter)
PROVIDER=anthropic

# Add API key for your chosen provider
ANTHROPIC_API_KEY=sk-ant-api03-...
# or
OPENROUTER_API_KEY=sk-or-v1-...
# or
OPENAI_API_KEY=sk-...

# Select model appropriate for your provider
DEFAULT_MODEL=claude-sonnet-5
```

**详细供应商配置见 [PROVIDERS.md](PROVIDERS.md)。**

#### 依赖

**核心：**

- Python 3.8+
- `anthropic` - Anthropic API
- `openai` - OpenAI/OpenRouter API
- `python-dotenv` - 配置

**可选（增强能力）：**

- `PyPDF2` - PDF 阅读
- `requests`、`beautifulsoup4`、`html2text` - WebFetch

**无需命令行工具！** 无 Homebrew 的 macOS 也可运行。

#### 支持的供应商

- **Anthropic** - 直连 Claude
- **OpenRouter** - Claude / GPT / Gemini / Llama 等
- **OpenAI** - 直连 GPT

Agent 自动处理各供应商不同的 API 格式。

#### OpenRouter 通用兜底

**不必**持有直连 Anthropic/OpenAI key。若所请求直连供应商的 key 缺失，且设置了
`OPENROUTER_API_KEY`，则经 OpenAI 兼容 SDK **透明回退到 OpenRouter**：

- `PROVIDER=anthropic` **且有** `ANTHROPIC_API_KEY` → Anthropic SDK（默认行为）。
- `PROVIDER=anthropic` **无** `ANTHROPIC_API_KEY`（但有 `OPENROUTER_API_KEY`）→ 走 OpenRouter。
- `PROVIDER=openai` **且有** `OPENAI_API_KEY` → OpenAI SDK。
- `PROVIDER=openai` **无** `OPENAI_API_KEY`（但有 `OPENROUTER_API_KEY`）→ 走 OpenRouter。

回退时原生模型 id **加前缀/映射**为 OpenRouter id：

| Requested model | OpenRouter id used |
|-----------------|--------------------|
| `claude-sonnet-*` (e.g. `claude-sonnet-5`) | `anthropic/claude-sonnet-4.6` |
| `claude-haiku-*` | `anthropic/claude-haiku-4.5` |
| `claude-opus-*` / other `claude-*` | `anthropic/claude-opus-4.8` |
| `gpt-*` / `o1-*` (e.g. `gpt-5.6-luna`) | `openai/<model>` |
| already prefixed (`vendor/model`) | passed through unchanged |

仅持有 `OPENROUTER_API_KEY` 时例如：

```bash
# No ANTHROPIC_API_KEY needed — falls back to OpenRouter automatically
python main.py --provider anthropic --model claude-sonnet-5 -p "..."

# gpt-5.6-luna routed through OpenRouter (no OPENAI_API_KEY needed)
python main.py --provider openai --model gpt-5.6-luna -p "..."
```

若要指定 OpenRouter 模型且不做映射，显式设 `PROVIDER=openrouter` 与 `vendor/model` id。

### 用法

#### 命令行入口（`main.py`）

`main.py` 是唯一推荐入口，统一 argparse。运行
`python main.py --help` 查看完整中文帮助：

```bash
python main.py --help
```

主要参数：

| 参数 | 说明 |
|------|------|
| （无参数） | 进入交互式对话（默认行为） |
| `-p, --prompt "任务"` | 非交互模式：执行单个任务后退出，适合脚本 / CI |
| `--list-tools` | **离线**列出全部已注册工具及简介（无需 API Key，可用于自检） |
| `--provider {anthropic,openai,openrouter}` | 临时覆盖 `.env` 中的 `PROVIDER` |
| `--model 模型名` | 临时覆盖 `.env` 中的 `DEFAULT_MODEL` |
| `--base-url URL` | 临时覆盖 API Base URL（自建网关 / 兼容 OpenAI 的服务） |
| `--max-iterations N` | 单个任务的最大 Agent 迭代轮数（默认 50） |
| `--no-color` | 禁用彩色输出（无 TTY 时自动禁用） |

#### 快速自检（离线，无需 API Key）

```bash
$ python main.py --list-tools
共 16 个工具：

  Task           Launch a new agent to handle complex, multi-step tasks autonomously.
  Bash           Executes a given bash command in a persistent shell session ...
  Glob           - Fast file pattern matching tool that works with any codebase size
  Grep           A powerful search tool built on ripgrep
  ...
```

#### 端到端示例：真实编码任务

配置好 `.env`（见上文 Configuration）后：

```bash
python main.py -p "创建 hello_world.py：打印 Hello, World!，包含一个按姓名问候的函数和一个 main 演示块，然后运行它验证输出。"
```

**成功时的终端输出结构大致如下**（示意，实际轮次/调用次数取决于模型）：

```
✓ Agent initialized successfully
You: 创建 hello_world.py ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 Calling tool: Write
   ✓ Completed (call #1)
   ✓ No lint errors
   File: hello_world.py
🔧 Calling tool: Bash
   ✓ Completed (call #2)
   Output:
     Hello, World!
     Hello, Alice!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Task completed!
   Iterations: 2
   Tool calls: 2
```

> 判定成功的标志：Agent 依次调用 `Write` 写文件、`Bash` 运行脚本，
> 终端出现脚本的真实输出，并以 `✅ Task completed!` 收尾。
> （`quickstart.py` 是同一任务的脚本化版本，可作对照。）

#### 交互式对话（默认）

```bash
python main.py
```

**功能：**

- 🎨 彩色输出
- ⚡ 实时流式响应
- 🔧 现场展示工具执行
- 📊 内置 status 命令
- 💬 对话历史
- 🔄 reset 重新开始

**会话内命令：**

- `/help` - 帮助
- `/quit` 或 `/exit` - 退出
- `/reset` - 清空对话历史
- `/clear` - 清屏
- `/status` - Agent 状态（工具调用、TODO 等）

#### 其他示例脚本（均需 API Key）

```bash
python quickstart.py                  # 基础快速上手（与上文端到端示例同款任务）
python example_complex_task.py        # 复杂多步任务
python example_with_system_hints.py   # 系统提示（System Hint）技术演示
```

#### 编程方式调用

```python
from agent import CodingAgent

agent = CodingAgent(api_key="your-key")

for event in agent.run("List all Python files"):
    if event["type"] == "text_delta":
        print(event["delta"], end="", flush=True)
    elif event["type"] == "done":
        print("\n✅ Done!")
```

### 纯 Python Grep 实现

**Grep** 完全用纯 Python 实现，不依赖 `grep`/`rg` 等，功能对齐 ripgrep：

```python
# Example: Search for pattern in files
{
    "name": "Grep",
    "input": {
        "pattern": "def.*test",
        "path": "/path/to/search",
        "output_mode": "content",
        "-i": True,              # Case insensitive
        "-C": 3,                 # 3 lines context
        "-n": True,              # Show line numbers
        "glob": "*.py",          # Only Python files
        "multiline": False       # Single line matching
    }
}
```

**能力：**

- ✅ 完整正则（Python `re`）
- ✅ 大小写不敏感（`-i`）
- ✅ 上下文行（`-A`、`-B`、`-C`）
- ✅ 行号（`-n`）
- ✅ 多行模式
- ✅ Glob（`glob`）
- ✅ 文件类型（`type`）
- ✅ 输出模式：`content`、`files_with_matches`、`count`
- ✅ Head limit
- ✅ 递归目录
- ✅ 跳过二进制
- ✅ 跳过隐藏文件/目录

### 架构

#### 模块化工具系统

每个工具继承 `BaseTool`：

```python
class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "MyTool"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Tool implementation
        return {"result": "success"}
```

#### 工具注册表

`ToolRegistry` 将工具名映射到实现：

```python
registry = ToolRegistry()
tool = registry.get_tool("Grep", system_state)
result = tool.execute(params)
```

#### 系统状态

`SystemState` 跟踪：

- 当前工作目录
- 工具调用次数
- TODO 列表
- Shell 会话
- 环境信息

#### 系统提示注入

每次 LLM 调用前注入：

```xml
<system_hint>
# System State
Current Time: 2025-10-12 15:30:45
Working Directory: /Users/boj/coding-agent
OS: Darwin
Python: Python 3.11.5

# Tool Call Statistics
- Grep: 2 calls
- Write: 1 calls

# Current TODO List
✅ [1] Search for files (completed)
🔄 [2] Implement feature (in_progress)
⬜ [3] Write tests (pending)
</system_hint>
```

### 设计原则

#### 1. 纯 Python 实现

**为何：** 最大可移植性与兼容性

- 任意有 Python 的系统
- 无需 Homebrew、apt 等
- 跨平台行为一致

#### 2. 模块化工具架构

**为何：** 可维护、可扩展

- 工具自包含
- 易新增、易单测
- 关注点分离清晰

#### 3. 无命令行依赖

**为何：** 可靠与可控

- **Grep**：纯 Python 正则
- **Glob**：`pathlib.glob()`
- **LS**：`os` / `pathlib`
- 核心路径不靠 subprocess
- 行为完全可控

#### 4. System Hint 自我感知

**为何：** 更好的 Agent 行为

- 工具调用计数防死循环
- TODO 保持任务焦点
- 提供环境上下文
- 支持自我监控

### 与第 2 章对照

| Technique | Status | Implementation |
|-----------|--------|----------------|
| Standard OpenAI Tool Format | ✅ | Anthropic SDK |
| Streaming Tool Calls | ✅ | Real-time JSON delta parsing |
| Parallel Tool Calls | ✅ | Multiple tools per response |
| Pure Python Tools | ✅ | **No command-line dependencies** |
| Grep without rg | ✅ | **Pure Python regex search** |
| Timestamps | ✅ | All messages/tools |
| Tool Call Counting | ✅ | Warns at 3+ |
| TODO List | ✅ | TodoWrite tool |
| System State | ✅ | Working dir, OS, Python |
| Persistent Shell | ✅ | Shell sessions |
| Auto Lint Detection | ✅ | After Write/Edit/MultiEdit |

### 配置（`.env`）

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional
DEFAULT_MODEL=claude-sonnet-5
MAX_ITERATIONS=50
MAX_TOKENS=8192
```

### 添加新工具

1. 在 `tools/` 新建文件：

```python
# tools/my_tool.py
from .base import BaseTool

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "MyTool"
    
    def _execute_impl(self, params):
        # Implementation
        return {"result": "success"}
```

2. 在 `tools/__init__.py` 注册：

```python
from .my_tool import MyTool

__all__ = [..., 'MyTool']
```

3. 加入 `tool_registry.py`：

```python
self._tools = {
    ...,
    "MyTool": MyTool,
}
```

4. 在 `tools.json` 增加定义

### 故障排查

#### "No module named 'tools'"

请在项目目录运行：

```bash
cd /Users/boj/ai-agent-book/projects/week5/coding-agent
python agent.py
```

#### Grep 找不到文件

检查：

- 路径是否正确
- 模式是否为合法正则
- Glob 是否匹配目标文件
- 文件是否为可搜索文本（非二进制）

#### Shell 命令失败

确认：

- `/bin/bash` 可用
- 工作目录存在
- 命令引号正确

### 测试

130+ 用例覆盖主要工具能力。

#### 运行测试

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=tools --cov-report=html

# Run specific tool tests
pytest tests/test_grep_tool.py
pytest tests/test_bash_tool.py

# Verbose output
pytest -v
```

#### 覆盖情况

- **130+ 测试**，14 个测试文件
- **2,200+ 行**测试代码
- **tools.json 主要特性**均有覆盖
- **集成测试**覆盖工具链与 system hints

详见 [tests/README.md](tests/README.md)。

### 学习路径

1. **从示例开始**：`python main.py`（交互 CLI）
2. **跑 quickstart**：`python quickstart.py`
3. **看 system hints**：`python example_with_system_hints.py`
4. **研读 Grep**：`tools/grep_tool.py`
5. **跑测试**：`pytest -v`
6. **读第 2 章**：理解理论
7. **加自定义工具**：扩展系统

### 参考

- 第 2 章：上下文工程（AI Agent 书）
- 工具规范：`tools.json`
- 系统提示：`system-prompt.md`
- Anthropic Claude API：https://docs.anthropic.com/

### 关键优势

1. **无外部工具依赖**
   - 纯 Python
   - 无需 rg、grep、find 等
   - 适合未装 Homebrew 的 Mac

2. **模块化架构**
   - 每工具一文件
   - 易读易改
   - 关注点分离

3. **可生产使用**
   - 完善错误处理
   - 自动 lint
   - system hints 提升可靠性
   - 流式输出改善体验

4. **教学价值**
   - 理解工具内部
   - 纯 Python 文件操作
   - 正则搜索实现
   - Agent 架构模式

### 许可证

MIT

### 贡献

教学实现，欢迎改编与扩展！

---

**Built with pure Python for maximum portability and learning! 🐍✨**

---

## Notes / 说明

- Offline self-check: `python main.py --list-tools` (no API key). / 离线自检：`python main.py --list-tools`（无需 API Key）。
- Commands, code blocks, paths, and env vars are identical in both language sections. / 命令、代码块、路径与环境变量在中英文两侧保持一致。
- Historical path examples (`/Users/boj/...`) are kept as in the original docs. / 文档中的历史路径示例（`/Users/boj/...`）按原文保留。
