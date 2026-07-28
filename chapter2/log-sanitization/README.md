# Log Sanitization / 日志脱敏

> Companion material for *AI Agents in Depth*, Chapter 2 — intelligent log sanitization that redacts secrets and PII while preserving debug value.  
> 配套《深入理解 AI Agent》第 2 章——在保留调试信息的同时检测并脱敏日志中的敏感数据。

← [Chapter 2 index / 返回第 2 章目录](../README.md)

---

## English

### Overview

Demonstrates detecting and sanitizing sensitive data in Agent logs and tool outputs. Two complementary engines:

1. **Offline rule engine (`regex`, default)** — pure regex + validators (Luhn, ID checksum). **No Ollama, no network, no external framework.** Deterministic and fast; first line of defense before logs hit disk. Covers both **secrets** (API keys, cloud tokens, private keys, connection-string passwords) common in Agent scenarios and traditional **PII** (ID cards, phones, credit cards, emails, etc.).
2. **Local LLM engine (`llm`)** — Ollama with a small local model (default `qwen3:0.6b`) for semantic Level 3 PII. Echoes the chapter point that small models can handle structured tasks, and also shows limits (e.g. descriptive prefixes instead of raw strings → replacement failure).

> Quick demo (offline, no extra deps): `python main.py --demo` — before/after samples and category summary.

### Categories covered by the offline rule engine

`regex_sanitizer.py` processes by priority (higher wins on overlap); each becomes a labeled placeholder:

| Category | Placeholder | Notes |
| --- | --- | --- |
| Private key / cert | `[REDACTED_PRIVATE_KEY]` | PEM private key blocks |
| JWT | `[REDACTED_JWT]` | `eyJ...` three-part tokens |
| URL credentials | `[REDACTED_URL_CRED]` | `scheme://user:PASSWORD@host` |
| AWS access key | `[REDACTED_AWS_KEY]` | `AKIA...` |
| GitHub / Slack / Google / OpenAI keys | `[REDACTED_*_TOKEN]` / `[REDACTED_API_KEY]` | `ghp_`, `xoxb-`, `AIza`, `sk-` |
| Bearer token | `[REDACTED_BEARER_TOKEN]` | `Authorization: Bearer ...` |
| Password / secret assignments | `[REDACTED_SECRET]` | `password=...`, `token: ...`, etc. |
| Email | `[REDACTED_EMAIL]` | |
| Credit card | `[REDACTED_CREDIT_CARD]` | Luhn-validated to cut false positives |
| IBAN | `[REDACTED_IBAN]` | |
| US SSN | `[REDACTED_SSN]` | |
| National ID | `[REDACTED_ID_CARD]` | Mainland China 18-digit with checksum |
| Phone | `[REDACTED_PHONE]` | Mainland China |
| IP address | `[REDACTED_IP]` | IPv4 |

### Level 3 PII categories (LLM engine)

Highly sensitive items in the privacy architecture, including: SSN, credit cards, bank accounts, medical record numbers, diagnoses/treatment, prescriptions, driver’s license, passport, financial PINs, tax IDs, health insurance IDs, biometric data.

### Features

- **Offline rule engine:** regex + Luhn/ID checksum; keys/secrets + PII; no model/network
- **Local LLM:** Ollama + small model (default `qwen3:0.6b`) for privacy-preserving PII detection
- **Internal reasoning:** model thinking via `<think>` tags
- **Streaming:** real-time thinking and detection progress
- **Performance metrics:** TTFT, token counts, speeds
- **Batch processing:** user-memory-evaluation Layer 3 cases
- **Detailed metrics:** prefill / output time and tok/s for both phases

### Installation

#### 1. Install Ollama (LLM path only)

> **OpenRouter fallback:** Default is local Ollama. If Ollama is unavailable and `OPENROUTER_API_KEY` is set, the Agent falls back to OpenRouter (default hosted model `openai/gpt-5.6-luna`). To force fallback: `export OLLAMA_HOST=http://127.0.0.1:1`.

**macOS:**
```bash
brew install ollama
ollama serve  # separate terminal
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
systemctl start ollama
```

**Windows:** Download from [ollama.com](https://ollama.com/download/windows)

> Ollama steps apply only to `--mode llm` or the LLM batch eval path. Offline rule engine (`--demo`, `--input`) needs only the Python stdlib.

#### 2. Pull model
```bash
ollama pull qwen3:0.6b
```

~500MB disk; you may use `qwen3:1.7b` or `qwen3:4b` for higher accuracy.

#### 3. Python deps
```bash
pip install -r requirements.txt
```

### Usage

Full flags: `python main.py --help` (Chinese help text).

#### Offline rule demo (recommended, no Ollama)
```bash
python main.py --demo
```

#### Sanitize a log file (offline)
```bash
python main.py --input app.log                 # writes app.log.sanitized
python main.py --input app.log -o cleaned.log  # custom output
```

Rule engine alone on built-in samples:
```bash
python regex_sanitizer.py
```

#### Local LLM engine
```bash
python main.py --demo --mode llm
python main.py --input app.log --mode llm --model qwen3:1.7b
```

#### Process all Layer 3 test cases (LLM batch path)

Uses LLM only; needs Ollama and the chapter3 user-memory-evaluation framework:
```bash
python main.py
```

#### Specific test / limit
```bash
python main.py --test-id layer3_13_emergency_medical_cascade
python main.py --limit 3
```

#### Model choice
```bash
python main.py --demo --mode llm --model qwen3:4b   # default qwen3:0.6b
```

### Output structure

Under `output/`:

```
output/
├── <test_id>_sanitized.txt    # Sanitized conversation text
├── <test_id>_summary.json     # Summary of PII found and replaced
├── performance_metrics.json   # Detailed performance metrics
└── performance_summary.json   # Aggregated performance statistics
```

### Performance metrics

**Timing:** Prefill (TTFT), Output Time, Total Time (ms)  
**Tokens:** Input / Output counts; Prefill / Output speed (tok/s)  
**Sanitization:** PII items found; replacements with `[REDACTED]`

### Architecture

1. **regex_sanitizer.py** — offline rule sanitizer  
2. **samples.py** — offline demo samples  
3. **config.py** — Ollama model and PII categories  
4. **test_loader.py** — loads user-memory-evaluation cases  
5. **agent.py** — LLM sanitization via Ollama  
6. **metrics.py** — metrics collection  
7. **main.py** — entry / orchestration  

### How it works (LLM path)

1. Load conversations from user-memory-evaluation  
2. Send each to local Qwen3 with a Level 3 PII detection prompt  
3. Replace detected values with `[REDACTED]`  
4. Collect performance metrics  
5. Write sanitized logs and summaries under `output/`  

### Privacy

- Default local Ollama path sends no data to external APIs  
- OpenRouter fallback (if used) does leave the machine  
- Sanitized logs use placeholders; handle any logged original PII securely  

### Troubleshooting

**Ollama not found:** install and `ollama serve`  
**Model not found:** `ollama pull qwen3:0.6b`  
**Evaluation framework not found:** expect `../user-memory-evaluation/` (or chapter3 path used by the loader)

---

## 中文

### 概述

演示如何从 Agent 的日志与工具输出中检测并脱敏敏感信息。提供**两种互补的脱敏引擎**：

1. **离线规则引擎（regex，默认）** —— 纯正则表达式 + 校验算法（Luhn、身份证校验码），**无需 Ollama、无需网络、无需外部框架**，结果确定、速度快，适合作为日志落盘前的第一道防线。同时覆盖 Agent 场景中最常泄露的**密钥类**敏感信息（API Key、云厂商令牌、私钥、连接串口令）与传统 **PII**（身份证、手机号、信用卡、邮箱等）。
2. **本地 LLM 引擎（llm）** —— 通过 Ollama 调用本地小模型（默认 `qwen3:0.6b`）语义识别 Level 3 PII。呼应本章「小模型也能胜任结构化任务」的论点，同时也暴露小模型的局限（例如可能返回带描述前缀的值而非原始字符串，导致回填失败）。

> 想快速看效果，直接运行 `python main.py --demo`（离线，无需任何依赖）即可看到多个代表性样本的 before/after 对比与脱敏类别汇总。

### 离线规则引擎覆盖的敏感信息类别

`regex_sanitizer.py` 按优先级处理以下类别（重叠时高优先级规则胜出），每类替换为带标签的占位符：

| 类别 | 占位符 | 说明 |
| --- | --- | --- |
| 私钥 / 证书 | `[REDACTED_PRIVATE_KEY]` | PEM 私钥块 |
| JWT | `[REDACTED_JWT]` | `eyJ...` 三段式令牌 |
| 连接串凭据 | `[REDACTED_URL_CRED]` | `scheme://user:PASSWORD@host` |
| AWS 访问密钥 | `[REDACTED_AWS_KEY]` | `AKIA...` |
| GitHub / Slack / Google / OpenAI 密钥 | `[REDACTED_*_TOKEN]` / `[REDACTED_API_KEY]` | `ghp_`、`xoxb-`、`AIza`、`sk-` |
| Bearer 令牌 | `[REDACTED_BEARER_TOKEN]` | `Authorization: Bearer ...` |
| 口令 / 密钥赋值 | `[REDACTED_SECRET]` | `password=...`、`token: ...` 等 |
| 邮箱 | `[REDACTED_EMAIL]` | |
| 信用卡号 | `[REDACTED_CREDIT_CARD]` | 通过 Luhn 校验，降低误报 |
| IBAN | `[REDACTED_IBAN]` | 国际银行账号 |
| 美国社保号 | `[REDACTED_SSN]` | |
| 身份证号 | `[REDACTED_ID_CARD]` | 中国大陆 18 位，含校验码验证 |
| 手机号 | `[REDACTED_PHONE]` | 中国大陆 |
| IP 地址 | `[REDACTED_IP]` | IPv4 |

### Level 3 PII 类别（LLM 引擎）

隐私架构中的高敏感信息，包括：社保号、信用卡、银行账号、病历号、诊断与治疗信息、处方、驾照、护照、金融 PIN、税号、医保 ID、生物特征数据等。

### 功能

- **离线规则引擎**：正则 + Luhn/身份证校验；覆盖密钥/机密与 PII；无需模型与网络
- **本地 LLM**：Ollama + 小模型（默认 `qwen3:0.6b`）做隐私友好的 PII 检测
- **内部推理**：通过 `<think>` 展示模型思考过程
- **流式输出**：实时显示思考与检测进度
- **性能指标**：TTFT、token 数、处理速度
- **批量处理**：user-memory-evaluation 框架的 Layer 3 用例
- **详细指标**：prefill / 输出时间与两阶段 tok/s

### 安装

#### 1. 安装 Ollama（仅 LLM 路径需要）

> **通用回退（OpenRouter）**：本实验默认用本地 Ollama 小模型。若 Ollama 不可用（未运行 / 不可达）且设置了 `OPENROUTER_API_KEY`，Agent 会自动改走 OpenRouter（默认托管模型 `openai/gpt-5.6-luna`）。想强制走回退做验证，可把 Ollama 指到一个不可达端口：`export OLLAMA_HOST=http://127.0.0.1:1`。

**macOS:**
```bash
brew install ollama
ollama serve  # 另开终端
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
systemctl start ollama
```

**Windows:** 从 [ollama.com](https://ollama.com/download/windows) 下载

> 说明：以下 Ollama 相关步骤仅在使用 `--mode llm`（本地 LLM 引擎）或运行 LLM 批量评测路径时才需要。离线规则引擎（`--demo`、`--input`）只依赖 Python 标准库，无需安装 Ollama。

#### 2. 拉取模型
```bash
ollama pull qwen3:0.6b
```

0.6B 模型约需 500MB 磁盘；可按需换用 `qwen3:1.7b`、`qwen3:4b` 提升准确率。

#### 3. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 用法

完整参数说明见 `python main.py --help`（中文）。

#### 离线规则演示（推荐，无需 Ollama）
```bash
python main.py --demo
```

#### 脱敏任意日志文件（离线）
```bash
python main.py --input app.log                 # 结果写到 app.log.sanitized
python main.py --input app.log -o cleaned.log  # 指定输出文件
```

也可以直接运行规则引擎模块，仅对内置样本做演示：
```bash
python regex_sanitizer.py
```

#### 使用本地 LLM 引擎
```bash
python main.py --demo --mode llm
python main.py --input app.log --mode llm --model qwen3:1.7b
```

#### 处理全部 Layer 3 测试用例（LLM 批量评测路径）

该路径固定使用 LLM，需要 Ollama 与 chapter3 评测框架：
```bash
python main.py
```

#### 指定用例 / 限制数量
```bash
python main.py --test-id layer3_13_emergency_medical_cascade
python main.py --limit 3
```

#### 选择模型
```bash
python main.py --demo --mode llm --model qwen3:4b   # 默认 qwen3:0.6b
```

### 输出结构

脱敏日志与指标保存在 `output/` 目录：

```
output/
├── <test_id>_sanitized.txt    # 脱敏后的对话文本
├── <test_id>_summary.json     # 发现与替换的 PII 摘要
├── performance_metrics.json   # 详细性能指标
└── performance_summary.json   # 聚合性能统计
```

### 性能指标

**时间：** Prefill（TTFT）、输出时间、总时间（毫秒）  
**Token：** 输入/输出数量；Prefill/输出速度（tok/s）  
**脱敏：** 发现的 PII 条数；替换为 `[REDACTED]` 的次数

### 架构

1. **regex_sanitizer.py**：离线规则脱敏（正则 + Luhn/身份证校验）  
2. **samples.py**：离线演示用的代表性 Agent 日志样本  
3. **config.py**：Ollama 模型与 PII 类别配置  
4. **test_loader.py**：从 user-memory-evaluation 加载用例  
5. **agent.py**：基于 Ollama 的 LLM 脱敏逻辑  
6. **metrics.py**：性能指标采集与报告  
7. **main.py**：入口与编排  

### 工作原理（LLM 路径）

1. 从 user-memory-evaluation 加载对话历史  
2. 将每段对话送入本地 Qwen3，用专用提示检测 Level 3 PII  
3. 将检出值替换为 `[REDACTED]`  
4. 采集性能指标  
5. 将脱敏日志与性能摘要写入 `output/`  

### 隐私考量

- 默认本地 Ollama 路径不向外部 API 发送数据  
- 若走 OpenRouter 回退则会离开本机  
- 脱敏日志使用占位符；任何原始 PII 日志都应妥善保管  

### 故障排除

**找不到 Ollama：** 安装并运行 `ollama serve`  
**找不到模型：** `ollama pull qwen3:0.6b`  
**找不到评测框架：** 确认 loader 所期望的 `../user-memory-evaluation/`（或 chapter3 路径）存在

---

## Notes / 说明

- Prefer `--demo` first; Ollama is optional for the rule path.  
- 建议先跑 `--demo`；规则路径无需 Ollama。
