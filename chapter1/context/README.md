# Context-Aware AI Agent with Ablation Studies / 上下文感知 Agent 与消融实验

> Multi-provider context-aware agent with systematic ablation of context components (history, reasoning, tool calls, tool results).  
> 配套《深入理解 AI Agent》第 1 章 **实验 1-1 ★★：上下文的关键作用**。

← [Chapter 1 index / 返回第 1 章目录](../README.md) · 📖 [Read the chapter / 读本章正文](../../book/chapter1.md)（[EN](../../book-en/chapter1.md)）

---

## English

### Overview

This project implements a context-aware AI agent with multiple tools (PDF parsing, currency conversion, calculator, code interpreter) and provides comprehensive ablation testing to explore how different context components affect agent behavior and performance. It supports multiple LLM providers: SiliconFlow Qwen, ByteDance Doubao, Moonshot Kimi, and DeepSeek.

### Key Features

- **Multi-provider Support**: Works with SiliconFlow (Qwen), Doubao (ByteDance), Kimi (Moonshot), and DeepSeek LLMs
- **Multi-tool Agent**: PDF parsing, currency conversion, calculations, and Python code execution
- **Context Modes**: Five different context configurations for ablation studies
- **Interactive & Batch Modes**: Run single tasks or comprehensive test suites
- **Conversation History**: Maintains context across multiple queries in a session
- **Detailed Analytics**: Performance metrics, visualizations, and comprehensive reports

### Supported LLM Providers

#### Doubao (ByteDance) - Default

- **Model**: `doubao-seed-1-6-thinking-250715` (customizable)
- **API**: OpenAI-compatible via Volcano Engine
- **Best for**: Advanced reasoning, faster responses, both English and Chinese tasks

#### SiliconFlow

- **Model**: `Qwen/Qwen3.5-397B-A17B` (customizable)
- **API**: OpenAI-compatible
- **Best for**: Complex reasoning tasks, detailed analysis

#### Kimi (Moonshot AI)

- **Model**: `kimi-k3` (K3 reasoning model; temperature is forced to 1 and max_tokens is large enough for its thinking output)
- **API**: OpenAI-compatible via Moonshot platform
- **Best for**: Advanced reasoning, multi-turn conversations, both English and Chinese tasks
- **Features**: Context caching for cost optimization

#### DeepSeek

- **Model**: `deepseek-v4-flash` (default; use `--model deepseek-v4-pro` for the stronger tier)
- **API**: OpenAI-compatible via [DeepSeek Platform](https://platform.deepseek.com/)
- **Best for**: Cost-effective tool-calling agents; thinking mode enabled so the `no_reasoning` ablation can strip `reasoning_content`
- **Note**: Legacy aliases `deepseek-chat` / `deepseek-reasoner` are deprecated (2026-07-24); prefer the V4 ids

### Architecture

#### Context Components

1. **Full Context** — Complete agent with all components
2. **No History** — Lacks historical tool call tracking
3. **No Reasoning** — Operates without strategic planning
4. **No Tool Calls** — Cannot execute external tools
5. **No Tool Results** — Blind to tool execution outcomes

#### Available Tools

- **`parse_pdf(url)`** — Download and extract text from PDF documents
- **`convert_currency(amount, from, to)`** — Real-time currency conversion
- **`calculate(expression)`** — Simple mathematical expression evaluation
- **`code_interpreter(code)`** — Execute Python code for complex calculations, totals, and data processing

### Prerequisites

- Python 3.8+
- API key for one of the supported providers:
  - **SiliconFlow**: Get from [SiliconFlow](https://siliconflow.cn)
  - **Doubao (ByteDance)**: Get from [Volcano Engine](https://www.volcengine.com/)
  - **Kimi (Moonshot)**: Get from [Moonshot Platform](https://platform.moonshot.cn/)
  - **DeepSeek**: Get from [DeepSeek Platform](https://platform.deepseek.com/api_keys)

### Sample Tasks

The system includes 5 pre-defined sample tasks demonstrating different capabilities:

1. **Simple Currency Conversion** — Basic multi-currency calculations
2. **Multi-Currency Budget Analysis** — Complex expense analysis across offices
3. **PDF Financial Analysis** — Parse and analyze financial documents
4. **Investment Growth Calculation** — Compound interest with currency conversion
5. **Comprehensive Financial Report** — Complete workflow using all tools

These samples are designed to showcase the agent's capabilities and the impact of context ablation.

### Quick Start

#### 1. Installation

```bash
# Clone the repository
cd chapter1/context

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp env.example .env
# Edit .env and add your API key (SILICONFLOW_API_KEY or ARK_API_KEY)
```

#### 2. Configure Provider

```bash
# For Doubao (ByteDance) - Default
export ARK_API_KEY=your_key_here  
python main.py  # Uses Doubao by default

# For SiliconFlow (Qwen)
export SILICONFLOW_API_KEY=your_key_here
python main.py --provider siliconflow

# For Kimi (Moonshot)
export MOONSHOT_API_KEY=your_key_here
python main.py --provider kimi

# For DeepSeek
export DEEPSEEK_API_KEY=your_key_here
python main.py --provider deepseek
# Optional stronger model:
python main.py --provider deepseek --model deepseek-v4-pro

# Or specify a custom model
python main.py --model doubao-seed-1-6-thinking-250715

# Universal OpenRouter fallback: if the provider key above is missing/invalid
# but OPENROUTER_API_KEY is set, requests are routed through OpenRouter and the
# model id is mapped automatically (bare gpt-*/o1-* -> openai/*, claude-* ->
# anthropic/*, deepseek-* -> deepseek/*, other native ids -> OPENROUTER_MODEL
# or openai/gpt-5.6-luna).
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
python main.py                       # falls back to OpenRouter when ARK_API_KEY is unset
python main.py --provider openrouter # or use OpenRouter directly
```

#### 3. Testing Kimi / DeepSeek Integration

```bash
# Quick test of Kimi K3 model
export MOONSHOT_API_KEY=your_key_here
python test_kimi.py

# Use Kimi in main script
python main.py --provider kimi --mode interactive

# Run ablation study with Kimi
python main.py --provider kimi --mode ablation

# Quick test of DeepSeek V4
export DEEPSEEK_API_KEY=your_key_here
python test_deepseek.py
# or: python quick_test_deepseek.py

# Use DeepSeek in main script / ablation study
python main.py --provider deepseek --mode interactive
python main.py --provider deepseek --mode ablation
```

#### 4. Run Interactive Mode (Recommended)

```bash
# Default (Doubao)
python main.py --mode interactive

# With SiliconFlow provider
python main.py --mode interactive --provider siliconflow

# In interactive mode, you can:
# - Type 'samples' to see pre-defined tasks
# - Type 'sample 3' to test PDF parsing
# - Type 'providers' to list available providers
# - Type 'provider kimi' to switch providers
# - Type 'status' to see current configuration
# - Type 'help' for all commands
```

#### 5. Run Sample Tasks

```bash
# Run without arguments to select from samples
python main.py --mode single

# With specific provider
python main.py --mode single --provider doubao

# Or provide your own task
python main.py --mode single \
  --task "Convert $1000 USD to EUR, GBP, and JPY. Calculate the average." \
  --context-mode full \
  --provider siliconflow
```

#### 6. Run Ablation Study

```bash
# With default provider (single case, all five context modes)
python main.py --mode ablation

# With Doubao provider
python main.py --mode ablation --provider doubao

# Multi-case comparison across modes (stronger evidence for the book's point)
python main.py --mode ablation --cases 3

# Compare only two modes and save raw results to a custom path
python main.py --mode ablation --ablation-modes full no_history --output my_ablation.json
```

`main.py` is the single CLI entry point. Run `python main.py --help` for the full (Chinese) flag reference.

Key flags:

| Flag | Description |
|------|-------------|
| `--mode` | `single` / `ablation` / `interactive` (default) |
| `--task` | Task text for `single` mode |
| `--context-mode` | Context mode for `single` mode (`full`, `no_history`, `no_reasoning`, `no_tool_calls`, `no_tool_results`) |
| `--ablation-modes` | Subset of modes to test in `ablation` mode (default: all five) |
| `--cases` | Number of cases each mode is run against in `ablation` mode (default: 1) |
| `--provider` / `--model` | LLM provider and optional model override |
| `--output` | Output path for the JSON result (single) or raw results (ablation) |

### Ablation Studies

The ablation studies systematically remove context components to understand their importance.

#### Test Scenario

A complex financial analysis task requiring:

1. PDF document parsing
2. Multiple currency conversions
3. Mathematical calculations
4. Result aggregation

#### Expected Behaviors

| Context Mode | Removed Component (book §实验 1.1) | Expected Behavior | Impact |
|-------------|-----------------------------------|-------------------|---------|
| **full** | none (baseline) | Complete successful execution | Baseline performance |
| **no_history** | 历史消息 (history) | Redundant operations, inefficiency | May repeat tool calls |
| **no_reasoning** | 思考过程 (reasoning) | Unstructured approach, potential errors | Lacks strategic planning |
| **no_tool_calls** | 工具定义 (tool definitions) | Complete failure | Cannot interact with external world |
| **no_tool_results** | 工具执行结果 (tool results) | Incorrect conclusions | Makes decisions without feedback |

**How each ablation is applied** (see `agent.py`):

- **no_tool_calls** — the `tools` parameter is omitted from the request, so the model has no tool definitions to call.
- **no_tool_results** — every tool result is replaced with a `[Tool result hidden]` placeholder.
- **no_reasoning** — `reasoning_content` is stripped from each assistant message before it is added back to the trajectory.
- **no_history** — `_prepare_messages_for_api()` sends only a sliding window (system prompt + current task + the most recent ReAct step) to the model, so earlier steps are forgotten and the agent tends to repeat tool calls. Full mode always sends the complete trajectory.

#### Running Tests

```bash
# Run the full ablation study (single case, all five modes)
python main.py --mode ablation

# Run across multiple cases for a stronger comparison
python main.py --mode ablation --cases 3

# This will generate:
# - ablation_study_results.png (visualization, if matplotlib is installed)
# - ablation_study_report.md (detailed report)
# - ablation_results.json (raw data; override path with --output)
```

The console prints two tables: a per-run **ablation study results** table and a **comparison matrix** (context mode x case) for reading the effect of each component at a glance.

### Understanding Results

#### Performance Metrics

- **Success Rate**: Whether the task was completed correctly
- **Execution Time**: Total time to complete the task
- **Iterations**: Number of agent-model interactions
- **Tool Calls**: Number of external tool invocations
- **Reasoning Steps**: Strategic planning iterations

#### Sample Output

```
ABLATION STUDY RESULTS
================================================================================
| Test Name                      | Success | Time   | Iterations | Tool Calls |
|--------------------------------|---------|--------|------------|------------|
| Baseline - Full Context        | ✓       | 12.3s  | 5          | 8          |
| No Historical Tool Calls       | ✓       | 18.7s  | 8          | 12         |
| No Reasoning Process           | ✗       | 25.4s  | 10         | 15         |
| No Tool Call Commands          | ✗       | 3.2s   | 2          | 0          |
| No Tool Call Results           | ✗       | 15.6s  | 10         | 10         |
```

### Key Insights

1. **Tool Calls Are Fundamental** — Without tool call capability, the agent cannot interact with external systems, making task completion impossible.
2. **Tool Results Provide Critical Feedback** — Without seeing results, the agent operates blind, leading to incorrect conclusions and infinite loops.
3. **Reasoning Enables Efficiency** — Strategic planning reduces iterations and tool calls, improving both speed and accuracy.
4. **History Prevents Redundancy** — Historical context prevents repeated operations and maintains task coherence across iterations.

### Advanced Usage

#### Interactive Mode Commands

| Command | Description |
|---------|-------------|
| `samples` | Display all available sample tasks |
| `sample <n>` | Run sample task number n |
| `providers` | List all available LLM providers |
| `provider <name>` | Switch to a different provider (e.g., `provider kimi`) |
| `modes` | List available context modes for ablation testing |
| `mode <name>` | Switch context mode (e.g., `mode no_history`) |
| `status` | Show current configuration (provider, model, mode, etc.) |
| `reset` | Reset agent trajectory (clear history) |
| `create_pdfs` | Generate sample PDF files for testing |
| `quit` | Exit interactive mode |

**Note:** The prompt shows the current provider in brackets, e.g., `[KIMI]>` or `[DOUBAO]>`

#### Conversation History

The agent maintains conversation history throughout interactive sessions:

- **Persistent Context**: The agent remembers previous queries and responses within a session
- **Multi-turn Conversations**: You can reference information from earlier in the conversation
- **Tool Call Memory**: Previous tool executions are remembered and can be referenced
- **Reset on Demand**: Use the `reset` command to clear history and start fresh

Example conversation flow:

```
[DOUBAO]> Remember that our budget is $10,000. Calculate 15% of it.
# Agent calculates and remembers the budget

[DOUBAO]> Now convert that 15% amount to EUR
# Agent uses the previously calculated amount without re-asking

[DOUBAO]> What was our original budget?
# Agent recalls the $10,000 mentioned earlier
```

#### Custom Tasks

```python
from agent import ContextAwareAgent, ContextMode

agent = ContextAwareAgent(api_key, ContextMode.FULL)
result = agent.execute_task("""
    Download the PDF from https://example.com/report.pdf,
    extract all monetary values, convert them to EUR,
    and calculate the total.
""")
```

#### Creating Test PDFs

```bash
python create_sample_pdf.py
# Creates test_pdfs/ directory with sample financial reports
```

#### Configuration

Edit `config.py` or set environment variables:

```bash
export MODEL_TEMPERATURE=0.5
export MAX_ITERATIONS=15
export LOG_LEVEL=DEBUG
```

### Project Structure

```
context/
├── agent.py              # Core agent implementation + context modes
├── main.py               # Single CLI entry point (single / ablation / interactive)
├── config.py             # Configuration management
├── create_sample_pdf.py  # PDF generation utility
├── requirements.txt      # Dependencies
├── env.example           # Environment template
└── README.md             # This file
```

> Note: the ablation study lives in `main.py` (`AblationTestSuite`), run via `python main.py --mode ablation`. There is no separate `ablation_tests.py`.

### Research Applications

- **AI Safety Research**: Understanding failure modes
- **System Design**: Identifying critical components
- **Optimization**: Finding minimal viable configurations
- **Education**: Teaching agent architecture principles

### Limitations

- Currency rates are fixed (production should use real-time APIs)
- PDF parsing may fail on complex layouts
- Model token limits may affect very large documents

---

## 中文

### 概述

本项目实现一个上下文感知 AI Agent，配备多种工具（PDF 解析、货币换算、计算器、代码解释器），并通过系统化的**消融实验**（Ablation Study）检验不同上下文组件对 Agent 行为与性能的影响。支持多家 LLM 提供商：SiliconFlow Qwen、字节跳动 Doubao、月之暗面 Kimi、DeepSeek。对应书中**实验 1-1 ★★：上下文的关键作用**。

### 主要特性

- **多提供商支持**：SiliconFlow（Qwen）、Doubao（字节）、Kimi（月之暗面）、DeepSeek
- **多工具 Agent**：PDF 解析、货币换算、计算与 Python 代码执行
- **上下文模式**：五种配置，用于消融对照
- **交互与批处理**：单任务运行或完整测试套件
- **对话历史**：同一会话内跨多轮查询保持上下文
- **详细分析**：性能指标、可视化与综合报告

### 支持的 LLM 提供商

#### Doubao（字节跳动）— 默认

- **模型**：`doubao-seed-1-6-thinking-250715`（可自定义）
- **API**：火山引擎上的 OpenAI 兼容接口
- **适合**：深度推理、较快响应，中英文任务均可

#### SiliconFlow

- **模型**：`Qwen/Qwen3.5-397B-A17B`（可自定义）
- **API**：OpenAI 兼容
- **适合**：复杂推理与细致分析

#### Kimi（月之暗面）

- **模型**：`kimi-k3`（K3 推理模型；temperature 强制为 1，max_tokens 足够容纳思考输出）
- **API**：Moonshot 平台 OpenAI 兼容接口
- **适合**：深度推理、多轮对话，中英文任务均可
- **特性**：上下文缓存以优化成本

#### DeepSeek

- **模型**：`deepseek-v4-flash`（默认；更强档可用 `--model deepseek-v4-pro`）
- **API**：[DeepSeek Platform](https://platform.deepseek.com/) 的 OpenAI 兼容接口
- **适合**：性价比高的工具调用；开启 thinking，便于 `no_reasoning` 消融剥离 `reasoning_content`
- **说明**：旧别名 `deepseek-chat` / `deepseek-reasoner` 已弃用（2026-07-24），请优先使用 V4 id

### 架构

#### 上下文组件

1. **Full Context** — 完整 Agent，保留全部组件
2. **No History** — 缺少历史工具调用追踪
3. **No Reasoning** — 无战略规划/思考过程
4. **No Tool Calls** — 无法执行外部工具
5. **No Tool Results** — 看不到工具执行结果

#### 可用工具

- **`parse_pdf(url)`** — 下载并抽取 PDF 文本
- **`convert_currency(amount, from, to)`** — 货币换算
- **`calculate(expression)`** — 简单数学表达式求值
- **`code_interpreter(code)`** — 执行 Python，用于复杂计算、汇总与数据处理

### 前置条件

- Python 3.8+
- 任一支持提供商的 API Key：
  - **SiliconFlow**：[SiliconFlow](https://siliconflow.cn)
  - **Doubao（字节）**：[火山引擎](https://www.volcengine.com/)
  - **Kimi（月之暗面）**：[Moonshot Platform](https://platform.moonshot.cn/)
  - **DeepSeek**：[DeepSeek Platform](https://platform.deepseek.com/api_keys)

### 示例任务

系统预置 5 个样例任务：

1. **简单货币换算** — 基础多币种计算
2. **多币种预算分析** — 跨办公室费用分析
3. **PDF 财务分析** — 解析并分析财务文档
4. **投资增长计算** — 复利与货币换算
5. **综合财务报告** — 串联全部工具的完整流程

用于展示 Agent 能力与上下文消融的影响。

### 快速开始

#### 1. 安装

```bash
# Clone the repository
cd chapter1/context

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp env.example .env
# Edit .env and add your API key (SILICONFLOW_API_KEY or ARK_API_KEY)
```

#### 2. 配置提供商

```bash
# For Doubao (ByteDance) - Default
export ARK_API_KEY=your_key_here  
python main.py  # Uses Doubao by default

# For SiliconFlow (Qwen)
export SILICONFLOW_API_KEY=your_key_here
python main.py --provider siliconflow

# For Kimi (Moonshot)
export MOONSHOT_API_KEY=your_key_here
python main.py --provider kimi

# For DeepSeek
export DEEPSEEK_API_KEY=your_key_here
python main.py --provider deepseek
# Optional stronger model:
python main.py --provider deepseek --model deepseek-v4-pro

# Or specify a custom model
python main.py --model doubao-seed-1-6-thinking-250715

# Universal OpenRouter fallback: if the provider key above is missing/invalid
# but OPENROUTER_API_KEY is set, requests are routed through OpenRouter and the
# model id is mapped automatically (bare gpt-*/o1-* -> openai/*, claude-* ->
# anthropic/*, deepseek-* -> deepseek/*, other native ids -> OPENROUTER_MODEL
# or openai/gpt-5.6-luna).
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
python main.py                       # falls back to OpenRouter when ARK_API_KEY is unset
python main.py --provider openrouter # or use OpenRouter directly
```

#### 3. 测试 Kimi / DeepSeek 集成

```bash
# Quick test of Kimi K3 model
export MOONSHOT_API_KEY=your_key_here
python test_kimi.py

# Use Kimi in main script
python main.py --provider kimi --mode interactive

# Run ablation study with Kimi
python main.py --provider kimi --mode ablation

# Quick test of DeepSeek V4
export DEEPSEEK_API_KEY=your_key_here
python test_deepseek.py
# or: python quick_test_deepseek.py

# Use DeepSeek in main script / ablation study
python main.py --provider deepseek --mode interactive
python main.py --provider deepseek --mode ablation
```

#### 4. 交互模式（推荐）

```bash
# Default (Doubao)
python main.py --mode interactive

# With SiliconFlow provider
python main.py --mode interactive --provider siliconflow

# In interactive mode, you can:
# - Type 'samples' to see pre-defined tasks
# - Type 'sample 3' to test PDF parsing
# - Type 'providers' to list available providers
# - Type 'provider kimi' to switch providers
# - Type 'status' to see current configuration
# - Type 'help' for all commands
```

#### 5. 运行样例任务

```bash
# Run without arguments to select from samples
python main.py --mode single

# With specific provider
python main.py --mode single --provider doubao

# Or provide your own task
python main.py --mode single \
  --task "Convert $1000 USD to EUR, GBP, and JPY. Calculate the average." \
  --context-mode full \
  --provider siliconflow
```

#### 6. 运行消融实验

```bash
# With default provider (single case, all five context modes)
python main.py --mode ablation

# With Doubao provider
python main.py --mode ablation --provider doubao

# Multi-case comparison across modes (stronger evidence for the book's point)
python main.py --mode ablation --cases 3

# Compare only two modes and save raw results to a custom path
python main.py --mode ablation --ablation-modes full no_history --output my_ablation.json
```

`main.py` 是唯一 CLI 入口。运行 `python main.py --help` 查看完整（中文）参数说明。

关键参数：

| 参数 | 说明 |
|------|------|
| `--mode` | `single` / `ablation` / `interactive`（默认） |
| `--task` | `single` 模式的任务文本 |
| `--context-mode` | `single` 模式的上下文模式（`full`、`no_history`、`no_reasoning`、`no_tool_calls`、`no_tool_results`） |
| `--ablation-modes` | `ablation` 模式下要测的模式子集（默认全部五种） |
| `--cases` | `ablation` 模式下每种模式跑的用例数（默认 1） |
| `--provider` / `--model` | LLM 提供商与可选模型覆盖 |
| `--output` | 单次结果或消融原始结果的 JSON 输出路径 |

### 消融实验

系统性地移除上下文组件，以理解其重要性。

#### 测试场景

需要以下能力的复杂财务分析任务：

1. PDF 文档解析  
2. 多次货币换算  
3. 数学计算  
4. 结果汇总  

#### 预期行为

| 上下文模式 | 移除组件（书中 §实验 1.1） | 预期行为 | 影响 |
|-------------|---------------------------|----------|------|
| **full** | 无（基线） | 完整成功执行 | 基线性能 |
| **no_history** | 历史消息 (history) | 冗余操作、效率下降 | 可能重复调用工具 |
| **no_reasoning** | 思考过程 (reasoning) | 方法无结构、易出错 | 缺少战略规划 |
| **no_tool_calls** | 工具定义 (tool definitions) | 完全失败 | 无法与外部世界交互 |
| **no_tool_results** | 工具执行结果 (tool results) | 错误结论 | 无反馈下做决策 |

**各消融如何落地**（见 `agent.py`）：

- **no_tool_calls** — 请求中省略 `tools` 参数，模型没有可调用的工具定义。
- **no_tool_results** — 每个工具结果替换为 `[Tool result hidden]` 占位符。
- **no_reasoning** — 写回轨迹前，从每条 assistant 消息中剥离 `reasoning_content`。
- **no_history** — `_prepare_messages_for_api()` 只发送滑动窗口（系统提示 + 当前任务 + 最近一步 ReAct），早期步骤被遗忘，易重复调工具。完整模式始终发送完整轨迹。

#### 运行测试

```bash
# Run the full ablation study (single case, all five modes)
python main.py --mode ablation

# Run across multiple cases for a stronger comparison
python main.py --mode ablation --cases 3

# This will generate:
# - ablation_study_results.png (visualization, if matplotlib is installed)
# - ablation_study_report.md (detailed report)
# - ablation_results.json (raw data; override path with --output)
```

控制台会打印两张表：逐次运行的 **ablation study results**，以及 **comparison matrix**（上下文模式 × 用例），便于一眼对比各组件的作用。

### 结果解读

#### 性能指标

- **Success Rate**：任务是否正确完成
- **Execution Time**：完成任务总耗时
- **Iterations**：Agent 与模型交互次数
- **Tool Calls**：外部工具调用次数
- **Reasoning Steps**：战略规划迭代次数

#### 输出示例

```
ABLATION STUDY RESULTS
================================================================================
| Test Name                      | Success | Time   | Iterations | Tool Calls |
|--------------------------------|---------|--------|------------|------------|
| Baseline - Full Context        | ✓       | 12.3s  | 5          | 8          |
| No Historical Tool Calls       | ✓       | 18.7s  | 8          | 12         |
| No Reasoning Process           | ✗       | 25.4s  | 10         | 15         |
| No Tool Call Commands          | ✗       | 3.2s   | 2          | 0          |
| No Tool Call Results           | ✗       | 15.6s  | 10         | 10         |
```

### 关键洞察

1. **工具调用是基础** — 没有工具调用能力，Agent 无法与外部系统交互，任务无法完成。
2. **工具结果提供关键反馈** — 看不到结果等于盲目行动，易导致错误结论与死循环。
3. **推理提升效率** — 战略规划减少迭代与工具调用，兼顾速度与准确。
4. **历史避免冗余** — 历史上下文防止重复操作，并在多轮中保持任务连贯。

### 进阶用法

#### 交互模式命令

| 命令 | 说明 |
|------|------|
| `samples` | 显示全部样例任务 |
| `sample <n>` | 运行第 n 个样例任务 |
| `providers` | 列出可用 LLM 提供商 |
| `provider <name>` | 切换提供商（如 `provider kimi`） |
| `modes` | 列出可用于消融的上下文模式 |
| `mode <name>` | 切换上下文模式（如 `mode no_history`） |
| `status` | 显示当前配置（提供商、模型、模式等） |
| `reset` | 重置 Agent 轨迹（清空历史） |
| `create_pdfs` | 生成测试用样例 PDF |
| `quit` | 退出交互模式 |

**说明：** 提示符会以括号显示当前提供商，如 `[KIMI]>` 或 `[DOUBAO]>`

#### 对话历史

交互会话中 Agent 会维护对话历史：

- **持久上下文**：会话内记住先前查询与回复
- **多轮对话**：可引用更早提到的信息
- **工具调用记忆**：先前工具执行结果可被引用
- **按需重置**：使用 `reset` 清空历史重新开始

示例对话流程：

```
[DOUBAO]> Remember that our budget is $10,000. Calculate 15% of it.
# Agent calculates and remembers the budget

[DOUBAO]> Now convert that 15% amount to EUR
# Agent uses the previously calculated amount without re-asking

[DOUBAO]> What was our original budget?
# Agent recalls the $10,000 mentioned earlier
```

#### 自定义任务

```python
from agent import ContextAwareAgent, ContextMode

agent = ContextAwareAgent(api_key, ContextMode.FULL)
result = agent.execute_task("""
    Download the PDF from https://example.com/report.pdf,
    extract all monetary values, convert them to EUR,
    and calculate the total.
""")
```

#### 生成测试 PDF

```bash
python create_sample_pdf.py
# Creates test_pdfs/ directory with sample financial reports
```

#### 配置

编辑 `config.py` 或设置环境变量：

```bash
export MODEL_TEMPERATURE=0.5
export MAX_ITERATIONS=15
export LOG_LEVEL=DEBUG
```

### 项目结构

```
context/
├── agent.py              # Core agent implementation + context modes
├── main.py               # Single CLI entry point (single / ablation / interactive)
├── config.py             # Configuration management
├── create_sample_pdf.py  # PDF generation utility
├── requirements.txt      # Dependencies
├── env.example           # Environment template
└── README.md             # This file
```

> 说明：消融实验逻辑在 `main.py` 的 `AblationTestSuite` 中，通过 `python main.py --mode ablation` 运行，没有单独的 `ablation_tests.py`。

### 研究用途

- **AI 安全研究**：理解失败模式  
- **系统设计**：识别关键组件  
- **优化**：寻找最小可用配置  
- **教学**：讲解 Agent 架构原理  

### 局限

- 货币汇率为固定值（生产环境应使用实时 API）  
- 复杂版式 PDF 解析可能失败  
- 模型 token 上限可能影响超大文档  

---

## Notes / 说明

- Educational project for context ablation; for production, add proper error handling, rate limiting, and security.  
  本项目为教学向消融实验；生产使用请补齐错误处理、限流与安全措施。  
- OpenRouter is a universal fallback when the direct provider key is missing.  
  未配置直连提供商 Key 时，可走 `OPENROUTER_API_KEY` 通用兜底。  
- License: MIT. Contributions welcome (extra tools, scenarios, ablation strategies, performance).  
  许可证：MIT。欢迎贡献（更多工具、场景、消融策略、性能优化）。  
