# Kimi Web Search Agent / Kimi 网络搜索 Agent

> Autonomous ReAct web-search agent on Kimi K3 with built-in `$web_search` (multi-round search + synthesis).  
> 配套《深入理解 AI Agent》第 1 章 **实验 1-2 ★：Kimi K3 原生 Agent 能力**。

← [Chapter 1 index / 返回第 1 章目录](../README.md) · 📖 [Read the chapter / 读本章正文](../../book/chapter1.md)（[EN](../../book-en/chapter1.md)）

---

## English

### Overview

This project implements an autonomous AI agent that uses Kimi (Moonshot AI) built-in web tools (`$web_search` / crawl-style search) to:

- **Understand the question**: analyze the user query and identify information needs
- **Search automatically**: fetch live web information via Kimi’s built-in `$web_search` tool
- **Iterate**: call search multiple times until evidence is sufficient
- **Synthesize**: combine multi-source results into a clear, accurate answer

It demonstrates the “Model as Agent” idea and the ReAct loop (think → act → observe).

### Kimi web-search service status

This example depends on Kimi's hosted `$web_search` service. The repository only
passes the built-in tool's arguments back to Kimi; it does not execute a search
engine locally.

Kimi's [official web-search documentation](https://platform.kimi.ai/docs/guide/use-web-search)
currently says that the service is being updated, advises against using it in the
near term, and asks developers to follow later documentation updates. Check that
page for the latest status before troubleshooting this example.

If a tool observation contains only a `search_id`, for example
`{"search_result": {"search_id": "..."}}`, but no search-result content:

1. Check Kimi's web-search documentation for the current service status.
2. Retry later, or use `python main.py --provider offline-demo` to inspect the
   ReAct flow without calling the hosted service.
3. Treat the response as a possible external tool/API availability issue; by
   itself, it does not show that the agent loop or local implementation is broken.

### Architecture

```mermaid
graph TD
    A[User question] --> B{Agent thinks}
    B -->|needs search| C[Call $web_search]
    C --> D[Kimi search backend]
    D --> E[Search results]
    E --> F{Enough info?}
    F -->|no| G[Call $web_search again]
    G --> H[More information]
    H --> F
    F -->|yes| I[Final answer]
    B -->|no search needed| J[Answer directly]
```

### Quick Start

#### 1. Install dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure API Key

Get a key from the [Moonshot AI platform](https://platform.moonshot.ai/), then set:

```bash
export MOONSHOT_API_KEY='your-api-key-here'
```

Or create a `.env` file:

```env
MOONSHOT_API_KEY=your-api-key-here
```

**Note**: For backward compatibility, `KIMI_API_KEY` is also accepted.

**Universal OpenRouter fallback**: if neither `MOONSHOT_API_KEY` nor `KIMI_API_KEY` is set but `OPENROUTER_API_KEY` is, requests go through OpenRouter using `OPENROUTER_MODEL` (default `openai/gpt-5.6-luna`). **Important limit**: Kimi’s built-in `$web_search` is Moonshot-only and is **not** available on OpenRouter—fallback mode answers from the model’s knowledge only, **without live web search**. Use a Moonshot key for real online search.

#### 3. Run the Agent

`main.py` provides a full CLI (Chinese help). List all flags:

```bash
python main.py --help
```

| Flag | Description | Default |
|------|-------------|---------|
| `query` | Question (positional); omit for interactive mode | none |
| `--provider` | Backend: `kimi` (built-in `$web_search`, needs API key) / `offline-demo` (offline sample trace) | `kimi` |
| `--model` | Model name | `kimi-k3` |
| `--max-steps` | Max ReAct iterations | `5` |
| `--base-url` | API base URL | `https://api.moonshot.cn/v1` |
| `--api-key` | Kimi API key (else from env) | env |
| `--output`, `-o` | Save question, ReAct trace, and answer as JSON | none |
| `--quiet` | Do not stream ReAct trace live | stream on |

**Offline ReAct demo** (no API key; replays a sample trace to show think → act → observe):

```bash
python main.py --provider offline-demo
```

**Interactive mode** (ongoing dialogue):

```bash
python main.py
```

**Single question** (streams think / act / observe steps):

```bash
python main.py "2024年诺贝尔物理学奖获得者是谁？"
python main.py "比特币现价" --max-steps 3 --output result.json
```

**Guided quickstart**:

```bash
python quickstart.py
```

**Advanced examples**:

```bash
python examples.py
```

> At runtime the agent prints a **ReAct trace**: 💭 think → 🔧 act (`$web_search`) → 👀 observe (results) → ✅ final answer. Use `agent.get_trace()` for a structured trace, or `--output` to save JSON.

### Usage Examples

#### Basic usage

```python
from agent import WebSearchAgent
from config import Config

# Create Agent
agent = WebSearchAgent(api_key=Config.get_api_key())

# Ask and get an answer
question = "Python 3.12 有哪些新特性？"
answer = agent.search_and_answer(question)
print(answer)
```

#### Advanced features

```bash
python examples.py
```

Includes:

- **Batch search**: multiple questions in one run
- **Context-aware search**: supply background for sharper queries
- **Comparative search**: search and compare items
- **Fact check**: verify claims
- **Research assistant**: deeper topic research

### Core Components

#### `agent.py` — core agent

- `WebSearchAgent`: main agent class
- `search_and_answer()`: run the ReAct loop and produce an answer
- `get_trace()`: structured ReAct trace of the last run (think / act / observe / final)
- `_chat()`: chat with the Kimi API
- `_get_system_prompt()`: system prompt defining agent behavior
- `_get_tools()`: tool definitions (`$web_search`)
- `search_impl()`: search implementation layer (extension point)
- `format_trace_step()`: render one trace step as readable text
- `run_offline_demo()`: offline sample-trace replay (no API key)

#### `config.py` — configuration

- API settings
- Model selection
- Search parameters

#### `main.py` — entry point

- `build_parser()`: argparse CLI (Chinese help; see `--help`)
- `run_interactive_mode()`: interactive dialogue
- `run_single_question()`: one-shot Q&A
- Offline demo (`--provider offline-demo`) and JSON output (`--output`)
- Session management

#### `quickstart.py` — guided demo

- `demo_search()`: demo search
- `interactive_mode()`: simplified interactive mode
- Colored output and user guidance
- API key checks

#### `examples.py` — advanced demos

- `AdvancedWebSearchAgent`: extended agent
- `batch_search()`: batch questions
- `search_with_context()`: context-aware search
- `comparative_search()`: multi-item comparison
- `fact_check()`: fact verification
- `example_research_assistant()`: deep research example

### Configuration Options

| Item | Description | Default |
|------|-------------|---------|
| `MOONSHOT_API_KEY` | Moonshot AI API key | required |
| `KIMI_API_KEY` | Legacy key env name (compat) | optional |
| `KIMI_BASE_URL` | API base URL | `https://api.moonshot.cn/v1` |
| `DEFAULT_MODEL` | Default model | `kimi-k3` |
| `MAX_SEARCH_ITERATIONS` | Max search iterations (in Config) | 5 |
| `SEARCH_TIMEOUT` | Search timeout (seconds) | 30 |
| `temperature` | Generation creativity | 0.6 |

### Technical Notes

#### Core stack

- **Kimi API**: Moonshot Kimi K3 (`kimi-k3`), a reasoning model with native web search
- **Built-in tool calling**: Kimi `$web_search` built-in function
- **Iterative search**: up to 5 rounds until information is sufficient
- **Context management**: full dialogue history for multi-turn chat
- **Temperature control**: adjustable creativity

#### Strengths

- **Live information**: up-to-date web results
- **Intent understanding**: search aligned with the question
- **Structured answers**: well-organized responses
- **Extensible**: easy to add tools via `search_impl` and related hooks

### Development ideas (not implemented)

- [ ] Async search (e.g. aiohttp)
- [ ] Result caching
- [ ] More search backends via `search_impl`
- [ ] Multilingual search
- [ ] Result quality scoring
- [ ] Search history
- [ ] Retries (e.g. tenacity)
- [ ] Better long-dialogue context management

### Caveats

1. **API limits**: respect Kimi quotas and rate limits
2. **Search quality**: depends on Kimi’s search capability
3. **Latency**: web search can take time
4. **Accuracy**: double-check critical facts; the agent may still err

### Usage tips

1. **Ask clearly**: specific questions get better answers
2. **Give context**: background helps when needed
3. **Iterate**: refine with more detail if the first answer is weak
4. **Set expectations**: answers are grounded in search results and may not cover everything

### Links

- [Kimi API docs](https://platform.moonshot.ai/docs)
- [Web search tool docs](https://platform.moonshot.ai/docs/guide/use-web-search)
- [Moonshot AI platform](https://platform.moonshot.ai/)

---

## 中文

### 概述

本项目实现了一个自主式 AI Agent，利用 Kimi（Moonshot AI）的内置 Web 搜索工具（search / crawl 能力），能够：

- **智能理解**：分析用户问题，识别关键信息需求
- **自动搜索**：使用 Kimi 内置 `$web_search` 工具获取实时网络信息
- **迭代搜索**：可多次调用搜索以获取更全面的信息
- **智能总结**：综合多源信息，生成准确、全面的答案

对应书中**实验 1-2 ★：Kimi K3 原生 Agent 能力**，体现“模型即 Agent”与 ReAct（想 → 做 → 看）循环。

### Kimi 联网搜索服务状态

本示例依赖 Kimi 托管的 `$web_search` 服务。本仓库只会将内置工具返回的参数原样传回
Kimi，并不会在本地执行搜索引擎。

Kimi 的[联网搜索官方文档](https://platform.kimi.ai/docs/guide/use-web-search)
目前注明：该服务正在更新，近期不建议使用，并请开发者关注后续文档更新。排查本示例前，
请先查看该页面确认最新服务状态。

如果工具观察结果只有 `search_id`，例如
`{"search_result": {"search_id": "..."}}`，却没有实际搜索内容：

1. 查看 Kimi 联网搜索文档，确认当前服务状态。
2. 稍后重试；如果只需查看 ReAct 流程，可运行
   `python main.py --provider offline-demo`，避免调用托管服务。
3. 优先考虑外部工具/API 的可用性问题；仅凭这一响应，不能说明 Agent 循环或本地实现有误。

### 架构设计

```mermaid
graph TD
    A[用户问题] --> B{Agent 思考}
    B -->|需要搜索| C[调用 $web_search 工具]
    C --> D[Kimi 搜索引擎]
    D --> E[返回搜索结果]
    E --> F{信息充足?}
    F -->|否| G[继续调用 $web_search]
    G --> H[获取更多信息]
    H --> F
    F -->|是| I[生成最终答案]
    B -->|不需要搜索| J[直接回答]
```

### 快速开始

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置 API Key

从 [Moonshot AI 平台](https://platform.moonshot.ai/) 获取 API Key，然后设置环境变量：

```bash
export MOONSHOT_API_KEY='your-api-key-here'
```

或创建 `.env` 文件：

```env
MOONSHOT_API_KEY=your-api-key-here
```

**注意**: 为了向后兼容，系统也支持使用 `KIMI_API_KEY` 环境变量。

**通用兜底（OpenRouter）**: 若未设置 `MOONSHOT_API_KEY`/`KIMI_API_KEY` 但设置了 `OPENROUTER_API_KEY`，请求会自动改走 OpenRouter，使用 `OPENROUTER_MODEL`（默认 `openai/gpt-5.6-luna`）。**重要限制**：Kimi 内置的 `$web_search` 工具是 Moonshot 专有能力，在 OpenRouter 上不可用——因此兜底模式下模型仅凭自身知识作答，**没有实时联网搜索**。如需真正的联网搜索，请使用 Moonshot 主 key。

#### 3. 运行 Agent

`main.py` 提供了完整的命令行接口（中文帮助）。查看全部参数：

```bash
python main.py --help
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 要提问的问题（位置参数）；省略则进入交互模式 | 无 |
| `--provider` | 搜索后端：`kimi`（调用内置 `$web_search`，需 API Key）/ `offline-demo`（离线示例轨迹） | `kimi` |
| `--model` | 模型名称 | `kimi-k3` |
| `--max-steps` | 最大 ReAct 迭代次数 | `5` |
| `--base-url` | API 基础 URL | `https://api.moonshot.cn/v1` |
| `--api-key` | Kimi API Key（默认读环境变量） | 环境变量 |
| `--output`, `-o` | 将问题、ReAct 轨迹与答案保存为 JSON | 无 |
| `--quiet` | 不实时打印 ReAct 轨迹 | 打印 |

**离线演示 ReAct 循环**（无需 API Key，回放示例轨迹，直观展示“想→做→看”）：

```bash
python main.py --provider offline-demo
```

**交互模式**（持续对话）：

```bash
python main.py
```

**单次问答**（运行时逐步打印思考/行动/观察轨迹）：

```bash
python main.py "2024年诺贝尔物理学奖获得者是谁？"
python main.py "比特币现价" --max-steps 3 --output result.json
```

**快速体验**（引导式交互）：

```bash
python quickstart.py
```

**高级示例**：

```bash
python examples.py
```

> 运行时会实时打印 **ReAct 轨迹**：💭 思考 → 🔧 行动（调用 `$web_search`）→ 👀 观察（搜索结果）→ ✅ 最终答案，对应本章讲的“想→做→看”循环。`agent.get_trace()` 可获取结构化轨迹，`--output` 可将其存为 JSON。

### 使用示例

#### 基础使用

```python
from agent import WebSearchAgent
from config import Config

# 创建 Agent
agent = WebSearchAgent(api_key=Config.get_api_key())

# 提问并获取答案
question = "Python 3.12 有哪些新特性？"
answer = agent.search_and_answer(question)
print(answer)
```

#### 高级功能

```bash
python examples.py
```

包含：

- **批量搜索**：同时搜索多个问题
- **带上下文搜索**：提供背景信息进行更精准的搜索
- **比较搜索**：搜索并比较多个项目
- **事实核查**：验证陈述的真实性
- **研究助手**：深度研究某个主题

### 核心组件

#### `agent.py` — 核心 Agent 实现

- `WebSearchAgent`: 主要的 Agent 类
- `search_and_answer()`: 执行 ReAct 循环并生成答案的主方法
- `get_trace()`: 返回上一次运行的结构化 ReAct 轨迹（思考/行动/观察/最终答案）
- `_chat()`: 与 Kimi API 进行对话交互
- `_get_system_prompt()`: 获取系统提示，定义 Agent 行为
- `_get_tools()`: 定义可用的工具（`$web_search`）
- `search_impl()`: 搜索实现的抽象层，便于扩展
- `format_trace_step()`: 将一条轨迹步骤渲染为可读文本
- `run_offline_demo()`: 离线回放示例轨迹，无需 API Key 即可演示 ReAct 循环

#### `config.py` — 配置管理

- API 配置
- 模型选择
- 搜索参数设置

#### `main.py` — 主程序入口

- `build_parser()`: argparse 命令行接口（中文帮助，见 `--help`）
- `run_interactive_mode()`: 交互式对话模式
- `run_single_question()`: 单次问答模式
- 离线演示模式（`--provider offline-demo`）与 JSON 结果输出（`--output`）
- 会话管理

#### `quickstart.py` — 快速体验脚本

- `demo_search()`: 演示搜索功能
- `interactive_mode()`: 简化的交互模式
- 彩色输出和用户引导
- API Key 配置检查

#### `examples.py` — 高级示例

- `AdvancedWebSearchAgent`: 扩展功能的 Agent 类
- `batch_search()`: 批量处理多个问题
- `search_with_context()`: 带上下文的搜索
- `comparative_search()`: 比较多个项目
- `fact_check()`: 事实验证功能
- `example_research_assistant()`: 深度研究示例

### 配置选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MOONSHOT_API_KEY` | Moonshot AI API 密钥 | 必填 |
| `KIMI_API_KEY` | 旧版 API 密钥变量名（向后兼容） | 可选 |
| `KIMI_BASE_URL` | API 基础 URL | `https://api.moonshot.cn/v1` |
| `DEFAULT_MODEL` | 默认模型 | `kimi-k3` |
| `MAX_SEARCH_ITERATIONS` | 最大搜索迭代次数（Config 中设置） | 5 |
| `SEARCH_TIMEOUT` | 搜索超时时间（秒） | 30 |
| `temperature` | 控制生成内容的创造性 | 0.6 |

### 技术特点

#### 核心技术

- **Kimi API**: 使用 Moonshot AI 的最新 Kimi K3 模型（`kimi-k3`，原生联网搜索的推理模型）
- **内置工具调用**: 利用 Kimi 的 `$web_search` 内置函数
- **迭代式搜索**: 支持多轮搜索直到获得充分信息（最多 5 次迭代）
- **上下文管理**: 维护完整对话历史，支持连续对话
- **温度控制**: 支持调整生成内容的创造性（temperature 参数）

#### 优势

- **实时信息**: 获取最新的网络信息
- **智能理解**: 理解用户意图，精准搜索
- **结构化输出**: 生成组织良好的答案
- **可扩展性**: 易于添加新功能和工具

### 开发计划（尚未实现）

- [ ] 添加异步搜索支持（使用 aiohttp）
- [ ] 实现搜索结果缓存机制
- [ ] 支持更多搜索后端（通过 `search_impl` 扩展）
- [ ] 支持多语言搜索
- [ ] 添加搜索结果质量评分
- [ ] 实现搜索历史记录
- [ ] 集成重试机制（使用 tenacity）
- [ ] 优化长对话的上下文管理

### 注意事项

1. **API 限制**: 请注意 Kimi API 的调用限制和配额
2. **搜索质量**: 搜索结果质量依赖于 Kimi 的搜索能力
3. **响应时间**: 网络搜索可能需要一定时间，请耐心等待
4. **内容准确性**: Agent 会尽力提供准确信息，但建议对重要信息进行二次验证

### 使用建议

1. **明确问题**: 提供清晰、具体的问题以获得更好的答案
2. **提供上下文**: 必要时提供背景信息帮助 Agent 理解
3. **迭代优化**: 如果答案不满意，可以提供更多细节重新提问
4. **合理期望**: Agent 基于搜索结果回答，可能无法回答所有问题

### 相关链接

- [Kimi API 文档](https://platform.moonshot.ai/docs)
- [Web 搜索工具文档](https://platform.moonshot.ai/docs/guide/use-web-search)
- [Moonshot AI 平台](https://platform.moonshot.ai/)

---

## Notes / 说明

- License: MIT.  
  许可证：MIT。  
- Author / 作者: AI Agent 实战训练营；version / 版本: 1.0.0.  
- Prefer `--provider offline-demo` first if you only want to see the ReAct shape without spending API quota.  
  若只想先看 ReAct 形态、不消耗配额，优先运行 `--provider offline-demo`。  
- Live search requires a Moonshot key; OpenRouter fallback has no `$web_search`.  
  真正联网搜索必须使用 Moonshot Key；OpenRouter 兜底没有 `$web_search`。  
