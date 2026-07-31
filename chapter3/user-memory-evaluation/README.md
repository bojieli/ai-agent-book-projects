# User Memory Evaluation Framework / 用户记忆评估框架

> Companion material for *AI Agents in Depth*, Chapter 3 — **Experiment 3-1**: three-layer memory eval suite with offline keyword-recall compare.  
> 配套《深入理解 AI Agent》第 3 章 **实验 3-1**：三层记忆评测集，含离线 keyword-recall 对照表。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Overview

Evaluates agent memory on three progressive layers using realistic business conversations: store, retrieve, and use information from user interactions.

#### Layer 1: Basic Recall & Direct Retrieval  
Single conversation; explicit facts (account numbers, confirmation codes, appointments).

#### Layer 2: Contextual Reasoning & Disambiguation  
Multiple conversations; ambiguous asks; retrieve **all** relevant info; know when to clarify.

#### Layer 3: Cross-Session Synthesis & Proactive Assistance  
Synthesize across sessions; surface critical connections; proactive help without being asked.

### Features

- **60 test cases** (20 per layer; 50+ rounds each)  
- **Experiment 6-3 structured LLM-as-Judge**: precision, recall, reasoning,
  proactivity, plus a hallucination veto; every dimension includes evidence and
  a concrete boundary-case decision
- Banking, insurance, healthcare, travel, retail, …
- Interactive, batch, programmatic modes
- Detailed reports

### Quickstart: scored comparison (Experiment 3-1)

Fully offline (no API key) with `keyword-recall` on fixtures:

```bash
python main.py --mode compare --metric keyword-recall
```

Real output (8 annotated cases, four configs):

```
             Memory System Comparison (Keyword Recall, 0.000-1.000)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Layer                         ┃ full_ctx  ┃ json_card ┃ simple_nt ┃ no_memry ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
│ Layer 1 · Basic Recall        │  1.000    │  1.000    │  0.417    │  0.000   │
│ Layer 2 · Disambiguation      │  1.000    │  1.000    │  0.333    │  0.000   │
│ Layer 3 · Proactive Synthesis │  1.000    │  1.000    │  0.125    │  0.000   │
│ Overall                       │  1.000    │  1.000    │  0.323    │  0.000   │
└───────────────────────────────┴───────────┴───────────┴───────────┴──────────┘
```

Scores are **computed** from `fixtures/system_responses.example.json` (not hand-written). *Simple Notes* does OK on Layer 1 but drops on L2/L3; *Advanced JSON Cards* holds across layers.

- `fixtures/gold_facts.json` — key facts from `test_cases/*.yaml`  
- `fixtures/system_responses.example.json` — replace with your `{system: {test_id: answer}}`  

### Installation

```bash
# From the repository root: use the shared Chapter 3 environment
uv sync --locked --python 3.12 --extra ch3

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch3]"

cd chapter3/user-memory-evaluation

# Single-project compatibility path, still supported during migration:
# python -m pip install -r requirements.txt

cp env.example .env
# API credentials for LLM judge (Kimi or OpenAI)
```

### Usage

`python main.py --help` (Chinese). Key flags:

| Flag | Meaning |
| --- | --- |
| `--mode {interactive,demo,batch,compare}` | Default `interactive` |
| `--metric {llm-judge,keyword-recall}` | Judge (API) or offline key-fact recall |
| `--responses PATH` | Answers JSON |
| `--gold PATH` | Gold facts (default `fixtures/gold_facts.json`) |
| `--category {layer1,layer2,layer3}` | One layer |
| `--test-cases-dir PATH` | Alternate dataset dir |
| `--evaluator {kimi,openai}` / `--model` | Judge backend |
| `--output PATH` | Report file |
| `--list` | List cases offline and exit |

```bash
python main.py --mode compare --metric keyword-recall --output compare.txt
python main.py --mode compare --metric keyword-recall --category layer3
python main.py --mode compare --metric llm-judge --evaluator kimi

python main.py --mode interactive
python main.py --mode demo
python main.py --mode batch --responses agent_responses.json
```

Batch JSON: `{"layer1_01_bank_account": "Your checking account number is 4429853327.", ...}`.

### Programmatic usage

```python
from framework import UserMemoryEvaluationFramework

framework = UserMemoryEvaluationFramework()
test_cases = framework.list_test_cases(category="layer1")
histories = framework.get_conversation_histories("layer1_01_bank_account")
question = framework.get_user_question("layer1_01_bank_account")
result = framework.submit_and_evaluate(
    test_id="layer1_01_bank_account",
    agent_response="Your checking account number is 4429853327.",
    extracted_memory=None
)
print(f"Reward: {result.reward:.3f}")
print(f"Passed: {result.reward >= 0.6}")
print(f"Reasoning: {result.reasoning}")
```

### Test case structure

Fields: `test_id`, `category`, `title`, `conversation_histories`, `user_question`, `evaluation_criteria`, `expected_behavior`.

L1: bank accounts, claims, appointments, flights, installs.  
L2: multi-vehicle, multi-card, multi-policy.  
L3: passport vs travel, coverage vs procedures, cross-session tax/warranty.

### Metrics

**`keyword-recall` (offline):** `reward = (# gold facts in answer) / (# gold facts)`, normalized substring match.

**`llm-judge` (API):** the Experiment 6-3 judge reads the authoritative
conversation source and returns four 1-4 grades (`excellent/good/pass/fail`):
factual precision, factual recall, reasoning correctness, and proactivity.
Each grade includes cited evidence and an applied boundary case. A separate
hallucination verdict is an unconditional zero-score veto. The legacy
`reward` field is derived from those four grades for existing report callers.
Task success is deliberately stricter than partial-credit reward: precision,
recall, and reasoning must each be at least `good` (3/4), and no hallucination
veto may fire. Proactivity remains diagnostic because a complete direct answer
does not always need extra advice.

Live structured-rubric check:

```bash
python validate_rubric.py \
  --test-id layer1_01_bank_account \
  --answer 'Your checking account is 4429853327. The direct-deposit routing number is 123006800.' \
  --output results/live_6_3_layer1.json
```

Experiments 6-4 and 6-9 use this judge in the end-to-end runner at
[`chapter6/user-memory-system-evaluation`](../../chapter6/user-memory-system-evaluation/).

### Configuration

```python
KIMI_API_KEY=your_key_here
DEFAULT_EVALUATOR=kimi  # or openai
MAX_RETRIES=3
REQUEST_TIMEOUT=60
```

### Extending

Add YAML under `test_cases/layer*/`. Extend `LLMEvaluator` for custom judges.

### Requirements / license

Python 3.12 with the root `ch3` extra, Kimi or OpenAI key for judge modes, 8GB+ RAM recommended. MIT License.

---

## 中文

### 概述

用真实业务对话，在三层递进难度上评测 Agent 记忆：能否存储、检索并利用用户交互中的信息。

#### 第 1 层：基础回忆与直接检索  
单会话、明确事实（账号、确认码、预约等）。

#### 第 2 层：上下文推理与消歧  
多会话、请求含糊；需取回**全部**相关信息并知道何时澄清。

#### 第 3 层：跨会话综合与主动协助  
跨会话综合、发现关键关联、主动提示。

### 特性

- **60 个用例**（每层 20；各 50+ 轮）  
- **LLM-as-Judge**  
- 银行、保险、医疗、出行、零售等  
- 交互 / 批处理 / 编程接口  
- 详细报告  

### 快速开始：记忆系统打分对照（实验 3-1）

完全离线（无需 API）：

```bash
python main.py --mode compare --metric keyword-recall
```

实测表见 English 节。分数由 `fixtures/system_responses.example.json` **计算得出**；*Simple Notes* 在 L1 尚可、L2/L3 下降，*Advanced JSON Cards* 三层均稳。

### 安装

```bash
# 在仓库根目录使用统一的第 3 章环境
uv sync --locked --python 3.12 --extra ch3

# 切换目录前先激活环境：
# macOS/Linux：
source .venv/bin/activate
# Windows PowerShell：.venv\Scripts\Activate.ps1
# Windows cmd：.venv\Scripts\activate.bat

# 未安装 uv 时可用 pip 兜底：
# python -m pip install -e ".[ch3]"

cd chapter3/user-memory-evaluation

# 迁移期间仍支持单项目兼容路径：
# python -m pip install -r requirements.txt

cp env.example .env
# LLM Judge 需配置 Kimi 或 OpenAI
```

### 用法

`python main.py --help`（中文）。主要标志见 English 表。

```bash
python main.py --mode compare --metric keyword-recall --output compare.txt
python main.py --mode compare --metric keyword-recall --category layer3
python main.py --mode compare --metric llm-judge --evaluator kimi

python main.py --mode interactive
python main.py --mode demo
python main.py --mode batch --responses agent_responses.json
```

编程接口见 English 节 `UserMemoryEvaluationFramework` 示例。

### 用例结构与指标

字段：`test_id`、`category`、`title`、`conversation_histories`、`user_question`、`evaluation_criteria`、`expected_behavior`。

- **`keyword-recall`**：离线关键事实召回  
- **`llm-judge`**：实验 6-3 的结构化 Rubric（需 API）。逐维输出事实精确率、事实召回率、
  思考正确性和主动性四档成绩、证据与边界案例；另设幻觉一票否决，触发后总分归零。

通过阈值：`reward >= 0.6`。

### 扩展与要求

在 `test_cases/layer*/` 添加 YAML；可继承 `LLMEvaluator`。根目录 `ch3` 安装使用 Python 3.12；Judge 模式需 API Key；建议 8GB+ 内存。MIT 许可。

---

## Notes / 说明

### OpenRouter 通用回退 / Universal OpenRouter fallback

When primary keys are missing and `OPENROUTER_API_KEY` is set, the chat/judge LLM can route through OpenRouter with automatic model mapping. See `env.example`.
