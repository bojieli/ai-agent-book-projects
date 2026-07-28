# Context Compression Strategies / 上下文压缩策略对比

> Companion material for *AI Agents in Depth*, Chapter 2 — **Experiment 2-9 ★★★: Comparison of context compression strategies**.  
> 配套《深入理解 AI Agent》第 2 章 **实验 2-9 ★★★：上下文压缩策略对比**。

← [Chapter 2 index / 返回第 2 章目录](../README.md)

---

## English

### Overview

Demonstrates and compares context compression strategies for LLM agents, using research on OpenAI co-founders’ current affiliations as the test task.

As context windows grow (128K+), efficient context management matters for:

- **Cost** — fewer tokens  
- **Performance** — lower latency  
- **Reliability** — fewer overflow errors  
- **Relevance** — keep what matters  

This lab implements and compares **6** strategies and their trade-offs.

### Compression strategies

#### 1. No compression
- Full webpage content into context  
- Expected: fails after a few tool calls (overflow)  
- Purpose: baseline problem  

#### 2. Non-context-aware: individual summaries
- Summarize each page with LLM, then concatenate  
- Preserves page-specific detail; may lose cross-page links  
- Multiple LLM calls; good when sources are independent  

#### 3. Non-context-aware: combined summary
- Concatenate all pages, then one summary  
- Better overall picture; may lose per-page attribution  
- One LLM call; may hit limits with many pages  

#### 4. Context-aware summarization
- Query-focused summary over all search results  
- Better relevance; extra LLM call  

#### 5. Context-aware with citations
- Like #4 plus citations / source links  
- Better for follow-ups; slightly larger  

#### 6. Windowed context
- Full content for latest tool call; compress older history  
- Balance detail vs efficiency  
- Only compresses messages not already marked `[COMPRESSED]`  

### Installation

```bash
cd chapter2/context-compression
pip install -r requirements.txt
cp env.example .env
# Edit .env with your API keys
```

**API keys:**

- `MOONSHOT_API_KEY` — Kimi/Moonshot (required for live runs). Book 实验 2-9 uses Kimi K3 (~1M real window); the demo **caps** the compression/overflow budget at `CONTEXT_WINDOW_SIZE` (default 128K) so overflow/compression is observable. Override model via `MODEL_NAME` or `-m/--model` (e.g. `kimi-k2.5`, `kimi-k3`, `moonshot-v1-128k`).
- `OPENROUTER_API_KEY` — fallback if Moonshot key unset (`kimi-*` → `moonshotai/kimi-k2`). Unchanged if `MOONSHOT_API_KEY` is set.
- `SERPER_API_KEY` — web search (optional; mock data if missing)

Keys: [Moonshot](https://platform.moonshot.cn/), [Serper free tier](https://serper.dev/)

### Scripts overview

| Script | Purpose | Output |
|--------|---------|--------|
| `main.py` | Interactive demo / single strategy | Console |
| `experiment.py` | Automated comparison (token / compression / success table) | `results/` |
| `run_all_strategies.py` | Strategies with detailed per-round logs | `logs/` |
| `quickstart.py` | Menu wrapper (env check + launcher) | Console |

CLIs use Chinese `--help`. Shared useful flags:

- `-s/--strategy` — one or more strategies (default all 6); see list or `--list-strategies`
- `-m/--model` — override `MODEL_NAME`
- `-n/--max-iterations` — max tool-call rounds per strategy

Strategy aliases: `no_compression`, `individual`, `combined`, `context_aware`, `citations`, `windowed`.

### Usage

#### Full experiment (comparison table + JSON)

```bash
python experiment.py                          # all 6 strategies + comparison table
python experiment.py -s context_aware         # one strategy
python experiment.py -s individual combined   # two non-task-aware strategies
python experiment.py -m moonshot-v1-128k -o results/run.json
python experiment.py --list-strategies
```

Runs selected strategies sequentially, researches co-founder affiliations, prints Success / Time / **Tokens** / Compression / Overflows, saves `results/experiment_TIMESTAMP.json` (or `-o`).

Key flags: `-s/--strategy`, `-m/--model`, `-o/--output`, `-n/--max-iterations`, `--streaming`, `--list-strategies`.

#### All strategies with logging

```bash
python run_all_strategies.py
python run_all_strategies.py -s windowed
python run_all_strategies.py --log-dir logs/k2 -m kimi-k2.5
```

- Sequential strategies  
- Compression summaries to log file  
- Streaming by default  
- Logs: `<log-dir>/strategy_run_TIMESTAMP.log`  
- JSON: `<log-dir>/strategy_results_TIMESTAMP.json`  
- End comparison summary  

Flags: `-s/--strategy`, `-m/--model`, `--log-dir`, `-n/--max-iterations`, `--list-strategies`.

#### Interactive demo

```bash
python main.py                    # choose strategy at prompt
python main.py -s citations
python main.py -s windowed --no-streaming
```

Streaming on by default; follow-ups useful for citation strategy.

#### Custom usage

```python
from agent import ResearchAgent
from compression_strategies import CompressionStrategy

agent = ResearchAgent(
    api_key="your_api_key",
    compression_strategy=CompressionStrategy.CONTEXT_AWARE_CITATIONS,
    enable_streaming=True
)

result = agent.execute_research()

if result['success']:
    print(result['final_answer'])
    print(f"Tool calls: {len(result['trajectory'].tool_calls)}")
```

### Project structure

```
context-compression/
├── config.py
├── web_tools.py
├── compression_strategies.py
├── agent.py
├── experiment.py
├── run_all_strategies.py
├── main.py
├── quickstart.py
├── requirements.txt
├── env.example
├── logs/                    # from run_all_strategies.py
└── results/                 # experiment JSON
```

### Key components

- **web_tools.py:** `search_web` (Serper + crawl), `fetch_webpage`, mock data without key  
- **compression_strategies.py:** `ContextCompressor`, `CompressedContent`, dynamic compression  
- **agent.py:** streaming, tools, history, windowed compression  
- **experiment.py:** automated runs, metrics, comparison table, JSON  

### Metrics

Success rate, execution time, compression ratio (compressed/original size), context overflows, tool calls, final answer length.

### Expected results (qualitative)

1. No compression → overflow fail  
2. Non-context-aware → may complete, miss detail  
3. Context-aware → good size/relevance balance  
4. With citations → best for follow-ups  
5. Windowed → efficient for long multi-turn  

### Measured results (real run)

Real end-to-end run (no mock): live Serper + Moonshot reasoning model.

- **Model:** `kimi-k3` (real window ~1M; demo budget `CONTEXT_WINDOW_SIZE = 128000`)  
- **Search:** real Serper + page crawl  
- **Task:** track current affiliations of ~11 OpenAI co-founders  
- **Date:** 2026-07-18 · `MAX_ITERATIONS=15` · raw: `results/kimi_k3_real_20260718.json`  

| # | Strategy | Success | Iterations | Tokens | Compress | Overflows | Time |
|---|----------|---------|-----------|--------|----------|-----------|------|
| 1 | `no_compression` | ❌ (overflow at 165,227 tok > 128K) | 5 | 166,043 | 102.1% | 1 | 107s |
| 2 | `non_context_aware_individual_summary` | ✅ | 12 | 276,608 | 10.9% | 4 | 2980s |
| 3 | `non_context_aware_combined_summary` | ✅ | 10 | 93,449 | 4.3% | 0 | 1189s |
| 4 | `context_aware_summary` | ✅ | 7 | 40,157 | 3.0% | 0 | 967s |
| 5 | `context_aware_with_citations` | ✅ | 10 | 222,992 | 4.1% | 3 | 1235s |
| 6 | `windowed_context` | ✅ | 7 | 174,601 | 102.4% | 4 | 867s |

Notes:

- **No compression** fails as designed past 128K (~5th iteration).  
- **Context-aware summary (#4)** most token-efficient success (40,157 tokens, 3.0% char compression).  
- **Individual summaries (#2)** slowest (~50 min): per-page summaries on a reasoning model.  
- **Windowed (#6)** compresses only when usage crosses ~80% of budget; keeps recent full content → char “compression ratio” ~100% while still finishing fastest among compressing strategies.  
- Single-run numbers vary; relative ordering is the takeaway.

### Configuration

`.env` or `config.py`:

- `MODEL_NAME` (default kimi-k3)  
- `MODEL_TEMPERATURE` (default 0.3)  
- `MAX_ITERATIONS` (default 50)  
- `MAX_WEBPAGE_LENGTH` (default 50000)  
- `SUMMARY_MAX_TOKENS` (default 500)  
- `CONTEXT_WINDOW_SIZE` (default 128000; intentional cap vs K3’s real ~1M window)  

### Troubleshooting

- **No Serper key:** mock data still exercises compression logic  
- **Overflow on non-baseline strategies:** lower `MAX_WEBPAGE_LENGTH` / `SUMMARY_MAX_TOKENS` / search `num_results`  
- **Slow:** `--no-streaming`, lower `-n/--max-iterations`, mock search  

### Research task

> “Find the current affiliations of all OpenAI co-founders”

Good because it needs many searches, accumulates text, stresses context management, and has checkable outcomes.

### Extending

New strategy: enum → `ContextCompressor` → `compress_search_results()` → experiment runner.  
New task: system prompt in `agent.py`, mock data in `web_tools.py`, tool descriptions as needed.

---

## 中文

### 概述

演示并对比 LLM Agent 的多种上下文压缩策略，测试任务为调研 OpenAI 联合创始人当前职业归属。

上下文窗口越来越大（128K+）时，高效管理上下文关乎：

- **成本** — 减少 token  
- **性能** — 更低延迟  
- **可靠性** — 减少溢出错误  
- **相关性** — 保留关键信息  

本实验实现并对比 **6** 种策略及其取舍。

### 压缩策略

#### 1. 无压缩
- 网页原文直接进入上下文  
- 预期：几次工具调用后溢出失败  
- 目的：展示基线问题  

#### 2. 非任务感知：逐页摘要
- 每页单独 LLM 摘要再拼接  
- 保留页内细节，可能丢跨页关系  
- 多次 LLM 调用；适合来源彼此独立  

#### 3. 非任务感知：合并摘要
- 先拼接全部网页再做一次总摘要  
- 更利把握全局，可能丢页级归属  
- 单次 LLM 调用；页多时可能撞限  

#### 4. 上下文感知摘要
- 结合查询对全部搜索结果做聚焦摘要  
- 相关性更好；多一次 LLM 调用  

#### 5. 带引用的上下文感知摘要
- 在 #4 基础上加引用与来源链接  
- 利于追问；上下文略大  

#### 6. 窗口化上下文
- 最近一次工具调用保留全文，更早历史压缩  
- 细节与效率折中  
- 只压缩尚未标记 `[COMPRESSED]` 的消息  

### 安装

```bash
cd chapter2/context-compression
pip install -r requirements.txt
cp env.example .env
# 编辑 .env 填入 API Key
```

**所需 Key：**

- `MOONSHOT_API_KEY`：Kimi/Moonshot（在线跑必需）。书中实验 2-9 使用 Kimi K3（真实窗口约 1M）；演示通过 `CONTEXT_WINDOW_SIZE`（默认 128K）**故意收紧**溢出/压缩预算以便观察。可用 `MODEL_NAME` 或 `-m/--model` 覆盖（如 `kimi-k2.5`、`kimi-k3`、`moonshot-v1-128k`）。
- `OPENROUTER_API_KEY`：未设置 Moonshot key 时的通用回退（`kimi-*` → `moonshotai/kimi-k2`）。设了 `MOONSHOT_API_KEY` 时行为不变。
- `SERPER_API_KEY`：联网搜索（可选；缺失则用 mock 数据）

获取：[Moonshot](https://platform.moonshot.cn/)、[Serper 免费档](https://serper.dev/)

### 脚本一览

| 脚本 | 作用 | 输出 |
|------|------|------|
| `main.py` | 交互演示 / 单策略 | 控制台 |
| `experiment.py` | 自动对比（token / 压缩 / 成功表） | `results/` |
| `run_all_strategies.py` | 带逐轮详细日志 | `logs/` |
| `quickstart.py` | 菜单封装（检查环境并启动） | 控制台 |

均提供中文 `--help`。共用常用参数：

- `-s/--strategy` — 一种或多种策略（默认全部 6 种）；见列表或 `--list-strategies`
- `-m/--model` — 覆盖 `MODEL_NAME`
- `-n/--max-iterations` — 每策略最大工具调用轮数

策略别名：`no_compression`、`individual`、`combined`、`context_aware`、`citations`、`windowed`。

### 用法

#### 完整实验（对比表 + JSON）

```bash
python experiment.py                          # 运行全部 6 种策略并生成对比表
python experiment.py -s context_aware         # 只运行「上下文感知压缩」
python experiment.py -s individual combined   # 只对比两种非任务感知策略
python experiment.py -m moonshot-v1-128k -o results/run.json
python experiment.py --list-strategies
```

依次测试所选策略、调研联合创始人归属、打印 Success / Time / **Tokens** / Compression / Overflows，保存到 `results/experiment_TIMESTAMP.json`（或 `-o`）。

主要参数：`-s/--strategy`、`-m/--model`、`-o/--output`、`-n/--max-iterations`、`--streaming`、`--list-strategies`。

#### 带日志跑全部策略

```bash
python run_all_strategies.py
python run_all_strategies.py -s windowed
python run_all_strategies.py --log-dir logs/k2 -m kimi-k2.5
```

- 顺序跑所选策略  
- 压缩摘要写入日志  
- 默认流式  
- 日志：`<log-dir>/strategy_run_TIMESTAMP.log`  
- JSON：`<log-dir>/strategy_results_TIMESTAMP.json`  
- 末尾对比摘要  

参数：`-s/--strategy`、`-m/--model`、`--log-dir`、`-n/--max-iterations`、`--list-strategies`。

#### 交互演示

```bash
python main.py                    # 提示选择策略
python main.py -s citations
python main.py -s windowed --no-streaming
```

默认开启流式；引用策略适合追问。

#### 编程调用

```python
from agent import ResearchAgent
from compression_strategies import CompressionStrategy

agent = ResearchAgent(
    api_key="your_api_key",
    compression_strategy=CompressionStrategy.CONTEXT_AWARE_CITATIONS,
    enable_streaming=True
)

result = agent.execute_research()

if result['success']:
    print(result['final_answer'])
    print(f"Tool calls: {len(result['trajectory'].tool_calls)}")
```

### 项目结构

```
context-compression/
├── config.py
├── web_tools.py
├── compression_strategies.py
├── agent.py
├── experiment.py
├── run_all_strategies.py
├── main.py
├── quickstart.py
├── requirements.txt
├── env.example
├── logs/
└── results/
```

### 关键组件

- **web_tools.py：** `search_web`（Serper + 抓取）、`fetch_webpage`、无 Key 时 mock  
- **compression_strategies.py：** `ContextCompressor`、`CompressedContent`、动态压缩  
- **agent.py：** 流式、工具、历史、窗口化压缩  
- **experiment.py：** 自动跑、指标、对比表、JSON  

### 采集指标

成功率、执行时间、压缩比（压缩后/原始）、上下文溢出次数、工具调用次数、最终答案长度。

### 定性预期

1. 无压缩 → 溢出失败  
2. 非任务感知 → 可能完成但丢细节  
3. 上下文感知 → 体积与相关性较均衡  
4. 带引用 → 最利于追问  
5. 窗口化 → 长对话更高效  

### 实测结果（真实运行）

真实端到端（无 mock）：实时 Serper + Moonshot 推理模型。

- **模型：** `kimi-k3`（真实窗口约 1M；演示预算 `CONTEXT_WINDOW_SIZE = 128000`）  
- **搜索：** 真实 Serper + 页面抓取  
- **任务：** 识别并追踪约 11 位 OpenAI 联合创始人的职业状态  
- **日期：** 2026-07-18 · `MAX_ITERATIONS=15` · 原始 JSON：`results/kimi_k3_real_20260718.json`  

| # | Strategy | Success | Iterations | Tokens | Compress | Overflows | Time |
|---|----------|---------|-----------|--------|----------|-----------|------|
| 1 | `no_compression` | ❌ (overflow at 165,227 tok > 128K) | 5 | 166,043 | 102.1% | 1 | 107s |
| 2 | `non_context_aware_individual_summary` | ✅ | 12 | 276,608 | 10.9% | 4 | 2980s |
| 3 | `non_context_aware_combined_summary` | ✅ | 10 | 93,449 | 4.3% | 0 | 1189s |
| 4 | `context_aware_summary` | ✅ | 7 | 40,157 | 3.0% | 0 | 967s |
| 5 | `context_aware_with_citations` | ✅ | 10 | 222,992 | 4.1% | 3 | 1235s |
| 6 | `windowed_context` | ✅ | 7 | 174,601 | 102.4% | 4 | 867s |

说明：

- **无压缩**按设计在超过 128K 时失败（约第 5 轮）。  
- **上下文感知摘要（#4）** token 最省（40,157 tokens，字符压缩 3.0%）。  
- **逐页摘要（#2）**最慢（约 50 分钟）：推理模型对每页单独摘要。  
- **窗口化（#6）**仅在用量跨过约 80% 预算时批量压缩未压缩工具消息；保留近期全文，字符「压缩比」约 100%，但在可完成任务的策略中总时间最短。  
- 单次运行绝对值会波动；相对排序是关键 takeaway。

### 配置

`.env` 或 `config.py`：

- `MODEL_NAME`（默认 kimi-k3）  
- `MODEL_TEMPERATURE`（默认 0.3）  
- `MAX_ITERATIONS`（默认 50）  
- `MAX_WEBPAGE_LENGTH`（默认 50000）  
- `SUMMARY_MAX_TOKENS`（默认 500）  
- `CONTEXT_WINDOW_SIZE`（默认 128000；相对 K3 真实 ~1M 的故意收紧）  

### 故障排除

- **无 Serper Key：** mock 仍可验证压缩逻辑  
- **非基线策略仍溢出：** 降低 `MAX_WEBPAGE_LENGTH` / `SUMMARY_MAX_TOKENS` / 搜索 `num_results`  
- **偏慢：** `--no-streaming`、减小 `-n/--max-iterations`、改用 mock 搜索  

### 研究任务

> 「查找所有 OpenAI 联合创始人的当前职业归属」

适合原因：需多次搜索、内容量大、考验上下文累积管理，结果可核对。

### 扩展

新策略：枚举 → `ContextCompressor` → `compress_search_results()` → 实验 runner。  
新任务：改 `agent.py` 系统提示、`web_tools.py` mock、工具描述。

---

## Notes / 说明

- The 128K budget is intentional so compression/overflow behavior is visible even on models with larger real windows.  
- 128K 预算是故意收紧的，以便在真实窗口更大的模型上仍能观察到压缩与溢出行为。
