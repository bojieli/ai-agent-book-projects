# Memobase Agent / Memobase Agent（Profile + Event 与手写记忆对照）

> Companion material for *AI Agents in Depth*, Chapter 3 — real Memobase SDK demo **and** a Memobase-inspired hand-rolled memory agent (Experiment 3-2 track).  
> 配套《深入理解 AI Agent》第 3 章——真实 Memobase SDK 演示 **与** Memobase 风格自研记忆 Agent（实验 3-2 对照）。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Two tracks in this folder — don’t confuse them

1. **Real Memobase framework demo** (`profile_demo.py`) — uses the actual open-source Memobase SDK (`pip install memobase`, package `memobase>=0.0.27`) against a **running Memobase server**. Canonical demo of Memobase’s *Profile* (structured user attributes) + *Event Memory* (timeline). See [Memobase Profile + Event Demo](#memobase-profile--event-demo-real-sdk).  
2. **Hand-rolled memory agent** (`agent.py` / `main.py`) — self-contained *Memobase-inspired* `MemoryStore` (episodic / semantic / procedural / working, pickle-persisted) calling Kimi directly. **No Memobase server**—only `KIMI_API_KEY`. The `--mode` commands (interactive / benchmark / demo / task) drive this agent.

### Features (hand-rolled agent)

**Memory types:** episodic (task experiences), semantic (facts), procedural (patterns), working (short-term context).

**Operations:** compression when over threshold; consolidation; importance-based decay; clustering; relevance/recency retrieval.

**Model:** Kimi K3 integration (tool use, multi-step reasoning, long context).

**LOCOMO-style categories:** multi-turn reasoning, long-context Q&A, task planning, knowledge integration, tool usage.

### Installation

```bash
cd chapter3/memobase
pip install -r requirements.txt
cp env.example .env
# Add Kimi API key (hand-rolled agent)
```

Edit `config.py` for model, memory thresholds, benchmark, logging.

### Usage (hand-rolled agent)

#### Interactive

```bash
python main.py --mode interactive
```

Commands: `/help`, `/memory`, `/clear`, `/reset`, `/learn`, `/exit`.

#### Benchmark

```bash
python main.py --mode benchmark
python main.py --mode benchmark --category multi_turn_reasoning
python main.py --mode benchmark --num-tasks 5
```

#### Demo / single task

```bash
python main.py --mode demo
python main.py --mode task --task "Plan a 7-day trip to Japan with a $3000 budget"
```

Extra: `--api-key KEY`, `--no-memory`, `--verbose`.

### Memobase Profile + Event Demo (real SDK)

`profile_demo.py` uses the **real** Memobase SDK: **Profile** (topic → sub-topic → content, e.g. `basic_info→城市`, `work→职位`) and **Event Memory** (timeline for “when did we discuss budget?”). Pipeline: `insert` → `flush` → `profile` / `event` / `context`.

#### Prerequisites

Memobase extracts **server-side**; you need a reachable service:

- **Self-hosted**: [memodb-io/memobase](https://github.com/memodb-io/memobase) (docker compose). Default `http://localhost:8019`, token `secret`. Extraction model is in the **server’s** `.env` / `config.yaml` (`--model` on the client is informational only).  
- **Cloud**: `project_url` + `api_key` from https://www.memobase.io  

Client: `--project-url` / `--api-key` or `MEMOBASE_PROJECT_URL` / `MEMOBASE_API_KEY` (see `env.example`).

#### Running

```bash
pip install -r requirements.txt

python profile_demo.py
python profile_demo.py --dry-run
python profile_demo.py --op profile
python profile_demo.py --op event
python profile_demo.py --op context
python profile_demo.py --input chat.json --output result.json
```

If no server is reachable, the demo exits with an actionable message (try `--dry-run` or set `--project-url`)—it does **not** invent memory output.

### Architecture (hand-rolled)

- **MemoryStore** (`agent.py`): pickle persistence, compression, clustering, decay, retrieval  
- **MemobaseAgent** (`agent.py`): message processing with memory context, learning, metrics  
- **LOCOMOBenchmark** (`locomo_benchmark.py`): tasks, scoring, persistence  

### Memory strategies

**Compression:** sort by importance/recency; keep important; cluster low-importance into summaries.  
**Consolidation:** decay; drop very low importance; extract patterns → procedural.  
**Retrieval:** content search + recent episodic + procedural → format into context.

### Results / development

Benchmark outputs under `benchmark_results/`. Extend tools / memory types in `config.py` / `locomo_benchmark.py` as needed.

### Troubleshooting

1. API key: `KIMI_API_KEY` in `.env`  
2. Memory overflow: lower `MAX_MEMORY_ENTRIES`, more aggressive compression, manual consolidation  
3. Slow: reduce `MODEL_MAX_TOKENS`, enable cache, category-specific benchmarks  

### License / acknowledgments

MIT-style educational use. Kimi by Moonshot AI; Memobase concepts; LOCOMO-inspired design.

---

## 中文

### 本目录两条线——不要搞混

1. **真实 Memobase 框架演示**（`profile_demo.py`）——官方开源 SDK（`memobase>=0.0.27`）对接**正在运行的 Memobase 服务**，展示书中的 *Profile*（结构化用户属性）+ *Event Memory*（时间线）。见下文 Profile + Event 演示。  
2. **手写记忆 Agent**（`agent.py` / `main.py`）——自包含、受 Memobase 启发的 `MemoryStore`（情景 / 语义 / 程序 / 工作记忆，pickle 持久化），直接调 Kimi。**不需要 Memobase 服务**，只要 `KIMI_API_KEY`。`--mode`（interactive / benchmark / demo / task）驱动的是这条线。

### 手写 Agent 功能

**记忆类型：** 情景、语义、程序、工作记忆。  
**操作：** 超阈值压缩、巩固、重要性衰减、聚类、相关度/近因检索。  
**模型：** Kimi K3。  
**评测类别：** 多轮推理、长上下文问答、任务规划、知识整合、工具使用。

### 安装

```bash
cd chapter3/memobase
pip install -r requirements.txt
cp env.example .env
# 手写 Agent 填写 Kimi API Key
```

在 `config.py` 中调整模型、记忆阈值、基准与日志。

### 用法（手写 Agent）

```bash
python main.py --mode interactive
# /help /memory /clear /reset /learn /exit

python main.py --mode benchmark
python main.py --mode benchmark --category multi_turn_reasoning
python main.py --mode benchmark --num-tasks 5

python main.py --mode demo
python main.py --mode task --task "Plan a 7-day trip to Japan with a $3000 budget"
```

额外：`--api-key`、`--no-memory`、`--verbose`。

### Memobase Profile + Event 演示（真实 SDK）

`profile_demo.py` 展示 **Profile**（topic → sub-topic → content）与 **Event Memory**（时间线）。流水线：`insert` → `flush` → `profile` / `event` / `context`。

#### 前置

抽取在**服务端**完成，需要可访问的 Memobase：

- **自托管**：[memodb-io/memobase](https://github.com/memodb-io/memobase)（docker compose）。默认 `http://localhost:8019`，token `secret`。抽取模型在**服务端**配置。  
- **云端**：https://www.memobase.io 的 `project_url` + `api_key`  

客户端：`--project-url` / `--api-key` 或 `MEMOBASE_PROJECT_URL` / `MEMOBASE_API_KEY`。

#### 运行

```bash
pip install -r requirements.txt

python profile_demo.py
python profile_demo.py --dry-run
python profile_demo.py --op profile
python profile_demo.py --op event
python profile_demo.py --op context
python profile_demo.py --input chat.json --output result.json
```

连不上服务时会给出可操作提示（`--dry-run` 或配置 URL），**不会捏造**记忆结果。

### 架构（手写）

- **MemoryStore** / **MemobaseAgent**（`agent.py`）  
- **LOCOMOBenchmark**（`locomo_benchmark.py`）  

压缩 / 巩固 / 检索策略与 English 节相同。

### 结果与排错

结果目录 `benchmark_results/`。常见问题：API Key、记忆溢出（调阈值/压缩）、性能（降 `MODEL_MAX_TOKENS`）。

### 许可

教学用途；致谢 Moonshot / Memobase / LOCOMO 相关设计。

---

## Notes / 说明

### OpenRouter 通用回退 / Universal OpenRouter fallback

If primary keys are absent and `OPENROUTER_API_KEY` is set, chat LLM routes through OpenRouter with automatic model mapping; `OPENROUTER_MODEL` forces an id. See `env.example`.
