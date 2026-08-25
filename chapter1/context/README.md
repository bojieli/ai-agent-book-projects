# Context-Aware AI Agent with Ablation Studies / 上下文感知 Agent 与消融实验

> Multi-provider context-aware agent with systematic ablation of context components (history, reasoning, tool calls, tool results).  
> 配套《深入理解 AI Agent》第 1 章 **实验 1-1 ★★：上下文的关键作用**。

← [Chapter 1 index / 返回第 1 章目录](../README.md) · 📖 [Read the chapter / 读本章正文](../../book/chapter1.md)（[EN](../../book-en/chapter1.md)）

---

## Code map

- **Run first:** python main.py --mode interactive (after provider setup).
- **Start here:** main.py builds the selected provider and agent loop.
- **Core behavior:** agent.py assembles history, reasoning, tool calls and tool results.
- **State / protocol:** AgentTrajectory and the provider adapter messages.
- **Verifier:** the ablation runner and tests under tests/; compare behavior, not just final text.
- **Experiment variable:** context modes (full, no history, no reasoning, no tool calls, no tool results).
- **Skip on first pass:** provider-specific clients, plotting and credential checks.

## English

### Overview

This project implements a context-aware AI agent with multiple tools (PDF parsing, currency conversion, calculator, code interpreter) and provides comprehensive ablation testing to explore how different context components affect agent behavior and performance. It supports multiple LLM providers, including Qwen directly through Alibaba Cloud Model Studio (Bailian), SiliconFlow Qwen, ByteDance Doubao, Moonshot Kimi, and DeepSeek.

### Key Features

- **Multi-provider Support**: Works with Alibaba Cloud Model Studio (Qwen), SiliconFlow (Qwen), Doubao (ByteDance), Kimi (Moonshot), and DeepSeek LLMs
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

#### Alibaba Cloud Model Studio / Bailian (Qwen)

- **Model**: `qwen3.7-plus` (customizable with `--model`)
- **API**: Direct OpenAI-compatible DashScope endpoint; no SiliconFlow account required
- **Provider names**: `dashscope` (canonical), with `qwen` and `bailian` aliases
- **Region note**: API keys are region-bound. Mainland keys use the default endpoint; international keys must set `DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

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

- Python 3.10+
- API key for one of the supported providers:
  - **Alibaba Cloud Model Studio / Bailian**: Get from [Model Studio](https://bailian.console.aliyun.com/)
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
# Recommended from the repository root: use the shared Chapter 1 environment
uv sync --locked --extra ch1

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch1]"

# Enter this experiment directory for the commands below
cd chapter1/context

# Single-project compatibility path, still supported during migration:
# python -m pip install -r requirements.txt

# Copy and configure environment
cp env.example .env
# Edit .env and add one provider key (for example DASHSCOPE_API_KEY or ARK_API_KEY)
```

#### 2. Configure Provider

```bash
# For Doubao (ByteDance) - Default
export ARK_API_KEY=your_key_here  
python main.py  # Uses Doubao by default

# For SiliconFlow (Qwen)
export SILICONFLOW_API_KEY=your_key_here
python main.py --provider siliconflow

# For Qwen directly through Alibaba Cloud Model Studio / Bailian
export DASHSCOPE_API_KEY=your_key_here
python main.py --provider dashscope
# --provider qwen and --provider bailian are equivalent aliases.
# For an international-region key, also set:
export DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1

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
export OPENROUTER_API_KEY=your-openrouter-api-key
python main.py                       # falls back to OpenRouter when ARK_API_KEY is unset
python main.py --provider openrouter # or use OpenRouter directly
```

#### 3. Testing Qwen / Kimi / DeepSeek Integration

```bash
# Run the ablation study directly on Alibaba Cloud Qwen
export DASHSCOPE_API_KEY=your_key_here
python main.py --provider dashscope --mode ablation

# Quick test of Kimi K3 model
export MOONSHOT_API_KEY=your_key_here
python tests/manual/check_kimi.py

# Use Kimi in main script
python main.py --provider kimi --mode interactive

# Run ablation study with Kimi
python main.py --provider kimi --mode ablation

# Quick test of DeepSeek V4
export DEEPSEEK_API_KEY=your_key_here
python tests/manual/check_deepseek.py
# or: python tests/manual/check_deepseek_quick.py

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
# - Type 'sample 2' to test PDF parsing
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

#### Accepted real Kimi K3 execution (2026-08-25)

`run_experiment_1_1.py` executes the exact five arms from the manuscript and
persists every credential-free provider request/response, rather than only a
summary table:

```bash
python run_experiment_1_1.py --provider kimi
```

`--model` is optional and defaults to the provider's entry in the shared
registry (`agentbook/providers`). Selecting one provider while naming another
provider's model is what made all five arms fail in
[#971](https://github.com/bojieli/ai-agent-book/issues/971), so `--provider`
alone is now enough:

```bash
export DASHSCOPE_API_KEY=your_key_here
python run_experiment_1_1.py --provider dashscope     # runs qwen3.7-plus
```

The accepted artifact is [validation/latest.json](validation/latest.json). It
is replaced only by a run that is both canonical — all five arms, guarded task,
silent tool-result withholding — and accepted. Anything else writes its own
timestamped directory and leaves the cited evidence alone.

#### Reading an arm

`completed` means the agent loop returned a terminal response. It does not mean
the task was done. The legacy `success` field is an alias for `completed`, and
`task_success` is the canonical numeric rubric. None of them distinguishes the
two ways an ablated arm ends without the answer, so every arm also carries an
`outcome`:

| `outcome` | What happened |
|---|---|
| `correct` | Terminal answer matching the numeric rubric |
| `no_unsupported_numbers` | Terminal answer claiming no figure the model was not given |
| `unsupported_numbers` | Terminal answer stating revenue-scale figures found in neither the task nor any observation the model received |
| `incorrect` | Terminal answer, wrong, but the model did have observations to work from |
| `no_terminal_response` | Hit the iteration ceiling, or errored |

`unsupported_numbers` is the case the `Completed` column can never show, and it
is the one that matters in production: an answer built on remembered exchange
rates is formatted exactly like an answer built on tool output. It is computed
in [grounding.py](grounding.py) from the messages actually sent, so an arm whose
observations were withheld has nothing to ground on regardless of what the
harness computed locally. Groundedness is deliberately independent of
correctness — a model with no observations that states the right total still did
not read it anywhere. `no_unsupported_numbers` covers both a principled refusal
and a turn that only narrated its plan before stopping; telling those apart is a
judgment about intent the harness does not make.

Observed results (these are not the expected-behavior labels below):

| Arm | Iterations | Tool actions | Repeated action | Outcome |
|---|---:|---:|---|---|
| full | 3 | 4 | no | `correct` |
| no history | 5 (ceiling) | 15 | yes | `no_terminal_response` |
| no reasoning | 3 | 4 | no | `correct` — **no measurable degradation**; the manuscript no longer claims one |
| no tool definitions | 1 | 0 | no | `no_unsupported_numbers` — reported that no conversion tool was reachable |
| no tool results | 5 (ceiling) | 9 | yes | `no_terminal_response` — kept calling and never converged |

The last two arms are not stable across runs; see the table below for what
repeated runs of the no-tool-results arm actually do.

`analysis.manuscript_behavior_claims` holds the canonical booleans, and
`all_manuscript_behavior_claims_observed` is false. A claim about an arm that
never reached the provider is reported as `null` rather than `true`, because two
of the four claims are phrased as absences that a failed request satisfies for
free. `analysis.claim_qualifications` records that the no-tool-definitions claim
is vacuous by construction: a request carrying no tool definitions cannot
produce a tool call, so the only observable quantity is what the model does
instead.

#### Two conditions the arms are sensitive to

Both default to the canonical setting. The alternates exist because they change
the result, and that is worth seeing. Supporting runs are in
[validation/probes_20260825T/](validation/probes_20260825T/), summarised in its
`index.json`.

**`--task guarded|unguarded`** controls one sentence of the prompt: *"Do not
estimate exchange rates yourself; use the tool observations."* Under the guarded
(canonical) task, Kimi K3's no-tool-definitions arm claims no figure it was not
given. Drop that one sentence and the same model, same arm, answers
`$9,587,333.33` — 0.16% from the tool's table, from rates it supplied itself,
with a caveat about assumed rates that a reader skimming the total would miss.

The constraint clearly matters, but it is a probability shift and not a switch:
under the *guarded* task the same model still stated unsupported figures in 2 of
13 arms. And nothing here isolates prompt from model — every provider except
Moonshot was unreachable while these runs were made, so no two models were
compared at a fixed prompt. Models differ substantially in hallucination
tendency, and that is likely the larger factor; the prompt constraint lowers the
odds without removing them. Rely on neither, which is what the groundedness
check exists for.

```bash
python run_experiment_1_1.py --provider kimi --modes no_tool_calls --task unguarded
```

**`--hidden-result empty|marker`** controls how the no-tool-results arm
withholds an observation. `empty` (canonical) sends a tool message with no
content: the API requires the message to exist, so this is as close to "the
result is gone" as the protocol allows. `marker` sends the visible redaction
`[Tool result hidden due to context mode]`, which *adds* a signal the ablation
was meant to remove — the model can see that an observation exists and is being
withheld, and can stop and say so. Across repeated runs of this arm alone (Kimi
K3, guarded task, ceiling of 5):

| Withholding style | Runs | Ran to the ceiling with no answer | Stated unsupported figures | Claimed nothing it was not given |
|---|---:|---:|---:|---:|
| `empty` (canonical) | 7 | 6 | 1 | 0 |
| `marker` | 4 | 1 | 1 | 2 |

The arm is not deterministic under either style, so read these as tendencies at
small n, not as laws. The tendency is clear enough: silent withholding sends the
model to the ceiling 6 times in 7, repeating conversions and then probing the
tool with test values such as 1 EUR→USD and 100 USD→EUR to work out why nothing
was coming back — the manuscript's blind execution. The visible marker sends it
there once in 4, and is the only style under which the model ever reported that
it had been given nothing, which is the point: the redaction is a signal, and
removing a signal is not the same ablation as removing the observation. Both
styles also produce answers from remembered rates, so that failure belongs to
neither design.

```bash
python run_experiment_1_1.py --provider kimi --modes no_tool_results --hidden-result marker
```

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
| **no_tool_calls** | 工具定义 (tool definitions) | No tool action — but a terminal answer either way, either an abstention or one built on remembered rates | Cannot interact with external world; the answer may still look complete |
| **no_tool_results** | 工具执行结果 (tool results) | Repeated and probing tool calls, often to the iteration ceiling | Acts without feedback and cannot tell that it is |

**How each ablation is applied** (see `agent.py`):

- **no_tool_calls** — the `tools` parameter is omitted from the request, so the model has no tool definitions to call.
- **no_tool_results** — every tool result is replaced with empty content, so the message the API requires is still there but carries no observation. `--hidden-result marker` swaps in the visible `[Tool result hidden due to context mode]` placeholder instead, which is a different experiment: it tells the model an observation is being withheld.
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

#### Automated Regression Tests

```bash
python -m pytest tests
```

Manual provider/API smoke scripts live under `tests/manual/` and require the corresponding API keys.

### Understanding Results

#### Performance Metrics

- **Terminal Response Rate**: Whether the agent returned a terminal response
- **Task Success**: Correctness under the task-specific rubric (when one is available)
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
# Creates fixtures/pdfs/ with sample financial reports
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
├── README.md             # This file
├── main.py               # Single CLI entry point (single / ablation / interactive)
├── agent.py              # Core agent implementation + context modes
├── config.py             # Configuration management
├── create_sample_pdf.py  # PDF generation utility
├── fixtures/
│   └── pdfs/             # Sample PDFs used by local demos/tests
├── tests/
│   ├── test_agent.py
│   ├── test_code_interpreter.py
│   ├── test_malformed_tool_json.py
│   └── manual/           # Provider/API smoke scripts; require real keys
├── requirements.txt      # Dependencies
└── env.example           # Environment template
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

本项目实现一个上下文感知 AI Agent，配备多种工具（PDF 解析、货币换算、计算器、代码解释器），并通过系统化的**消融实验**（Ablation Study）检验不同上下文组件对 Agent 行为与性能的影响。支持通过阿里云百炼直连 Qwen，也支持 SiliconFlow Qwen、字节跳动 Doubao、月之暗面 Kimi、DeepSeek。对应书中**实验 1-1 ★★：上下文的关键作用**。

### 主要特性

- **多提供商支持**：阿里云百炼（Qwen 直连）、SiliconFlow（Qwen）、Doubao（字节）、Kimi（月之暗面）、DeepSeek
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

#### 阿里云百炼（Qwen 直连）

- **模型**：`qwen3.7-plus`（可通过 `--model` 自定义）
- **API**：直连 DashScope 的 OpenAI 兼容接口，无需 SiliconFlow 账号
- **提供商名称**：规范名称为 `dashscope`，也可使用别名 `qwen` 或 `bailian`
- **区域说明**：API Key 与区域绑定。中国内地 Key 默认直连内地端点；国际站 Key 必须设置 `DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

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

- Python 3.10+
- 任一支持提供商的 API Key：
  - **阿里云百炼**：[百炼控制台](https://bailian.console.aliyun.com/)
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
# 推荐在仓库根目录使用统一的第 1 章环境
uv sync --locked --extra ch1

# 切换目录前先激活环境：
# macOS/Linux：
source .venv/bin/activate
# Windows PowerShell：.\.venv\Scripts\Activate.ps1
# Windows cmd：.venv\Scripts\activate.bat

# 未安装 uv 时可用 pip 兜底：
# python -m pip install -e ".[ch1]"

# 进入本实验目录，后续命令都在这里运行
cd chapter1/context

# 迁移期间仍支持单项目兼容路径：
# python -m pip install -r requirements.txt

# 复制并配置环境变量
cp env.example .env
# 编辑 .env 并填入一个提供商的 API Key（例如 DASHSCOPE_API_KEY 或 ARK_API_KEY）
```

#### 2. 配置提供商

```bash
# For Doubao (ByteDance) - Default
export ARK_API_KEY=your_key_here  
python main.py  # Uses Doubao by default

# For SiliconFlow (Qwen)
export SILICONFLOW_API_KEY=your_key_here
python main.py --provider siliconflow

# 通过阿里云百炼直连 Qwen
export DASHSCOPE_API_KEY=your_key_here
python main.py --provider dashscope
# --provider qwen 与 --provider bailian 是等价别名。
# 如果使用国际站 Key，还需设置：
export DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1

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
export OPENROUTER_API_KEY=your-openrouter-api-key
python main.py                       # falls back to OpenRouter when ARK_API_KEY is unset
python main.py --provider openrouter # or use OpenRouter directly
```

#### 3. 测试 Qwen / Kimi / DeepSeek 集成

```bash
# 通过阿里云百炼 Qwen 直接运行消融实验
export DASHSCOPE_API_KEY=your_key_here
python main.py --provider dashscope --mode ablation

# Quick test of Kimi K3 model
export MOONSHOT_API_KEY=your_key_here
python tests/manual/check_kimi.py

# Use Kimi in main script
python main.py --provider kimi --mode interactive

# Run ablation study with Kimi
python main.py --provider kimi --mode ablation

# Quick test of DeepSeek V4
export DEEPSEEK_API_KEY=your_key_here
python tests/manual/check_deepseek.py
# or: python tests/manual/check_deepseek_quick.py

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
# - Type 'sample 2' to test PDF parsing
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

#### 已验收的 Kimi K3 真实执行（2026-08-25）

`run_experiment_1_1.py` 会按正文运行五个精确实验组，并保存每轮真实 API 的无凭据
请求与响应，而不只是汇总表：

```bash
python run_experiment_1_1.py --provider kimi
```

`--model` 可省略，缺省取共享注册表（`agentbook/providers`）中该提供商的默认模型。
选定一个提供商却写另一个提供商的模型名，正是
[#971](https://github.com/bojieli/ai-agent-book/issues/971) 中五组全部失败的原因；
现在只传 `--provider` 就够了：

```bash
export DASHSCOPE_API_KEY=your_key_here
python run_experiment_1_1.py --provider dashscope     # 使用 qwen3.7-plus
```

验收产物见 [validation/latest.json](validation/latest.json)。只有既是标准配置
（五组齐全、带约束的任务、静默隐藏工具结果）又通过验收的运行才会覆盖它；其余运行
只写自己的时间戳目录，不会动被引用的证据。

#### 怎么读一组实验

`completed` 表示 Agent 循环返回了终止响应，不代表任务做对了。旧字段 `success` 是
`completed` 的别名，`task_success` 才是数值评分标准。三者都区分不出「消融组没给出
答案」的两种情况，因此每组还带一个 `outcome`：

| `outcome` | 含义 |
|---|---|
| `correct` | 终止回答且符合数值评分标准 |
| `no_unsupported_numbers` | 终止回答中没有声称任何模型未被给予的数字 |
| `unsupported_numbers` | 终止回答中出现了任务与观测里都没有的营收量级数字 |
| `incorrect` | 有观测可依据，但回答仍然错误 |
| `no_terminal_response` | 触到迭代上限，或报错 |

`unsupported_numbers` 正是 `Completed` 那一列永远显示不出来的情况，也是生产中真正
要命的一种：用记忆中的汇率拼出来的答案，排版和用工具结果算出来的答案一模一样。它由
[grounding.py](grounding.py) 依据**实际发出的消息**计算，因此被隐藏了观测的实验组
无论框架本地算出了什么，都无处可依。可依据性与正确性是两条独立的轴——没有观测却报出
正确总数的模型，同样不是「读到」的。`no_unsupported_numbers` 同时涵盖「明确拒绝」和
「只说了一句打算怎么做就停下」；区分这两者属于对意图的判断，本框架不做。

实测结果（下方「预期行为」表是设计预期，不是实测）：

| 实验组 | 迭代 | 工具行动 | 重复行动 | outcome |
|---|---:|---:|---|---|
| full | 3 | 4 | 否 | `correct` |
| no history | 5（触顶） | 15 | 是 | `no_terminal_response` |
| no reasoning | 3 | 4 | 否 | `correct` —— **测不出退化**；正文已不再作此断言 |
| no tool definitions | 1 | 0 | 否 | `no_unsupported_numbers` —— 声明会话中没有可用的换汇工具 |
| no tool results | 5（触顶） | 9 | 是 | `no_terminal_response` —— 一直重调工具，始终没有收敛 |

后两组在多次运行之间并不稳定；「移除工具执行结果」组反复运行的实际表现见下表。

`analysis.manuscript_behavior_claims` 保存正文行为结论的布尔值，
`all_manuscript_behavior_claims_observed` 为 false。对于根本没有到达提供商的实验组，
结论记为 `null` 而不是 `true`——四条结论里有两条是以「没有发生什么」表述的，一次失败
的请求就能白白满足它们。`analysis.claim_qualifications` 则记下：「移除工具定义后没有
工具行动」是构造性必然，请求里没有工具定义，模型本就发不出工具调用；唯一可观察的是
它转而做了什么。

#### 两个会改变结论的开关

两者默认都是标准配置；提供另一个取值，是因为它确实会改变结果，而这值得看见。支撑数据
见 [validation/probes_20260825T/](validation/probes_20260825T/)，汇总在其 `index.json`。

**`--task guarded|unguarded`** 控制提示词里的一句话：*「不要自行估计汇率，请使用工具
观测。」* 在带约束（标准）的任务下，Kimi K3 的「移除工具定义」组不会声称任何未被给予
的数字；去掉这一句，同一个模型、同一组实验就给出了 `$9,587,333.33`——与工具汇率表相差
0.16%，汇率是它自己补上的，附带的「基于所假设汇率」说明，只看总数的读者根本不会注意到。

这条约束确实起作用，但它只是概率上的偏移，不是开关：在**带约束**的任务下，同一个模型
仍有 2/13 组报出了无依据的数字。而且这里无法把提示词和模型分开——这批运行期间除
Moonshot 外的提供商都不可用，没有在固定提示词下比较过两个模型。不同模型的幻觉率差异
很大，那多半才是更主要的因素；提示词约束只能降低概率，不能消除。两者都不能依赖，这正是
可依据性检查存在的意义。

```bash
python run_experiment_1_1.py --provider kimi --modes no_tool_calls --task unguarded
```

**`--hidden-result empty|marker`** 控制「移除工具执行结果」组如何隐藏观测。`empty`
（标准）发送一条内容为空的 tool 消息——协议要求这条消息必须存在，所以这已是「结果消失
了」最接近的实现。`marker` 发送可见的占位符
`[Tool result hidden due to context mode]`，这等于**补上**了一个本该被消融掉的信号：
模型能看出「这里有观测，但被藏了」，于是可以停下来说明情况。对这一组反复运行
（Kimi K3、带约束任务、上限 5 轮）：

| 隐藏方式 | 运行次数 | 触顶且无答案 | 报出无依据数字 | 未声称任何未被给予的数字 |
|---|---:|---:|---:|---:|
| `empty`（标准） | 7 | 6 | 1 | 0 |
| `marker` | 4 | 1 | 1 | 2 |

这一组在两种方式下都不是确定性的，样本量也小，因此上表只是倾向而非定律。倾向本身足够
清楚：静默隐藏下 7 次里有 6 次跑到迭代上限——反复重做换汇，然后用测试值试探工具
（1 EUR→USD、100 USD→EUR）以判断为什么什么都没回来——这正是正文所说的「盲目执行」；
可见占位符下 4 次里只有 1 次如此，而且只有在这种方式下，模型才报告过「我什么都没拿到」。
这正是关键：占位符本身是一个信号，拿走一个信号和拿走观测并不是同一个消融。两种方式也都
出现过用记忆中的汇率作答，所以那一种失败不属于任何一种设计。

```bash
python run_experiment_1_1.py --provider kimi --modes no_tool_results --hidden-result marker
```

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
| **no_tool_calls** | 工具定义 (tool definitions) | 没有工具行动，但两种情况都会给出终止回答：要么拒绝，要么用记忆中的汇率作答 | 无法与外部世界交互；但回答看上去可能仍然完整 |
| **no_tool_results** | 工具执行结果 (tool results) | 反复重调并试探工具，常常一直触到迭代上限 | 在没有反馈的情况下行动，且察觉不到这一点 |

**各消融如何落地**（见 `agent.py`）：

- **no_tool_calls** — 请求中省略 `tools` 参数，模型没有可调用的工具定义。
- **no_tool_results** — 每个工具结果的内容被置空：API 要求这条消息存在，但它不再携带任何观测。`--hidden-result marker` 则换成可见的 `[Tool result hidden due to context mode]` 占位符——那是另一个实验，因为它等于告诉模型「这里有观测被藏起来了」。
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

#### 自动化回归测试

```bash
python -m pytest tests
```

需要真实 API Key 的手动提供商/API 冒烟脚本放在 `tests/manual/`。

### 结果解读

#### 性能指标

- **Terminal Response Rate**：Agent 是否返回了终止响应
- **Task Success**：在存在任务专用评分标准时，任务是否正确完成
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
# Creates fixtures/pdfs/ with sample financial reports
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
├── README.md             # 本文件
├── main.py               # 单一 CLI 入口（single / ablation / interactive）
├── agent.py              # Core agent implementation + context modes
├── config.py             # Configuration management
├── create_sample_pdf.py  # PDF generation utility
├── fixtures/
│   └── pdfs/             # 本地 demo/tests 使用的样例 PDF
├── tests/
│   ├── test_agent.py
│   ├── test_code_interpreter.py
│   ├── test_malformed_tool_json.py
│   └── manual/           # 需真实 Key 的提供商/API 冒烟脚本
├── requirements.txt      # Dependencies
└── env.example           # Environment template
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
