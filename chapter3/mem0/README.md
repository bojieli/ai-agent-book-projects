# Mem0 Agent with Kimi K3 for LOCOMO Benchmark / Mem0 Agent 与 LOCOMO 评测

> Companion material for *AI Agents in Depth*, Chapter 3 — Mem0 memory framework + Kimi for long-context multi-session memory (Experiment 3-2 comparison track).  
> 配套《深入理解 AI Agent》第 3 章——Mem0 记忆框架 + Kimi，长上下文多会话记忆（实验 3-2 对照实现之一）。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Overview

An agent that combines the **Mem0** memory framework with the **Kimi** language model for LOCOMO-style long-context multi-agent / multi-session tasks:

- **Persistent memory** via Mem0 across sessions  
- **Kimi** integration (experiment caps context budget below the model’s full window)  
- **LOCOMO benchmark** scenarios  
- Multi-session and multi-agent collaboration with shared memory  

### Features

**Core:** dynamic extract/consolidate/retrieve; context preservation; metrics (consistency, coherence, latency, memory use); local or cloud memory backend.

**LOCOMO scenarios:** collaborative planning; information sharing; multi-step problem solving; negotiation; teaching & learning.

### Installation

Prerequisites: Python 3.8+, Kimi API key; optional Mem0 cloud key.

```bash
cd chapter3/mem0
pip install -r requirements.txt
cp env.example .env
# Edit .env with API keys
```

Required env:

- `KIMI_API_KEY`  
- `MODEL_NAME` (default `kimi-k3`) — **raw Moonshot model id** (e.g. `kimi-k3`, `kimi-k2.5`); do **not** use `provider/model` slash form; Mem0 uses OpenAI-compatible provider pointed at Moonshot `base_url` and forwards the string verbatim (`kimi/k3` → “Not found the model”)  
- `MEMORY_BACKEND`: `local` / `cloud`  
- `MAX_TOKENS` (default 128000)  

### Quick start

```bash
python quickstart.py
```

Shows basic chat with memory, multi-session persistence, multi-agent collaboration.

#### Memory pipeline demo (extract — compare — decide)

Clearest demo of Mem0’s ADD / UPDATE / DELETE / NOOP and cross-session recall:

```bash
python main.py --mode demo --user-id demo_user
```

Book centerpiece (chapter 3): user lives in Beijing, later moves to Shanghai → Mem0 **UPDATE**s instead of two contradictory memories; in between, semantic search recalls the stored fact. Same routine: `memory_pipeline_example()` in `quickstart.py`.

#### Direct memory operations CLI

```bash
python main.py --help   # Chinese descriptions

python main.py --mode memory --op add   --text "我住在北京，是一名后端工程师" --user-id u1
python main.py --mode memory --op search --query "这个用户住在哪里？" --user-id u1
python main.py --mode memory --op get-all --user-id u1 --output mem.json
python main.py --mode memory --op history --memory-id <id>
python main.py --mode memory --op delete --memory-id <id>
```

Flags: `--op {add,search,get-all,history,delete}`, `--text`, `--query`, `--memory-id`, `--user-id`, `--agent-id`, `--model`, `--output`. `--text` may be a raw string or path to a JSON message list.

> Demo, memory ops, and chat modes need a working LLM key (`KIMI_API_KEY`) and vector store. Without a key the CLI parses args then reports the missing key—no fabricated memory output.

#### Interactive / batch

```bash
python main.py --mode interactive
# commands: help, memories, metrics, save, load, new, exit

python main.py --mode batch --input conversations.json --output results.json
```

Batch input format:

```json
[
  {
    "session_id": "session_001",
    "user_id": "user_001",
    "agent_id": "agent_001",
    "turns": ["First user message", "Second user message"]
  }
]
```

### LOCOMO benchmark

```bash
python experiment.py --scenarios 10 --output results/
```

Metrics: consistency, coherence, memory retention, response time, context utilization. Results JSON under `results/` with per-scenario and overall metrics.

### Architecture

- `agent.py`: `Mem0Agent`, `KimiK3Client`, `AgentContext`  
- `config.py`: Kimi / Mem0 / LOCOMO config  
- `experiment.py`: `LOCOMOBenchmark`  

Mem0 provides vector store, consolidation, retrieval, multi-level (user/agent/session) organization.

### Memory backends

```python
# Local Chroma
config.mem0.backend = "local"
config.mem0.vector_store_config = {
    "provider": "chroma",
    "config": {"collection_name": "my_collection", "path": "./data/chroma_db"}
}

# Cloud
config.mem0.backend = "cloud"
config.mem0.api_key = "your_mem0_api_key"
```

### Troubleshooting

1. API key: set valid `KIMI_API_KEY` in `.env`  
2. Local backend: write permission under `./data/`  
3. Cloud: valid `MEM0_API_KEY`  
4. Debug: `export LOG_LEVEL=DEBUG`  

### Project structure

```
mem0/
├── agent.py, config.py, experiment.py, main.py, quickstart.py
├── requirements.txt, env.example, README.md
```

### Limitations

Needs network for APIs; memory grows with use; context capped in experiment config; quality depends on model availability.

### License / acknowledgments

Part of AI Agent Book materials. Mem0 by Mem0 AI; Kimi by Moonshot AI.

---

## 中文

### 概述

将 **Mem0** 记忆框架与 **Kimi** 语言模型结合，面向 LOCOMO 风格长上下文、多会话 / 多 Agent 任务：

- 跨会话**持久记忆**  
- Kimi 集成（实验中会限制上下文预算）  
- LOCOMO 场景评测  
- 多会话、多 Agent 共享记忆协作  

### 功能

**核心：** 自动抽取 / 合并 / 检索；跨会话上下文保持；一致性、连贯性、时延、记忆利用率等指标；本地或云端记忆后端。

**LOCOMO 场景：** 协作规划、信息共享、多步解题、谈判、教与学。

### 安装

Python 3.8+、Kimi API Key；可选 Mem0 云端 Key。

```bash
cd chapter3/mem0
pip install -r requirements.txt
cp env.example .env
# 编辑 .env 填入 API Key
```

环境变量：

- `KIMI_API_KEY`  
- `MODEL_NAME`（默认 `kimi-k3`）——**原始 Moonshot 模型 id**，不要用 `provider/model` 斜杠形式  
- `MEMORY_BACKEND`：`local` / `cloud`  
- `MAX_TOKENS`（默认 128000）  

### 快速开始

```bash
python quickstart.py
```

#### 记忆管线演示（提取—对比—决策）

```bash
python main.py --mode demo --user-id demo_user
```

书中示例：先说住在北京，后来说搬到上海 → Mem0 用 **UPDATE** 修订，而不是存两条矛盾记忆；中间用语义检索调用已存事实。

#### 直接记忆操作 CLI

```bash
python main.py --help

python main.py --mode memory --op add   --text "我住在北京，是一名后端工程师" --user-id u1
python main.py --mode memory --op search --query "这个用户住在哪里？" --user-id u1
python main.py --mode memory --op get-all --user-id u1 --output mem.json
python main.py --mode memory --op history --memory-id <id>
python main.py --mode memory --op delete --memory-id <id>
```

无 Key 时 CLI 会解析参数后明确报错，**不会伪造**记忆输出。

#### 交互 / 批处理

```bash
python main.py --mode interactive
python main.py --mode batch --input conversations.json --output results.json
```

### LOCOMO 基准

```bash
python experiment.py --scenarios 10 --output results/
```

指标：一致性、连贯性、记忆保持、响应时间、上下文利用等。

### 架构与后端

- `agent.py` / `config.py` / `experiment.py`  
- 本地 Chroma 或 Mem0 Cloud（配置见 English 节代码块）  

### 故障排查

检查 `KIMI_API_KEY`、`./data/` 写权限、`MEM0_API_KEY`；`LOG_LEVEL=DEBUG`。

### 项目结构

```
mem0/
├── agent.py, config.py, experiment.py, main.py, quickstart.py
├── requirements.txt, env.example, README.md
```

### 局限与许可

需联网调用 API；记忆随使用增长；实验中上下文有上限。教学材料许可。

---

## Notes / 说明

### OpenRouter 通用回退 / Universal OpenRouter fallback

- Primary provider keys unchanged if set.  
- Else `OPENROUTER_API_KEY` routes chat LLM via `https://openrouter.ai/api/v1` with automatic model id mapping; `OPENROUTER_MODEL` forces a specific id.  
- **Note:** Mem0’s embedder still uses OpenAI embeddings (OpenRouter has no embeddings endpoint), so `OPENAI_API_KEY` is still required for store/retrieve. OpenRouter only covers the chat LLM (fact extraction, ADD/UPDATE/DELETE, answering).

Add `OPENROUTER_API_KEY=...` to `.env` (see `env.example`).
