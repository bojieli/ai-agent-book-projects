# GPT-5 Native Tools Agent / GPT-5 原生工具 Agent

> GPT-5 native `web_search` + `code_interpreter` via OpenRouter — Deep Research loop: search → read → analyze → search again.  
> 配套《深入理解 AI Agent》第 1 章 **实验 1-3 ★：GPT-5.6 原生 Deep Research 能力**。

← [Chapter 1 index / 返回第 1 章目录](../README.md) · 📖 [Read the chapter / 读本章正文](../../book/chapter1.md)（[EN](../../book-en/chapter1.md)）

---

## English

### Overview

An advanced AI agent leveraging GPT-5's native `web_search` and `code_interpreter` tools through the OpenRouter API, matching the exact implementation pattern from production Go code. This agent can search the internet for real-time information and run code for deep analysis using GPT-5's built-in capabilities, realizing the “search → read → analyze → search again” Deep Research loop.

### Features

- **Native Tool Support**: Utilizes GPT-5's built-in `web_search` and `code_interpreter` tools with OpenRouter-specific format
- **OpenRouter Integration**: Exact API format matching production Go implementation
- **Web Search Capability**:
  - Real-time internet search for current information
  - Configurable search context size and user location
- **Reasoning Levels**: Support for low, medium, and high reasoning effort
- **Interactive CLI**: User-friendly command-line interface with reasoning controls
- **Agent Chaining**: Chain multiple requests for complex workflows
- **Comprehensive Testing**: Test suite demonstrating various use cases

### Prerequisites

- Python 3.8 or higher
- OpenRouter API key (get one at [https://openrouter.ai/keys](https://openrouter.ai/keys))
- Internet connection for web search functionality

### Quick Start

#### 1. Installation

```bash
# Clone or navigate to the project directory
cd chapter1/search-codegen

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env

# Edit .env and add your OpenRouter API key
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

#### 2. Configuration

Edit `.env` file with your settings:

```env
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
MODEL_NAME=openai/gpt-5.6-sol
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=4000
```

> This experiment uses OpenRouter as its **primary** backend, so no fallback is needed. The same `OPENROUTER_API_KEY` doubles as the **universal fallback** for the other chapter1 experiments (`context`, `learning-from-experience`, `web-search-agent`) when their direct provider key is missing.

#### 3. Run the Agent

**Interactive mode (recommended):**

```bash
python main.py
```

**Single request mode:**

```bash
python main.py --mode single --request "Search for latest AI news and analyze the trends"
```

**Run tests:**

```bash
python main.py --mode test
```

### CLI Arguments

Run `python main.py --help` for the full (Chinese) help text.

| Flag | Description | Default |
|------|-------------|---------|
| `--mode` | Run mode: `interactive` / `single` / `test` | `interactive` |
| `--request` | Task or query for `single` / `--dry-run` | — |
| `--model` | Override model name | `MODEL_NAME` from config |
| `--reasoning` | Reasoning effort (`low` / `medium` / `high`) | `low` |
| `--verbosity` | Output verbosity (`low` / `medium` / `high`) | model default |
| `--no-tools` | Disable native tools | tools enabled |
| `--output` | Save full result (trace / request body) as JSON | — |
| `--dry-run` | Offline assemble and print request body; no network, no API key | off |
| `--test` | In `test` mode, run a named case | all tests |

**Reasoning Effort** and **Verbosity** are the two GPT-5 native knobs highlighted in the book: the former controls thinking depth, the latter answer detail. Both are exposed on the CLI and injected into the request body as-is.

Examples:

```bash
# Book example: closest pair among ASEAN 10 capitals (search coords + code great-circle distance)
python main.py --mode single --request "东盟 10 国首都之间距离最近的两个首都是？给出详细分析推理过程。" --reasoning high

# Book example: Bitcoin technical analysis (multi-source live data + indicators)
python main.py --mode single --request "搜索比特币最近一个月走势，计算 MA、RSI、MACD 等技术指标" --verbosity high --output btc.json
```

### Offline Request Body (dry-run)

Inspect the real request under the “model as Agent” paradigm—including both native tool definitions plus `reasoning` and `verbosity`—without an API key:

```bash
python main.py --dry-run --request "东盟 10 国首都之间距离最近的两个首都是？" --reasoning high --verbosity high
```

In the printed body, the `tools` array includes both `web_search` and `code_interpreter`, and `reasoning.effort` / `verbosity` reflect the chosen levels—the native tools + reasoning/verbosity combination described in the book.

### Usage Examples

#### Example 1: Web Search Only

```python
from agent import GPT5NativeAgent
from config import Config

agent = GPT5NativeAgent(
    api_key=Config.OPENROUTER_API_KEY,
    base_url=Config.OPENROUTER_BASE_URL
)

result = agent.process_request(
    "What are the latest developments in quantum computing?",
    use_tools=True
)
print(result["response"])
```

#### Example 2: Web Search with High Reasoning

```python
result = agent.process_request(
    "Analyze the implications of quantum computing on encryption",
    use_tools=True,
    reasoning_effort="high"
)
```

#### Example 3: Web Search with Analysis

```python
result = agent.process_request(
    """Search for current Bitcoin price and market data, 
    then analyze the volatility and predict trends""",
    use_tools=True,
    reasoning_effort="medium"
)
```

#### Example 4: Search and Analyze Method

```python
analysis_code = """
import statistics
# Process search results
prices = [45000, 46000, 45500, 47000, 46500]
volatility = statistics.stdev(prices)
print(f"Volatility: ${volatility:.2f}")
"""

result = agent.search_and_analyze(
    topic="Current cryptocurrency market conditions",
    analysis_code=analysis_code
)
```

### Project Structure

```
search-codegen/
├── agent.py          # Core GPT-5 agent implementation
├── config.py         # Configuration management
├── main.py           # Interactive CLI and entry point
├── test_agent.py     # Comprehensive test suite
├── env.example       # Environment variables template
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

### OpenRouter Tool Format

#### web_search Tool Structure

The web_search tool uses OpenRouter's specific format:

```python
{
    "type": "web_search",
    "search_context_size": "medium",
    "user_location": {
        "type": "approximate",
        "country": "US"
    }
}
```

#### Reasoning Configuration

Supports configurable reasoning effort:

- **low**: Fast responses with basic reasoning
- **medium**: Balanced reasoning and response time
- **high**: Deep reasoning for complex queries

### Testing

The test suite includes comprehensive test cases:

1. **Basic Web Search**: Test internet search capabilities
2. **Web Search with Analysis**: Search with analytical insights
3. **Complex Research**: Deep research with high reasoning
4. **Search and Code**: Search with code generation
5. **Reasoning Comparison**: Compare different reasoning levels
6. **Search and Analyze Method**: Convenience method testing
7. **Agent Chain**: Multi-step workflow

```bash
# Run all tests
python test_agent.py

# Run specific test
python main.py --mode test --test basic
```

Available test names: `basic`, `analysis`, `complex`, `code`, `reasoning`, `search_analyze`, `chain`

### Interactive CLI Commands

When running in interactive mode:

- `/help` — Show help message
- `/clear` — Clear conversation history
- `/history` — Show conversation history
- `/tools` — Toggle tools on/off
- `/search` — Enter web search mode
- `/code` — Enter code generation mode
- `/analyze` — Combined search + analysis mode
- `/config` — Show current configuration
- `/reasoning` — Set reasoning effort level
- `/exit` — Exit the application

### Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Required |
| `MODEL_NAME` | GPT-5 model identifier | `openai/gpt-5.6-sol` |
| `DEFAULT_TEMPERATURE` | Response randomness (0-1) | `0.3` |
| `DEFAULT_MAX_TOKENS` | Maximum response length | `4000` |
| `DEFAULT_TOOL_CHOICE` | Tool selection strategy | `auto` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### API Integration

This agent uses the OpenRouter API to access GPT-5. OpenRouter provides:

- Unified API for multiple models
- Automatic fallbacks for reliability
- Usage tracking and analytics
- Competitive pricing

Learn more at [OpenRouter Documentation](https://openrouter.ai/docs).

### Token Usage

The agent tracks token usage for each request:

- Prompt tokens: Input token count
- Completion tokens: Output token count
- Total tokens: Combined usage

Monitor costs based on OpenRouter's pricing for `openai/gpt-5.6-sol` (verified 2026-07-24; check the [model page](https://openrouter.ai/openai/gpt-5.6-sol) for current rates):

- Input: $5 per million tokens
- Output: $30 per million tokens

### Troubleshooting

#### API Key Issues

```bash
# Verify your API key starts with 'sk-or-'
echo $OPENROUTER_API_KEY
```

#### Rate Limiting

Adjust `RATE_LIMIT_RPM` in `.env` if encountering rate limits.

#### Tool Errors

- Ensure `use_tools=True` when calling `process_request`
- Set `tool_choice="required"` to force tool usage

### Resources

- [OpenRouter GPT-5 API](https://openrouter.ai/openai/gpt-5.6-sol)
- [OpenAI Native Tools Documentation](https://platform.openai.com/docs/guides/tools)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [API Keys](https://openrouter.ai/keys)

---

## 中文

### 概述

本项目通过 OpenRouter API 调用 GPT-5 原生 `web_search` 与 `code_interpreter` 工具，API 形态对齐生产环境 Go 实现。Agent 可联网检索实时信息，并写代码做深度分析，实现“搜索 → 阅读 → 分析 → 再搜索”的 Deep Research 循环。对应书中**实验 1-3 ★：GPT-5.6 原生 Deep Research 能力**。

### 特性

- **原生工具支持**：以 OpenRouter 特定格式使用 GPT-5 内置 `web_search` 与 `code_interpreter`
- **OpenRouter 集成**：请求格式与生产 Go 实现一致
- **网络搜索**：
  - 实时检索当前信息
  - 可配置搜索上下文大小与用户位置
- **推理档位**：支持 low / medium / high 推理力度
- **交互式 CLI**：带推理控制的命令行界面
- **Agent 串联**：多请求链式工作流
- **完整测试**：覆盖多种用例的测试套件

### 前置条件

- Python 3.8 或更高  
- OpenRouter API Key（[https://openrouter.ai/keys](https://openrouter.ai/keys)）  
- 需要联网才能使用搜索功能  

### 快速开始

#### 1. 安装

```bash
# Clone or navigate to the project directory
cd chapter1/search-codegen

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env

# Edit .env and add your OpenRouter API key
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

#### 2. 配置

编辑 `.env`：

```env
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
MODEL_NAME=openai/gpt-5.6-sol
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=4000
```

> 本实验以 OpenRouter 为**主后端**，无需再配其他兜底。同一 `OPENROUTER_API_KEY` 也是其他第 1 章实验（`context`、`learning-from-experience`、`web-search-agent`）在直连 Key 缺失时的**通用兜底**。

#### 3. 运行 Agent

**交互模式（推荐）：**

```bash
python main.py
```

**单次请求：**

```bash
python main.py --mode single --request "Search for latest AI news and analyze the trends"
```

**运行测试：**

```bash
python main.py --mode test
```

### 命令行参数（CLI）

运行 `python main.py --help` 查看完整中文帮助。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--mode` | 运行模式：`interactive` 交互 / `single` 单次 / `test` 测试 | `interactive` |
| `--request` | `single` / `--dry-run` 模式下的任务或查询内容 | — |
| `--model` | 覆盖模型名称 | 配置中的 `MODEL_NAME` |
| `--reasoning` | 推理力度 Reasoning Effort（`low`/`medium`/`high`） | `low` |
| `--verbosity` | 输出详略程度 Verbosity（`low`/`medium`/`high`） | 跟随模型 |
| `--no-tools` | 禁用原生工具 | 启用 |
| `--output` | 将完整结果（含轨迹 / 请求体）保存为 JSON | — |
| `--dry-run` | 离线组装并打印请求体，不联网、无需 API Key | 关闭 |
| `--test` | `test` 模式下运行指定用例 | 运行全部 |

**Reasoning Effort** 与 **Verbosity** 是书中强调的两个 GPT-5 原生参数：前者调节思考深度，后者控制回答详略。二者都已通过 CLI 暴露，并原样注入到发送给模型的请求体中。

示例：

```bash
# 书中示例任务：东盟 10 国首都最近的一对（搜索坐标 + 代码计算大圆距离）
python main.py --mode single --request "东盟 10 国首都之间距离最近的两个首都是？给出详细分析推理过程。" --reasoning high

# 书中示例任务：比特币技术分析（多源实时数据 + 指标计算）
python main.py --mode single --request "搜索比特币最近一个月走势，计算 MA、RSI、MACD 等技术指标" --verbosity high --output btc.json
```

### 离线查看请求体（dry-run）

无需 API Key 即可查看“模型即 Agent”范式下真正发送给模型的请求——包括两个原生工具的定义、`reasoning` 与 `verbosity` 参数：

```bash
python main.py --dry-run --request "东盟 10 国首都之间距离最近的两个首都是？" --reasoning high --verbosity high
```

输出的请求体中，`tools` 数组同时包含 `web_search` 和 `code_interpreter`，`reasoning.effort` 与 `verbosity` 反映所选档位——正是书中所述的原生工具 + 推理/详略参数的组合。

### 使用示例

#### 示例 1：仅网络搜索

```python
from agent import GPT5NativeAgent
from config import Config

agent = GPT5NativeAgent(
    api_key=Config.OPENROUTER_API_KEY,
    base_url=Config.OPENROUTER_BASE_URL
)

result = agent.process_request(
    "What are the latest developments in quantum computing?",
    use_tools=True
)
print(result["response"])
```

#### 示例 2：高推理力度搜索

```python
result = agent.process_request(
    "Analyze the implications of quantum computing on encryption",
    use_tools=True,
    reasoning_effort="high"
)
```

#### 示例 3：搜索 + 分析

```python
result = agent.process_request(
    """Search for current Bitcoin price and market data, 
    then analyze the volatility and predict trends""",
    use_tools=True,
    reasoning_effort="medium"
)
```

#### 示例 4：search_and_analyze 方法

```python
analysis_code = """
import statistics
# Process search results
prices = [45000, 46000, 45500, 47000, 46500]
volatility = statistics.stdev(prices)
print(f"Volatility: ${volatility:.2f}")
"""

result = agent.search_and_analyze(
    topic="Current cryptocurrency market conditions",
    analysis_code=analysis_code
)
```

### 项目结构

```
search-codegen/
├── agent.py          # Core GPT-5 agent implementation
├── config.py         # Configuration management
├── main.py           # Interactive CLI and entry point
├── test_agent.py     # Comprehensive test suite
├── env.example       # Environment variables template
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

### OpenRouter 工具格式

#### web_search 结构

web_search 使用 OpenRouter 特定格式：

```python
{
    "type": "web_search",
    "search_context_size": "medium",
    "user_location": {
        "type": "approximate",
        "country": "US"
    }
}
```

#### 推理配置

可配置推理力度：

- **low**：快速响应、基础推理  
- **medium**：推理深度与响应时间平衡  
- **high**：复杂查询的深度推理  

### 测试

测试套件覆盖：

1. **Basic Web Search**：基础联网搜索  
2. **Web Search with Analysis**：搜索 + 分析  
3. **Complex Research**：高推理深度研究  
4. **Search and Code**：搜索 + 代码生成  
5. **Reasoning Comparison**：对比不同推理档位  
6. **Search and Analyze Method**：便捷方法测试  
7. **Agent Chain**：多步工作流  

```bash
# Run all tests
python test_agent.py

# Run specific test
python main.py --mode test --test basic
```

可用测试名：`basic`、`analysis`、`complex`、`code`、`reasoning`、`search_analyze`、`chain`

### 交互式 CLI 命令

交互模式下可用：

- `/help` — 显示帮助  
- `/clear` — 清空对话历史  
- `/history` — 显示对话历史  
- `/tools` — 开关工具  
- `/search` — 进入网络搜索模式  
- `/code` — 进入代码生成模式  
- `/analyze` — 搜索 + 分析模式  
- `/config` — 显示当前配置  
- `/reasoning` — 设置推理力度  
- `/exit` — 退出  

### 配置项

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENROUTER_API_KEY` | OpenRouter API 密钥 | 必填 |
| `MODEL_NAME` | GPT-5 模型标识 | `openai/gpt-5.6-sol` |
| `DEFAULT_TEMPERATURE` | 随机性（0–1） | `0.3` |
| `DEFAULT_MAX_TOKENS` | 最大回复长度 | `4000` |
| `DEFAULT_TOOL_CHOICE` | 工具选择策略 | `auto` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

### API 集成

通过 OpenRouter 访问 GPT-5。OpenRouter 提供：

- 多模型统一 API  
- 可靠性自动回退  
- 用量追踪与分析  
- 有竞争力的定价  

详见 [OpenRouter Documentation](https://openrouter.ai/docs)。

### Token 用量

每次请求会统计：

- Prompt tokens：输入  
- Completion tokens：输出  
- Total tokens：合计  

可参考 OpenRouter 上 `openai/gpt-5.6-sol` 的定价监控成本（2026-07-24 核对；最新价格见[模型页](https://openrouter.ai/openai/gpt-5.6-sol)）：

- 输入：$5 / 百万 tokens  
- 输出：$30 / 百万 tokens  

### 故障排查

#### API Key 问题

```bash
# Verify your API key starts with 'sk-or-'
echo $OPENROUTER_API_KEY
```

#### 限流

若遇限流，可在 `.env` 中调整 `RATE_LIMIT_RPM`。

#### 工具错误

- 调用 `process_request` 时确保 `use_tools=True`  
- 可设 `tool_choice="required"` 强制使用工具  

### 相关链接

- [OpenRouter GPT-5 API](https://openrouter.ai/openai/gpt-5.6-sol)
- [OpenAI Native Tools Documentation](https://platform.openai.com/docs/guides/tools)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [API Keys](https://openrouter.ai/keys)

---

## Notes / 说明

- Part of the AI Agent curriculum / 属于 AI Agent 实战训练营课程材料。  
- Prefer interactive mode for exploration; use `--dry-run` to inspect request shape without spending tokens.  
  探索时优先用交互模式；用 `--dry-run` 可在不消耗 token 的情况下查看请求结构。  
- Built with GPT-5 native capabilities via OpenRouter.  
  基于 OpenRouter 上的 GPT-5 原生能力构建。  
