# Experiment 5-7: Adaptive Log Parser / 自适应的日志解析系统（实验 5-7）

> Companion lab for *AI Agents in Depth*, Chapter 5 — self-evolving log parser: on unknown formats, Agent generates `parse`, tests, hot-reloads into the engine.  
> 《深入理解 AI Agent》第 5 章「代码作为系统适配器」：遇新格式不报错，Agent 生成解析代码，测试通过后热更新。

← [Chapter 5 index / 返回第 5 章目录](../README.md)

---

## English

### Overview

A **self-evolving** Agent log-parsing system. It starts with basic formats; on unparseable new formats it does not just error—it sends the failed sample + error to an Agent, which generates parsing code, auto-tests, and **hot-updates** the registry. Fully automatic; no human in the loop.

### Self-heal loop

```
  one log line
     │
     ▼
 [parse engine] try registered parsers in order
     │
     ├── some parser matches → structured fields ✅
     │
     └── all fail (new format) ❌
             │  failed sample + error
             ▼
        [codegen Agent]  ← OpenAI(gpt-5.6-luna)
             │  emit def parse(line)->dict|None
             ▼
        [auto test]  structural asserts (tester.py)
             │
             ├── fail → feedback to Agent, retry (max 3)
             │
             └── pass → [hot-load register] + persist to parsers/*.py
                          │
                          ▼
                   system parses that format ✅ (reuse after restart; no Agent)
```

Code map:

- `engine.py`: parse engine + registry + hot-load (`importlib`). Built-in `builtin_json_parser`.
- `agent.py`: codegen Agent; OpenAI generates parsers; iterative fix with failure feedback.
- `tester.py`: auto tests / structural asserts on generated `parse`.
- `demo.py`: full loop with step-by-step prints.
- `parsers/`: persisted learned parsers for reuse.

### Three progressive formats in the demo

1. Basic JSON lines (native): `{"timestamp": "...", "level": "INFO", "message": "..."}`
2. New format A — pipe-separated: `2026-07-17T10:23:01Z|INFO|agent.planner|step=3|Generated plan...`
3. New format B — nested brackets: `[2026-07-17 10:24:55] (ERROR) <tool=web_search> {latency_ms=812 status=timeout} :: ...`

A and B fail on first parse → Agent generates parser → tests pass → hot update succeeds.

### Run

```bash
pip install -r requirements.txt
cp env.example .env      # OPENAI_API_KEY (default model gpt-5.6-luna); or OPENROUTER_API_KEY fallback

python demo.py                       # full demo (two new formats, two real Agent calls; needs API key)
python demo.py --offline             # offline: canned parsers; no API key
python demo.py --quick               # one new format only; one fewer API call
python demo.py --log-file logs.txt   # step 3 uses external log file (one line per entry)
python demo.py --output out.jsonl    # write structured results as JSONL
python demo.py --help
```

CLI:

| Flag | Description |
| --- | --- |
| `--offline` | Use **canned** parser source instead of OpenAI; no key; deterministic fail-detect → gen → test → hot-reload → persist |
| `--quick` | Only pipe-separated new format; skip nested-brackets; one fewer Agent/API call |
| `--model MODEL` | Override codegen model; else `MODEL` env then `gpt-5.6-luna`. Display-only under `--offline` |
| `--log-file PATH` | External log file (one line each). Step 3 uses the learned system on that file instead of built-in mixed samples |
| `--output PATH` | Write step-3 structured results as JSONL |

Default `demo.py` calls OpenAI for real: (a) detect new-format failure; (b) Agent codegen + auto-test; (c) hot-update parse success; then a new engine loads from `parsers/` to prove persistence (no Agent).

**No API key → `--offline`**: uses `OfflineCodeGenAgent` in `agent.py` (lookup table of prewritten parsers by required fields—not a live LLM), but **fail detect → auto-test → hot-load → persist** matches online mode.

### Sample output (real run excerpt)

From `python demo.py` with gpt-5.6-luna:

```text
步骤 1：遇到新格式 A —— 自定义竖线分隔格式
(a) 先让系统解析，预期【失败】：
  ❌ 解析失败：2026-07-17T10:23:01Z|INFO|agent.planner|step=3|Generated plan with 5 actions
触发自愈闭环：
  🔎 检测到无法解析的新格式，触发自愈。报错：没有任何已注册解析器能解析该行：...
  --- 第 1/3 次：Agent 生成解析代码 ---
    | import re
    | _PATTERN = re.compile(
    |     r"^\s*"
    |     r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"
    |     r"\s*\|\s*(?P<level>[A-Za-z]+)\s*\|\s*(?P<module>[^|]+?)"
    |     r"\s*\|\s*step\s*=\s*(?P<step>\d+)\s*\|\s*(?P<message>\S(?:.*\S)?)\s*$"
    | )
    | def parse(line: str) -> dict | None:
    |     match = _PATTERN.match(line)
    |     if not match:
    |         return None
    |     fields = match.groupdict()
    |     fields["module"] = fields["module"].strip()
    |     fields["message"] = fields["message"].strip()
    |     fields["step"] = int(fields["step"])
    |     return fields
  🧪 自动测试（数据结构断言）：
    [样本1] 通过，解析出字段：['level', 'message', 'module', 'step', 'timestamp']
  ✅ 自动测试通过，已热更新注册解析器 'pipe_parser' 并持久化到 parsers/pipe_parser.py
(c) 热更新后重新解析同样的日志，预期【成功】：
  ✅ [pipe_parser] {'_parser': 'pipe_parser', 'timestamp': '2026-07-17T10:23:01Z',
     'level': 'INFO', 'module': 'agent.planner', 'step': 3, 'message': 'Generated plan with 5 actions'}
...
演示结束
新格式 A（竖线分隔）自愈结果：成功
新格式 B（嵌套括号）自愈结果：成功
持久化复用（混合格式全部解析）：成功
```

> LLM code may vary (names, regex); success = auto-test pass. `python demo.py --offline` makes the loop **deterministic** without a key.

### Adapt / extend

- **Model / provider**: OpenAI-compatible; env only.
  - `MODEL` or `python demo.py --model gpt-5.6`.
  - `OPENAI_BASE_URL` + matching `OPENAI_API_KEY` / `MODEL`.
  - Read in `CodeGenAgent.__init__` in `agent.py`.
- **New log formats**: add samples and required keys like `PIPE_LOGS` / `BRACKET_LOGS` in `demo.py`, then `self_heal(engine, agent, "your_parser", XXX_LOGS, XXX_REQUIRED)`. `required_keys` define test acceptance.
- **Live streams**: call `engine.parse_line(line)` in your read loop; catch `ParseError` to trigger self-heal. Learned parsers in `parsers/*.py` load via `engine.load_persisted()`.

### Limitations

- **Visual QA degraded**: book design renders viz code in a virtual browser + Vision LLM; here that step is **structural asserts** on `parse` (no playwright/browser). Core loop (fail → codegen → test → hot-load → persist) is **real**.
- **Safety**: generated code runs via `importlib`—trusted lab only; production needs sandbox/AST allowlists/resource limits. System prompt already constrains stdlib-only, no side effects.
- **Non-determinism**: LLM codegen is noisy; “fail → feedback retry” up to 3 times; remaining failures are normal—re-run.

---

## 中文

### 概述

一个**能自我进化**的 Agent 日志解析系统。系统初始只支持基础日志格式；遇到无法解析的新格式时，不是报错，
而是自动把失败样本 + 报错交给 Agent，让它生成能正确解析的代码，自动测试通过后**热更新**
注册进解析系统。全流程自动化，无需人工介入。

### 自愈闭环

```
  一行日志
     │
     ▼
 [解析引擎] 依次尝试已注册的解析器
     │
     ├── 有解析器认识 → 输出结构化字段 ✅
     │
     └── 全部失败（检测到新格式）❌
             │  失败样本 + 报错
             ▼
        [代码生成 Agent]  ← OpenAI(gpt-5.6-luna)
             │  生成 def parse(line)->dict|None
             ▼
        [自动测试]  数据结构断言（tester.py）
             │
             ├── 不通过 → 把失败报告反馈给 Agent 重试（最多 3 次）
             │
             └── 通过 → [热加载注册] + 持久化到 parsers/*.py
                          │
                          ▼
                   系统现在能正确解析该新格式 ✅（下次重启直接复用，不再问 Agent）
```

对应代码：
- `engine.py`：解析引擎 + 解析器注册表 + 热加载（`importlib`）。内置 `builtin_json_parser`。
- `agent.py`：代码生成 Agent，调用 OpenAI 生成解析函数，支持带失败反馈迭代修复。
- `tester.py`：自动测试，对生成的 `parse` 函数做数据结构断言。
- `demo.py`：串起整条闭环并逐步打印。
- `parsers/`：Agent 学会的解析器持久化到这里，供下次直接复用。

### 演示的三种递进格式

1. 基础 JSON 行（系统原生支持）：`{"timestamp": "...", "level": "INFO", "message": "..."}`
2. 新格式 A —— 自定义竖线分隔：`2026-07-17T10:23:01Z|INFO|agent.planner|step=3|Generated plan...`
3. 新格式 B —— 嵌套括号：`[2026-07-17 10:24:55] (ERROR) <tool=web_search> {latency_ms=812 status=timeout} :: ...`

格式 A、B 初次解析都会失败，触发 Agent 生成解析器 → 自动测试通过 → 热更新后能正确解析。

### 运行

```bash
pip install -r requirements.txt
cp env.example .env      # 填入 OPENAI_API_KEY（默认模型 gpt-5.6-luna）；未配置时设 OPENROUTER_API_KEY 自动改走 OpenRouter

python demo.py                       # 完整演示（两种新格式，两次真实 Agent 调用，需 API Key）
python demo.py --offline             # 离线演示：用预置解析器跑完整机制，无需 API Key
python demo.py --quick               # 快速模式：只演示 1 种新格式，省一次 API 调用
python demo.py --log-file logs.txt   # 步骤 3 改用外部日志文件（每行一条）验证复用
python demo.py --output out.jsonl    # 把解析出的结构化结果写成 JSONL
python demo.py --help                # 查看全部参数
```

命令行参数：

| 参数 | 说明 |
| --- | --- |
| `--offline` | 用**预置**（canned）解析器代码代替调用 OpenAI，无需 API Key，确定性地演示整条机制（失败检测→生成→测试→热重载→持久化）。 |
| `--quick` | 只演示 1 种新格式（竖线分隔），跳过嵌套括号格式，省一次 Agent/API 调用。 |
| `--model MODEL` | 覆盖代码生成模型；默认读 `MODEL` 环境变量再回落 `gpt-5.6-luna`。`--offline` 下仅作展示。 |
| `--log-file PATH` | 外部日志文件（每行一条）。给定后步骤 3 改用学到的解析系统解析该文件，替代内置混合样本，验证解析器可复用到真实日志流。 |
| `--output PATH` | 把步骤 3 解析出的结构化结果以 JSONL（每行一条 JSON）写入该文件。 |

`demo.py` 默认真实调用 OpenAI，依次演示：(a) 新格式初次解析失败被检测到；
(b) Agent 生成解析代码并通过自动测试；(c) 热更新后系统正确解析该新格式并打印结构化结果；
最后新建一个引擎，直接从 `parsers/` 加载已学会的解析器，验证持久化复用（不再调用 Agent）。

**没有 API Key 时用 `--offline`**：离线模式换用 `agent.py` 里的 `OfflineCodeGenAgent`，它按必需字段
查表返回预写好的解析器源码（并非真让 LLM 现写），但**失败检测→自动测试→热加载注册→持久化**这些
运行时机制与在线模式完全一致，可完整跑通并验证闭环。

### 预期输出示例（真实运行片段）

以下摘自一次真实运行（`python demo.py`，模型 gpt-5.6-luna）：

```text
步骤 1：遇到新格式 A —— 自定义竖线分隔格式
(a) 先让系统解析，预期【失败】：
  ❌ 解析失败：2026-07-17T10:23:01Z|INFO|agent.planner|step=3|Generated plan with 5 actions
触发自愈闭环：
  🔎 检测到无法解析的新格式，触发自愈。报错：没有任何已注册解析器能解析该行：...
  --- 第 1/3 次：Agent 生成解析代码 ---
    | import re
    | _PATTERN = re.compile(
    |     r"^\s*"
    |     r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"
    |     r"\s*\|\s*(?P<level>[A-Za-z]+)\s*\|\s*(?P<module>[^|]+?)"
    |     r"\s*\|\s*step\s*=\s*(?P<step>\d+)\s*\|\s*(?P<message>\S(?:.*\S)?)\s*$"
    | )
    | def parse(line: str) -> dict | None:
    |     match = _PATTERN.match(line)
    |     if not match:
    |         return None
    |     fields = match.groupdict()
    |     fields["module"] = fields["module"].strip()
    |     fields["message"] = fields["message"].strip()
    |     fields["step"] = int(fields["step"])
    |     return fields
  🧪 自动测试（数据结构断言）：
    [样本1] 通过，解析出字段：['level', 'message', 'module', 'step', 'timestamp']
  ✅ 自动测试通过，已热更新注册解析器 'pipe_parser' 并持久化到 parsers/pipe_parser.py
(c) 热更新后重新解析同样的日志，预期【成功】：
  ✅ [pipe_parser] {'_parser': 'pipe_parser', 'timestamp': '2026-07-17T10:23:01Z',
     'level': 'INFO', 'module': 'agent.planner', 'step': 3, 'message': 'Generated plan with 5 actions'}
...
演示结束
新格式 A（竖线分隔）自愈结果：成功
新格式 B（嵌套括号）自愈结果：成功
持久化复用（混合格式全部解析）：成功
```

> LLM 生成的代码每次可能略有不同（如变量名、正则写法），但只要通过自动测试即视为成功。
> 若用 `python demo.py --offline`，预置解析器让输出**确定性**复现上述闭环（无需 API Key）。

### 如何适配 / 扩展

- **换模型 / 供应商**：本项目统一走 OpenAI 兼容协议，改环境变量即可，无需改代码。
  - `MODEL`：换模型，例如 `MODEL=gpt-5.6`；也可在命令行用 `python demo.py --model gpt-5.6` 临时覆盖。
  - `OPENAI_BASE_URL`：换成任意 OpenAI 兼容端点（如自建网关、Moonshot/火山方舟等），
    再把 `OPENAI_API_KEY` 换成对应服务的 key、`MODEL` 换成该服务的模型名即可。
  - 三者的读取逻辑集中在 `agent.py` 的 `CodeGenAgent.__init__`。
- **换输入日志格式**：在 `demo.py` 里按现有 `PIPE_LOGS` / `BRACKET_LOGS` 的写法，加一组
  你自己的样本（`XXX_LOGS`）和必需字段列表（`XXX_REQUIRED`），再调一次
  `self_heal(engine, agent, "your_parser", XXX_LOGS, XXX_REQUIRED)` 即可让系统自学。
  `required_keys` 决定自动测试的验收标准（哪些字段必须被解析出且非空）。
- **接入真实日志流**：把 `engine.parse_line(line)` 接到你的日志读取循环上；捕获
  `ParseError` 即触发自愈闭环。已学会的解析器持久化在 `parsers/*.py`，重启后由
  `engine.load_persisted()` 自动加载复用。

### 局限与说明

- **可视化验证降级**：书中原方案是把生成的可视化代码放进**虚拟浏览器**渲染，再用
  **Vision LLM** 检查渲染效果。本机没有 playwright/浏览器环境，因此把这一步降级为对
  生成的解析函数做**数据结构断言**（用样本数据断言解析出的结构化字段正确）。核心闭环
  （检测失败 → 生成解析代码 → 自动测试 → 热加载注册新解析器 → 持久化复用）是**真实实现**的。
- **安全性**：Agent 生成的代码通过 `importlib` 直接执行，仅适用于可信实验环境；生产中应
  加沙箱、AST 白名单、资源限制等隔离手段。系统提示已约束只用标准库、无副作用。
- **确定性**：LLM 生成代码存在不确定性，故设置了「测试不通过→带反馈重试」的迭代修复
  （最多 3 次）；仍可能失败，属正常现象，重跑即可。

---

## Notes / 说明

- Use `--offline` without a key. / 无 Key 用 `--offline`。
- Commands/code/paths/env vars are identical in both language sections. / 命令、代码、路径与环境变量在中英文两侧保持一致。
