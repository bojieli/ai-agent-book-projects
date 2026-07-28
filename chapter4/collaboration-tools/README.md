# Collaboration Tools MCP Server / 协作工具 MCP 服务器

> Companion code for *AI Agents in Depth*, Chapter 4 — **Experiment 4-3 ★★**. MCP server: browser automation, sub-agents, HITL, multi-channel notifications, timers.  
> 配套《深入理解 AI Agent》第 4 章 **实验 4-3 ★★**。协作 MCP 服务器：浏览器、子 Agent、HITL、多渠道通知、定时器。

← [Chapter 4 index / 返回第 4 章目录](../README.md)

---

## English

A comprehensive Model Context Protocol (MCP) server that provides collaboration tools for AI agents, including browser automation, human-in-the-loop assistance, notifications, and timer management.

### Features

#### Browser Automation (using browser-use)
- Navigate to URLs and manage browser tabs
- Extract content from web pages
- Execute high-level browser tasks using AI agents
- Take screenshots
- Full virtual browser capabilities

#### Sub-Agent Management
- Spawn sub-agents in **sync** (wait for result) or **async** (returns a `task_id`) mode
- Send follow-up messages to a sub-agent and cancel a running one
- **Two context-passing strategies**, made inspectable (context text + token count):
  - `minimal` — pass only the task plus an optional hand-picked slice (cheapest, private, may starve the sub-agent)
  - `llm_generated` — one extra LLM call synthesizes a compact, privacy-filtered hand-off context from the parent trajectory
- Sub-agent system prompt uses labeled context sources (`[FROM_MAIN_AGENT]` / `[FROM_USER]` / `[TOOL_RESULT]`) and standardized JSON output

#### Human-in-the-Loop (HITL)
- Request admin approval for sensitive actions
- Request input from human administrators
- Manage pending approval requests
- Configurable timeout and notification channels

#### Email Notifications
- Send emails via SMTP or SendGrid
- Support for HTML emails
- CC recipients and attachments
- Flexible configuration

#### Instant Messaging
- Telegram bot integration
- Slack webhook support
- Discord webhook support
- Configurable default channels

#### Timer & Scheduling
- Set one-time timers
- Create recurring timers
- Cancel and manage timers
- Persistent timer storage
- Callback notifications when timers expire

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd chapter4/collaboration-tools
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the example environment file and configure it:
```bash
cp env.example .env
# Edit .env with your configuration
```

4. Install Playwright browsers (for browser automation):
```bash
playwright install chromium
```

### Configuration

Configure the server by setting environment variables in `.env`:

#### Browser Settings
```env
BROWSER_HEADLESS=false
BROWSER_USER_DATA_DIR=~/.config/collaboration-tools/browser
```

#### Email Configuration
```env
# SMTP (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Or use SendGrid
SENDGRID_API_KEY=your-sendgrid-api-key
```

#### Instant Messaging
```env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_DEFAULT_CHAT_ID=your-chat-id
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK
```

#### HITL Settings
```env
HITL_ADMIN_EMAIL=admin@example.com
HITL_TIMEOUT_SECONDS=3600
```

#### For Browser Tasks (AI Agent)
```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5.6-luna
```

> **Universal OpenRouter fallback**: all LLM entry points (`spawn_subagent`,
> intelligence tools, browser-use) resolve credentials via `src/llm_fallback.py`.
> When `OPENAI_API_KEY` is absent but `OPENROUTER_API_KEY` is set, they route
> through OpenRouter (`base_url=https://openrouter.ai/api/v1`, model id mapped to
> `provider/model` form, e.g. `gpt-5.6-luna` → `openai/gpt-5.6-luna`). With neither
> key set, sub-agents run in deterministic offline mode (no fabricated output).

### Usage

#### CLI entry (`main.py`)

Without starting the MCP server, use the unified CLI to list tools, call them individually, or run end-to-end demos. Help text is Chinese; `-h` works on any subcommand:

```bash
python main.py --help            # overview
python main.py list              # list all collaboration tools (sub-agent / HITL / multi-channel notify)
python main.py demo              # end-to-end collab demo: support agent handles a refund
python main.py subagent -h       # sub-agent subcommand help
python main.py hitl -h           # HITL subcommand help
python main.py notify -h         # notify subcommand help
```

Common examples:

```bash
# Compare two context-passing strategies (minimal vs llm_generated)
python main.py subagent compare

# Spawn sub-agent (sync, minimal context)
python main.py subagent spawn --task "查询订单 A12345 状态" --strategy minimal --role 订单查询助手

# Sensitive decision needs admin approval; --auto-approve simulates admin reply offline
python main.py hitl approve --message "删除 1000 条记录？" --timeout 5 --auto-approve

# Multi-channel notification
python main.py notify slack --message "部署完成"
```

`demo` chains three collaboration tool types: (1) delegate a sub-agent for refund approval and compare context strategies; (2) large action triggers HITL (approve-before-timeout vs conservative default-on-timeout); (3) multi-channel notify collaborators. **HITL and notify paths run fully offline**; real sub-agent execution and `llm_generated` need `OPENAI_API_KEY` (if unset, the command still parses and runs with a clear prompt).

#### Running the MCP Server

Start the server using stdio transport:
```bash
python src/main.py
```

Or use it as an MCP server with any MCP-compatible client.

#### Quick Start Demo

Run the quickstart demo to see all features in action:
```bash
python quickstart.py
```

#### Sub-Agent Context Strategy Comparison

Spawn a sub-agent under **both** context-passing strategies on the same task and
print the difference (context tokens handed off, extra preparation cost, whether
private data leaked, and each sub-agent's result). Requires `OPENAI_API_KEY`
(default model `gpt-5.6-luna`, override with `OPENAI_MODEL`):
```bash
export OPENAI_API_KEY=sk-...
python subagent_comparison.py
```
Typically `minimal` uses far fewer tokens and never leaks private fields, but the
sub-agent may return `need_info`; `llm_generated` spends one extra LLM call to
hand off richer, privacy-filtered context so the sub-agent can complete the task.

#### Using with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "collaboration-tools": {
      "command": "python",
      "args": ["/path/to/collaboration-tools/src/main.py"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### Available Tools

#### Browser Tools
- `mcp_browser_navigate` - Navigate to a URL
- `mcp_browser_get_content` - Get page content
- `mcp_browser_execute_task` - Execute AI-driven browser task
- `mcp_browser_screenshot` - Take a screenshot
- `mcp_browser_list_tabs` - List all open tabs

#### Notification Tools
- `mcp_send_email` - Send email notification
- `mcp_send_telegram_message` - Send Telegram message
- `mcp_send_slack_message` - Send Slack message
- `mcp_send_discord_message` - Send Discord message

#### Sub-Agent Tools
- `mcp_spawn_subagent` - Spawn a sub-agent (sync/async, `minimal`/`llm_generated` context)
- `mcp_send_message_to_subagent` - Send a follow-up message to a sub-agent
- `mcp_cancel_subagent` - Cancel a sub-agent
- `mcp_get_subagent_status` - Get a sub-agent's status/result (for async)

#### Human-in-the-Loop Tools
- `mcp_request_admin_approval` - Request admin approval
- `mcp_request_admin_input` - Request admin input
- `mcp_respond_to_request` - Respond to approval request (admin)
- `mcp_list_pending_requests` - List pending requests

#### Timer Tools
- `mcp_set_timer` - Set a one-time timer
- `mcp_set_recurring_timer` - Set a recurring timer
- `mcp_cancel_timer` - Cancel a timer
- `mcp_list_timers` - List all timers
- `mcp_get_timer_status` - Get timer status

### Example Usage

#### Browser Automation
```python
# Navigate to a website
await mcp_browser_navigate(url="https://example.com")

# Execute a complex task
await mcp_browser_execute_task(
    task="Search for AI agent tutorials on Google and extract the top 5 results"
)

# Take a screenshot
await mcp_browser_screenshot(full_page=True)
```

#### Notifications
```python
# Send email
await mcp_send_email(
    to_email="user@example.com",
    subject="Task Completed",
    body="Your task has finished successfully!"
)

# Send Slack message
await mcp_send_slack_message(
    message="🎉 Deployment successful!"
)
```

#### Human-in-the-Loop
```python
# Request approval for sensitive action
result = await mcp_request_admin_approval(
    request_message="Delete 1000 records from database?",
    urgent=True,
    timeout_seconds=300
)

if result["approved"]:
    # Proceed with action
    pass
```

#### Timers
```python
# Set a timer
await mcp_set_timer(
    duration_seconds=300,
    timer_name="Check website",
    callback_message="Time to check the website status"
)

# Set recurring timer
await mcp_set_recurring_timer(
    interval_seconds=3600,
    max_occurrences=24,
    timer_name="Hourly health check"
)
```

### Architecture

The server is organized into modular components:

```
collaboration-tools/
├── src/
│   ├── main.py              # MCP server entry point
│   ├── config.py            # Configuration management
│   ├── browser_tools.py     # Browser automation
│   ├── notification_tools.py # Email & IM notifications
│   ├── hitl_tools.py        # Human-in-the-loop
│   └── timer_tools.py       # Timer management
├── requirements.txt         # Python dependencies
├── env.example             # Example configuration
└── README.md               # This file
```

### Requirements

- Python 3.11+
- OpenAI API key (for browser AI agent tasks)
- Optional: Email/IM service credentials
- Playwright browsers for browser automation

### Troubleshooting

#### Browser Issues
If browser automation fails:
```bash
# Reinstall Playwright browsers
playwright install chromium --force
```

#### Email Issues
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Ensure "Less secure app access" is NOT enabled (use App Passwords instead)

#### Telegram Issues
- Create a bot via [@BotFather](https://t.me/botfather)
- Get your chat ID from [@userinfobot](https://t.me/userinfobot)

#### LangChain/Pydantic Issues
If you see errors like "`ChatOpenAI` is not fully defined" or Pydantic validation errors:
- This is a known compatibility issue between LangChain and Pydantic v2
- The fix: ChatOpenAI is now initialized on-demand only when needed (in `browser_execute_task`)
- Simple browser navigation doesn't require OpenAI API key
- Only autonomous browser tasks (`browser_execute_task`) require `OPENAI_API_KEY`

### License

MIT License

### Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## 中文

为 AI Agent 提供协作能力的综合 Model Context Protocol（MCP）服务器，涵盖浏览器自动化、人机协同、通知与定时器管理。

### 功能

#### 浏览器自动化（browser-use）
- 导航 URL、管理标签页
- 抽取网页内容
- 用 AI Agent 执行高层浏览器任务
- 截图
- 完整虚拟浏览器能力

#### 子 Agent 管理
- 以 **sync**（等待结果）或 **async**（返回 `task_id`）模式 spawn 子 Agent
- 向子 Agent 发送后续消息、取消运行中的子 Agent
- **两种上下文传递策略**（可检查上下文文本与 token 数）：
  - `minimal` — 只传任务 + 可选手选片段（最省、隐私好，可能饿死子 Agent）
  - `llm_generated` — 额外一次 LLM 调用，从父轨迹合成紧凑、隐私过滤的交接上下文
- 子 Agent system prompt 使用带标签的上下文来源（`[FROM_MAIN_AGENT]` / `[FROM_USER]` / `[TOOL_RESULT]`）与标准化 JSON 输出

#### 人机协同（HITL）
- 敏感操作请求管理员审批
- 向人类管理员请求输入
- 管理待处理审批
- 可配置超时与通知渠道

#### 邮件通知
- 经 SMTP 或 SendGrid 发信
- 支持 HTML
- 抄送与附件
- 灵活配置

#### 即时通讯
- Telegram bot
- Slack webhook
- Discord webhook
- 可配置默认频道

#### 定时器与调度
- 一次性定时器
- 循环定时器
- 取消与管理
- 持久化存储
- 到期回调通知

### 安装

1. 进入项目目录：
```bash
cd chapter4/collaboration-tools
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 复制环境模板并配置：
```bash
cp env.example .env
# Edit .env with your configuration
```

4. 安装 Playwright 浏览器（浏览器自动化）：
```bash
playwright install chromium
```

### 配置

在 `.env` 中设置环境变量：

#### 浏览器
```env
BROWSER_HEADLESS=false
BROWSER_USER_DATA_DIR=~/.config/collaboration-tools/browser
```

#### 邮件
```env
# SMTP (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Or use SendGrid
SENDGRID_API_KEY=your-sendgrid-api-key
```

#### 即时通讯
```env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_DEFAULT_CHAT_ID=your-chat-id
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK
```

#### HITL
```env
HITL_ADMIN_EMAIL=admin@example.com
HITL_TIMEOUT_SECONDS=3600
```

#### 浏览器任务（AI Agent）
```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5.6-luna
```

> **OpenRouter 通用兜底**：所有 LLM 入口（`spawn_subagent`、
> intelligence 工具、browser-use）经 `src/llm_fallback.py` 解析凭据。
> 未设置 `OPENAI_API_KEY` 但设置了 `OPENROUTER_API_KEY` 时，走
> OpenRouter（`base_url=https://openrouter.ai/api/v1`，模型 id 映射为
> `provider/model`，如 `gpt-5.6-luna` → `openai/gpt-5.6-luna`）。两者皆无时，
> 子 Agent 以确定性离线模式运行（不编造输出）。

### 使用

#### 命令行入口（`main.py`）

不启动 MCP 服务器，也可以用统一的命令行入口列出、单独调用协作工具，或运行端到端演示。
帮助信息为中文，`-h` 可查看任意子命令的参数：

```bash
python main.py --help            # 总览
python main.py list              # 列出全部协作工具（子 Agent / HITL / 多渠道通知）
python main.py demo              # 端到端协作演示：客服协调 Agent 处理一笔退款
python main.py subagent -h       # 子 Agent 子命令帮助
python main.py hitl -h           # HITL 子命令帮助
python main.py notify -h         # 通知子命令帮助
```

常用示例：

```bash
# 对比两种上下文传递策略（minimal vs llm_generated）
python main.py subagent compare

# 创建子 Agent（同步、最小化上下文）
python main.py subagent spawn --task "查询订单 A12345 状态" --strategy minimal --role 订单查询助手

# 关键决策请求管理员批准；--auto-approve 在后台模拟管理员应答，便于离线演示闭环
python main.py hitl approve --message "删除 1000 条记录？" --timeout 5 --auto-approve

# 多渠道通知
python main.py notify slack --message "部署完成"
```

`demo` 会串联三类协作工具：① 委派子 Agent 审批退款并对比上下文策略；② 大额操作
触发 HITL 审批（演示"超时前批准"与"超时保守默认"两种路径）；③ 向协作者多渠道通知结果。
其中 **HITL 与通知路径完全离线可跑**；子 Agent 的真实执行与 `llm_generated` 策略需要
`OPENAI_API_KEY`（未配置时会明确提示，命令仍可正常解析运行）。

#### 运行 MCP 服务器

使用 stdio 传输启动：
```bash
python src/main.py
```

也可作为 MCP 服务器接入任意兼容客户端。

#### 快速演示

```bash
python quickstart.py
```

#### 子 Agent 上下文策略对比

对同一任务分别用**两种**上下文传递策略 spawn，并打印差异（交接 token、额外准备成本、
是否泄漏隐私字段、各子 Agent 结果）。需要 `OPENAI_API_KEY`
（默认模型 `gpt-5.6-luna`，可用 `OPENAI_MODEL` 覆盖）：
```bash
export OPENAI_API_KEY=sk-...
python subagent_comparison.py
```
通常 `minimal` token 更少且不泄漏隐私字段，但子 Agent 可能返回 `need_info`；
`llm_generated` 多一次 LLM 调用交接更丰富、经隐私过滤的上下文，便于子 Agent 完成任务。

#### 与 Claude Desktop 联用

在 Claude Desktop 配置（`claude_desktop_config.json`）中加入：

```json
{
  "mcpServers": {
    "collaboration-tools": {
      "command": "python",
      "args": ["/path/to/collaboration-tools/src/main.py"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### 可用工具

#### 浏览器工具
- `mcp_browser_navigate` — 导航到 URL
- `mcp_browser_get_content` — 获取页面内容
- `mcp_browser_execute_task` — 执行 AI 驱动的浏览器任务
- `mcp_browser_screenshot` — 截图
- `mcp_browser_list_tabs` — 列出标签页

#### 通知工具
- `mcp_send_email` — 发送邮件
- `mcp_send_telegram_message` — Telegram 消息
- `mcp_send_slack_message` — Slack 消息
- `mcp_send_discord_message` — Discord 消息

#### 子 Agent 工具
- `mcp_spawn_subagent` — 创建子 Agent（sync/async，`minimal`/`llm_generated` 上下文）
- `mcp_send_message_to_subagent` — 向子 Agent 发后续消息
- `mcp_cancel_subagent` — 取消子 Agent
- `mcp_get_subagent_status` — 查询状态/结果（async）

#### HITL 工具
- `mcp_request_admin_approval` — 请求管理员审批
- `mcp_request_admin_input` — 请求管理员输入
- `mcp_respond_to_request` — 响应审批请求（管理员侧）
- `mcp_list_pending_requests` — 列出待处理请求

#### 定时器工具
- `mcp_set_timer` — 一次性定时器
- `mcp_set_recurring_timer` — 循环定时器
- `mcp_cancel_timer` — 取消定时器
- `mcp_list_timers` — 列出定时器
- `mcp_get_timer_status` — 查询定时器状态

### 使用示例

#### 浏览器自动化
```python
# Navigate to a website
await mcp_browser_navigate(url="https://example.com")

# Execute a complex task
await mcp_browser_execute_task(
    task="Search for AI agent tutorials on Google and extract the top 5 results"
)

# Take a screenshot
await mcp_browser_screenshot(full_page=True)
```

#### 通知
```python
# Send email
await mcp_send_email(
    to_email="user@example.com",
    subject="Task Completed",
    body="Your task has finished successfully!"
)

# Send Slack message
await mcp_send_slack_message(
    message="🎉 Deployment successful!"
)
```

#### 人机协同
```python
# Request approval for sensitive action
result = await mcp_request_admin_approval(
    request_message="Delete 1000 records from database?",
    urgent=True,
    timeout_seconds=300
)

if result["approved"]:
    # Proceed with action
    pass
```

#### 定时器
```python
# Set a timer
await mcp_set_timer(
    duration_seconds=300,
    timer_name="Check website",
    callback_message="Time to check the website status"
)

# Set recurring timer
await mcp_set_recurring_timer(
    interval_seconds=3600,
    max_occurrences=24,
    timer_name="Hourly health check"
)
```

### 架构

服务器按模块组织：

```
collaboration-tools/
├── src/
│   ├── main.py              # MCP server entry point
│   ├── config.py            # Configuration management
│   ├── browser_tools.py     # Browser automation
│   ├── notification_tools.py # Email & IM notifications
│   ├── hitl_tools.py        # Human-in-the-loop
│   └── timer_tools.py       # Timer management
├── requirements.txt         # Python dependencies
├── env.example             # Example configuration
└── README.md               # This file
```

### 依赖要求

- Python 3.11+
- OpenAI API key（浏览器 AI 任务）
- 可选：邮件/IM 凭据
- Playwright 浏览器（浏览器自动化）

### 故障排除

#### 浏览器问题
若浏览器自动化失败：
```bash
# Reinstall Playwright browsers
playwright install chromium --force
```

#### 邮件问题
- Gmail 请使用 [应用专用密码](https://support.google.com/accounts/answer/185833)
- 不要开启「不够安全的应用访问」（改用应用专用密码）

#### Telegram 问题
- 通过 [@BotFather](https://t.me/botfather) 创建 bot
- 用 [@userinfobot](https://t.me/userinfobot) 获取 chat ID

#### LangChain/Pydantic 问题
若出现 "`ChatOpenAI` is not fully defined" 或 Pydantic 校验错误：
- 这是 LangChain 与 Pydantic v2 的已知兼容问题
- 修复：ChatOpenAI 仅在需要时按需初始化（`browser_execute_task`）
- 简单导航不需要 OpenAI API key
- 仅自主浏览器任务（`browser_execute_task`）需要 `OPENAI_API_KEY`

### 许可证

MIT License

### 贡献

欢迎提交 issue 或 pull request。

---

## Notes / 说明

- HITL + notify paths in `python main.py demo` run offline without API keys.  
- `python main.py demo` 中 HITL 与通知路径可离线、无需 API Key。  
- Browser AI tasks and `llm_generated` sub-agent strategy need an LLM key.  
- 浏览器 AI 任务与 `llm_generated` 子 Agent 策略需要 LLM Key。
