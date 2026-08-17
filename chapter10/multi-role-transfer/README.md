## English

# Experiment 10-1: Two Ways to Implement Multi-Role Switching (★★)

Companion code for *Deep Understanding of AI Agents*. This is a controlled comparison of two ways to implement
multi-role behavior over the same shared trajectory:

1. **System-prompt transfer**: `transfer_to_agent(target_role, reason)` swaps the current role's system prompt
   and tool set while retaining the conversation history.
2. **Skill loading**: one fixed system prompt and one fixed tool catalog remain in place; `load_skill(name)` appends
   the selected `SKILL.md` to the trajectory through progressive disclosure.

## What This Experiment Illustrates

- Unlike a predefined stage pipeline, both arms let the model decide which cross-domain capability to use next.
- Both arms use the same canonical `SKILL.md` role documents and retain the same user/assistant/tool trajectory. The
  independent variable is where that document lives: a replaced high-priority system message, or an appended Skill
  tool result. Each arm adds only the minimal instruction needed to invoke its transition tool.
- The comparison separates mechanism metrics (prefix stability and transition calls) from target metrics (task success,
  uncached input tokens, latency, and boundary instruction-following), following Chapter 6's evaluation method.
- The core mechanism is **autonomous role handoff**, but every tool used by an accepted run still performs
  real work. In particular, `web_search` calls Tavily and fails closed when `TAVILY_API_KEY` is absent;
  there is no knowledge-base/mock fallback in the current implementation.

## Architecture

| Property | Path 1 · system-prompt transfer | Path 2 · Skill loading |
|---|---|---|
| Role instruction | Replaces the system prompt | Appends a `SKILL.md` tool result |
| Tool exposure | Only the current role's tools | Fixed superset of tools; Skill supplies the behavioral boundary |
| Prefix cache | Diverges at each role boundary | Stable system/tool prefix; new Skill content is appended |
| Harness enforcement | Can make out-of-role tools unavailable | Requires a separate policy/permission gate for hard enforcement |
| Runtime complexity | Role registry + dynamic prompt/tool switching + loop guards | Stable agent loop + Skill catalog/loader |

Path 1:

```text
                        Shared conversation history (user/assistant/tool messages, retained throughout)
                                       ▲   ▲
   On each LLM call:                    │   │
   [ current role's system prompt ] + history ┘   └ only [ current role's tool set + transfer_to_agent ] exposed

   Two model actions:
     ① Call its own dedicated tools (normal function calling)
     ② Call transfer_to_agent(target_role, reason)
        → Orchestrator swaps "system prompt + tool set", history stays unchanged
        → New role inherits all history (shared context)
```

Path 2:

```text
   fixed [ system prompt + all tool schemas ] + shared history
                                                │
                          load_skill(name) ─────┘
                          → SKILL.md is appended as a tool result
                          → the static prefix is not rewritten
```

5 roles (`roles.py`):

The roster and dedicated-tool table below describe Path 1. Path 2 reuses the same five names as Skill directories;
its runtime tool visibility is intentionally fixed as shown above.

| Role | Description | Dedicated Tool Set |
|------|-------------|-------------------|
| `triage` | Front-desk triage / default entry point, decomposes requests and hands off sequentially, final wrap-up | Only `transfer_to_agent` |
| `research` | Information retrieval | `web_search` (real Tavily search with attributable URLs) |
| `coding` | Programming | `execute_python` (real execution with output capture) |
| `data_analysis` | Data analysis / computation | `calculate`, `descriptive_stats` |
| `writing` | Polishing and writing | `count_characters` |

Each role additionally holds `transfer_to_agent`, enabling autonomous handoff of control to colleagues.

Code structure:

- `tools.py` — Implementation of each role's dedicated tools + OpenAI function-calling schema
- `roles.py` — 5 role definitions (system prompts + tool sets) + `transfer_to_agent` schema
- `orchestrator.py` — Handoff orchestrator (shared history + main loop for swapping system prompts/tool sets, with deadlock prevention and self-handoff rejection)
- `skills/*/SKILL.md` — The five role capabilities used by the Skill arm
- `skill_orchestrator.py` — Stable-prefix Skill loader and agent loop
- `evaluation.py` — Deterministic outcome Rubric and trajectory-prefix boundary cases
- `experiment_protocol.json` — Pre-registered controls, strata, metrics and statistical tests
- `tasks.example.json` — Small mixed-strata task-file template for a smoke run
- `tasks.complex.example.json` — Eight multi-stage tasks with branching rules, source conflicts, explicit-stop
  instructions, prompt-injection probes, no-side-effect coding invariants and revision/loop constraints
- `run_comparison.py` — Paired live A/B runner and machine-readable report
- `demo.py` — Single-command demo entry point
- `tests/` — Offline regressions for tool dispatch and local tools

## How to Run

```bash
# From the repository root: use the shared Chapter 10 environment
uv sync --locked --python 3.12 --extra ch10

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch10]"

cd chapter10/multi-role-transfer

# Single-project compatibility path, still supported during migration:
# python -m pip install -r requirements.txt

# Configure API key (choose one)
export OPENAI_API_KEY=your-openai-api-key        # Direct export
export TAVILY_API_KEY=your-tavily-key            # Required by research.web_search; no mock fallback
# or: cp env.example .env and fill in

python demo.py
```

`demo.py` remains the single-run illustration of Path 1. Run the paired comparison with the same model in both arms:

```bash
python run_comparison.py \
  --model gpt-5.6-luna \
  --trials 5 \
  --output validation/comparison/luna-YYYYMMDD.json
```

For a formal paired campaign, provide a JSON array of records via `--task-file tasks.json`; each record may include
`id`, `prompt`, `kind`, and observable gates such as `required_capabilities`, `required_tools`, `forbidden_tools`,
`required_tool_order`, `required_output_patterns`, `forbidden_output_patterns`, `min_source_urls`,
`min_output_source_urls` and `max_deliverable_chars`. `kind` can be `cagr`, `coding`, `writing` or `complex`;
`--trials` means repetitions per task.
The built-in `--task` is intentionally a single-task smoke path, not the 30-sample claim.

For example, the three-row template can be repeated ten times as a 30-cell pilot (expand the task file for a real
production decision):

```bash
python run_comparison.py --model gpt-5.6-luna \
  --task-file tasks.example.json --trials 10 \
  --output validation/comparison/luna-pilot.json
```

For the harder rule-following pilot, use the eight-task suite. It intentionally mixes long chains with short
single-role and early-stop cases so that an extra Skill load is not automatically treated as a cost win:

```bash
python run_comparison.py --model gpt-5.6-luna \
  --task-file tasks.complex.example.json --trials 4 \
  --output validation/comparison/luna-complex-pilot.json
```

The complex records are pre-registered task specifications, not fabricated expected answers. Their deterministic
gates check observable tool calls, tool order, source URLs, forbidden actions, uncertainty language and bounded
deliverables; numerical correctness and usefulness still require the blinded quality review described below. A
formal result should expand this suite to at least 30 paired task samples and retain every failed trajectory.

The default run executes five paired end-to-end trials and one pass over each boundary case per arm. It requires
`TAVILY_API_KEY` because the research tool fails closed. To report monetary cost, pass the provider's current prices
explicitly rather than baking volatile prices into the repository:

```bash
python run_comparison.py --model gpt-5.6-luna --trials 5 \
  --input-price-per-million <price> \
  --cached-input-price-per-million <price> \
  --output-price-per-million <price>
```

When a deterministic Rubric changes, rescore saved trajectories without spending another API call:

```bash
python run_comparison.py --replay validation/comparison/previous.json \
  --output validation/comparison/previous-rescored.json
```

### Pre-registered evaluation protocol

Hold the model, provider, task text, temperature, tool implementations, maximum steps and trial count fixed. Alternate
the two arms within each trial, use a fresh conversation for every cell, source both arms' role instructions from the
same `SKILL.md` files, and retain every trajectory including failures.
Use at least 30 paired task samples (or report the five-trial run only as a smoke test), stratified across research →
analysis → writing, coding → writing, single-role tasks and tasks that explicitly stop after an intermediate stage.
This is an architecture comparison, not a one-variable prompt ablation: Path 1 has hard tool isolation while Path 2
keeps a fixed tool superset to preserve the prefix. Add a third fixed-tools/dynamic-prompt arm if a pure prompt-carrier
causal estimate is required.

Report three groups of metrics:

- **Cost**: API calls, input/output tokens, cached and uncached input tokens, wall-clock p50/p95, and price-recomputed
  dollars. Prefix-cache hit tokens are the target measurement; prompt length alone is only a mechanism proxy.
- Distinguish model **KV/prompt cache** from a **KB/Skill document cache**: the former is measured by provider
  `cached_tokens`; the latter needs its own hit/miss, version-key and load-latency fields. A Skill cache hit does not
  imply a model-prefix cache hit.
- This protocol defines Skill loading as appending `SKILL.md` through a tool result. A runtime that mutates a
  system/developer message or tool schemas when loading a Skill changes the prefix and belongs in a separate arm.
- **Actual effect**: deterministic outcome gates first (source URL, real calculation call, correct CAGR range, format,
  deliverable length, and required capability-sequence completion), then a blinded pairwise judge or human reviewer for usefulness and writing quality. If a runtime
  adds a wrap-up envelope, apply the length limit to the text passed to `count_characters`, identically in both arms.
  Apply a hallucination veto.
- **Boundary instruction-following**: use frozen trajectory prefixes for current-user override, prompt injection in
  retrieved text, missing evidence and transition loops. Score only observable next actions and forbidden actions.

For binary paired outcomes report Pass@1 and Pass-consecutive-k, a paired 95% bootstrap interval, and McNemar's test;
for token/latency deltas report paired medians and bootstrap intervals. Randomize A/B display order for pairwise judging
and judge the swapped order a second time to control position bias. Do not infer a winner from one successful trace.

Configurable environment variables (all have defaults):
`OPENAI_API_KEY`, `OPENAI_BASE_URL` (default `https://api.openai.com/v1`),
`OPENAI_MODEL` (default `gpt-5.6-luna`), and `TAVILY_API_KEY` for the research role's real web search.

**General fallback**: Prefers direct OpenAI connection via `OPENAI_API_KEY`; if that variable is not set but
`OPENROUTER_API_KEY` is set, it automatically switches to OpenRouter and maps the model name to its namespace
(`gpt-5.6-luna` → `openai/gpt-5.6-luna`). Note: The `gpt-5.6` series requires organization verification for direct OpenAI access;
setting only `OPENROUTER_API_KEY` (without `OPENAI_API_KEY`) forces OpenRouter, which is simpler.

### Command-Line Arguments

All arguments are optional; if omitted, behavior is identical to the original version (runs the default `cagr` scenario). Run
`python demo.py --help` to see the full Chinese documentation.

| Argument | Effect |
|----------|--------|
| `--list-roles` | **Offline self-check**: Only prints the role roster + built-in scenarios and exits, **no API Key required** |
| `--scenario {cagr,solar,coding}` | Select a built-in scenario (default `cagr`); `coding` routes to the `coding` role to actually run code |
| `--task "..."` | Custom task text, overrides `--scenario` |
| `--role {triage,research,coding,data_analysis,writing}` | Specify the **starting role** (alias `--starting-role`, default `triage`) |
| `--interactive` | **Interactive multi-turn**: Reuses the same orchestrator, roles and shared history persist across turns |
| `--model gpt-5.6-luna` | Temporarily overrides `OPENAI_MODEL` |
| `--max-steps 30` | Hard upper limit on LLM rounds per message (default 20, prevents infinite loops) |

Examples:

```bash
python demo.py --list-roles            # Offline view of roles/scenarios, no API call
python demo.py --scenario coding       # Scenario routed to the coding role
python demo.py --task "Research and summarize…" # Custom task
python demo.py --role research         # Start from the research role
python demo.py --interactive           # Interactive multi-turn, type exit to quit
```

Run the provenance-complete Moonshot + Tavily acceptance campaign with:

```bash
python run_official_experiment.py --run-id exp10-1-kimi-k2.5-tavily-receipts-YYYYMMDD-vN
```

This path retains credential-free raw Moonshot requests/responses, response IDs
and usage, raw Tavily HTTP response bodies with the API key removed from the
stored request, current runtime source hashes, artifact hashes, and a combined
behavior/provenance acceptance record.

Three built-in scenarios (`SCENARIOS`): `cagr` (default, new energy vehicle sales → CAGR → investment summary),
`solar` (same chain with a different set of photovoltaic installation data), `coding` (routes to the `coding` role
to actually run a Fibonacci script via `execute_python`, then `writing`/`triage` wraps up).

## Offline Validation

```bash
# From the repository root; include dev tools for pytest.
uv sync --locked --python 3.12 --extra ch10 --extra dev
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1

cd chapter10/multi-role-transfer
python -m pytest tests
python -m pytest tests/test_skill_comparison.py
python demo.py --list-roles
```

`tests/` contains offline regressions for `count_characters`, `execute_python` timeouts, and tool-dispatch error handling. They do not require an API key.

## Formal v2 evidence

The authoritative package is [`validation/comparison/runs/exp10-1-qwen35flash-20260809-v2/`](validation/comparison/runs/exp10-1-qwen35flash-20260809-v2/), independently checked by [`validate_comparison.py`](validate_comparison.py) (12/12 gates). The campaign uses `qwen/qwen3.5-flash-02-23` through OpenRouter, 30 paired tasks at temperature 0, an eight-round per-cell limit, 60 main trajectories, and 12 boundary trajectories. The Skill arm now requires `load_skill("triage")` before any specialist tool.

For this bounded model/configuration, Skill passes 15/30 deterministic task gates versus Transfer's 2/30. Skill's median delta is +6,855 uncached input tokens, +4.368 seconds, and +$0.00044304 repriced cost. An independent Gemini 2.5 Flash Lite judge reviewed all 30 pairs twice with swapped order: Skill 32, Transfer 20, and 8 ties across 60 judgments. These are bounded architecture results, not model-independent superiority claims.

The Skill arm keeps all tool schemas visible to preserve a stable prefix, but the Harness rejects tools before a Skill is loaded or when the current Skill does not authorize them. Visibility is therefore not mistaken for progressive disclosure.

## Path 1 Demo and Historical Evidence

`demo.py` presents a composite task requiring **multiple cross-domain switches**:

> Look up China's new energy vehicle sales for 2021–2023 → Calculate the compound annual growth rate (CAGR) → Write a Chinese summary for investors

Expected autonomous handoff chain:

```text
triage → research → data_analysis → writing
```

- `triage` determines the first step is to look up data, hands off to `research`;
- `research` uses `web_search` to find the three years of sales data, hands off to `data_analysis`;
- `data_analysis` uses `calculate` to compute CAGR ≈ 64.22%, hands off to `writing`;
- `writing` synthesizes the sales data and CAGR from **the prior history** and directly produces the final draft.

`writing` never retrieved or computed anything itself, yet it can reference accurate sales figures and growth rates —
this is evidence of **shared context**. After execution, the full handoff chain, each `from→to` and `reason`,
and a **role-by-role summary** (who called which dedicated tools, who produced the final reply) are printed,
making it clear at a glance how "different specialized roles take turns on the same history."

> Note: Real LLM output has randomness; specific wording or step counts in a given run may vary slightly, but the handoff mechanism is consistent.

### Expected Output Shape

The following excerpt illustrates the console format. The canonical accepted real run is
[`validation/runs/exp10-1-kimi-k2.5-tavily-receipts-20260730-v3/manifest.json`](validation/runs/exp10-1-kimi-k2.5-tavily-receipts-20260730-v3/manifest.json):
it records Moonshot `kimi-k2.5`, three real Tavily searches with source URLs, the complete handoff chain,
the calculation tool call, and the counted draft. All 9 behavior and 6 provenance gates passed. The run
retains nine raw Moonshot requests/responses with unique response IDs and usage, three raw Tavily response
bodies, five runtime source hashes, and four artifact hashes; all declared hashes recompute and the
credential scan found zero hits. The older v2 JSON remains as a sanitized summary-only historical run.

```text
=== Role Roster (5 specialized roles) ===
• triage — Front-desk triage (default entry)
    Tool set: ['transfer_to_agent']
    System prompt (first line): You are the 'front-desk triage' role of the general assistant system, and the default entry point.
• research — Information retrieval specialist
    Tool set: ['web_search', 'transfer_to_agent']
    ...(other roles omitted, see full list in the role table above)

┌── Current role: Information Retrieval Specialist (research)   Tools: ['web_search', 'transfer_to_agent']
└── 🔧 Calling tool web_search args={'query': 'China 2021 2022 2023 new energy vehicle sales CPCA CAAM'}
    → [Search Results · China Passenger Car Association / CAAM]…2021: 3.521 million units / 2022: 6.887 million units / 2023: 9.495 million units
┌── Current role: Data Analysis Specialist (data_analysis)   Tools: ['calculate', 'descriptive_stats', 'transfer_to_agent']
└── 🔧 Calling tool calculate args={'expression': '(9.495/3.521)**(1/2)-1'}
    → (9.495/3.521)**(1/2)-1 = 0.6421562289791105

================ Run Summary ================
Autonomous handoff chain: triage → research → data_analysis → writing → triage
Handoff count: 4
  1. triage → research  |  reason: Need to first retrieve China's 2021, 2022, 2023 new energy vehicle sales and reliable sources, to provide data for subsequent CAGR calculation and investor summary.
  2. research → data_analysis  |  reason: Retrieved 2021, 2022, 2023 NEV sales data; please calculate the two-year CAGR from 2021 to 2023 and provide the result for subsequent writing.
  3. data_analysis → writing  |  reason: Sales data and CAGR completed: 2021: 3.521M, 2022: 6.887M, 2023: 9.495M; 2021–2023 CAGR=(9.495/3.521)^(1/2)-1=64.22%. Please write a Chinese investor summary of no more than 120 characters based on this.
  4. writing → triage  |  reason: Completed investor summary and verified length (101 characters, within 120-char limit)… Please do final wrap-up confirmation.

Role-by-role breakdown (who used which tools, who produced the final reply):
  triage        : (routing/handoff only, no dedicated tools used)  ⇒ Produced final reply
  research      : web_search
  data_analysis : calculate
  writing       : count_characters

Final output:
According to public data from CAAM, China's new energy vehicle sales grew from 3.521 million units in 2021 to 6.887 million in 2022 and 9.495 million in 2023. The two-year CAGR from 2021 to 2023 reached 64.2%, indicating rapid market expansion with significant growth potential.
```

## Interpretation and Limitations

- The default model is `gpt-5.6-luna`; whether the handoff follows the expected chain depends heavily on the selected model's instruction-following ability. Switching models may yield different results.
- Prefix-cache reuse is provider dependent. Use the provider-reported `cached_tokens` field when available; otherwise
  label any prefix-hash comparison as a mechanism proxy rather than measured cache savings.
- The Skill arm intentionally keeps all tool schemas stable and visible. A Skill is a soft behavioral boundary, not a
  permission boundary. High-risk tools still need a harness-level allowlist or approval gate.
- `load_skill` adds an extra tool round and appends instructions to the trajectory. On short, single-role tasks that
  overhead can outweigh cache savings; the experiment must include such tasks instead of only long handoff chains.
- The `research` role requires a live Tavily credential. Missing credentials, HTTP failures, or empty provider results are surfaced explicitly and never replaced with canned facts.
- Real LLM output has randomness: the exact number of handoff steps, the wording of each `reason`, whether the `coding` role is visited, etc., may vary between runs, but the handoff mechanism itself is consistent.
- `orchestrator.py` has a hard `max_steps` limit (default 20) and a correction prompt for "same (role, tool, arguments) called ≥3 times consecutively" to prevent model infinite loops; this is a safety net, not an indication that every run will use all these steps.

---

## 中文

# 实验 10-1：多角色转换的两种实现路径对比（★★）

《深入理解 AI Agent》配套代码。实验在同一条共享轨迹上，对比两种实现多角色行为的方法：

1. **切换系统提示词**：`transfer_to_agent(target_role, reason)` 保留对话历史，但替换当前角色的
   system prompt 和工具集；
2. **加载 Skill**：system prompt 与工具目录全程固定，通过 `load_skill(name)` 把相应 `SKILL.md`
   作为工具结果追加到轨迹末尾，实现渐进式披露。

## 这个实验想说明什么

- 两条路径都由 Agent 自主判断下一项专业能力，都共享完整历史，并共用同一份 `SKILL.md` 角色规程；
  唯一核心变量是这份规程放在被替换的 system prompt，还是追加的 Skill tool result 中。两边只增加
  调用各自转换工具所需的最小机制说明。
- 实验按第六章的方法区分**机制指标**与**目标指标**：前缀是否稳定只是机制，真正要比较的是
  未缓存输入 token、延迟、实际任务成功率和边界指令遵循率。
- 机制重点是「自主角色移交」，但验收运行中调用的工具仍必须执行真实工作。当前
  `web_search` 真实调用 Tavily；缺少 `TAVILY_API_KEY` 时会失败关闭，不再回退到内置知识库或 mock。

## 架构

| 属性 | 路径一：系统提示词切换 | 路径二：Skill 加载 |
|---|---|---|
| 角色指令的位置 | 替换 system prompt | 以 `SKILL.md` 工具结果追加 |
| 工具可见性 | 只暴露当前角色的工具 | 固定暴露工具全集，由 Skill 形成行为边界 |
| 前缀缓存 | 每次切换都从差异点重新计算 | system prompt 与工具定义保持稳定 |
| Harness 硬约束 | 可让越界工具在结构上不可调用 | 仍需额外权限门或 allowlist |
| 实现复杂度 | 角色注册表、动态提示词/工具切换、防循环 | 固定 Agent 循环、Skill 目录与加载器 |

路径一：

```text
                        共享对话历史 history（user/assistant/tool 消息，全程保留）
                                        ▲   ▲
   每轮调用大模型时：                     │   │
   [ 当前角色的 system prompt ] + history ┘   └ 只暴露 [ 当前角色工具集 + transfer_to_agent ]

   模型两种动作：
     ① 调用自己的专属工具（普通 function calling）
     ② 调用 transfer_to_agent(target_role, reason)
        → 编排器换掉「系统提示词 + 工具集」，history 原样不动
        → 新角色继承全部历史（共享上下文）
```

路径二：

```text
   固定 [ system prompt + 全部工具 schema ] + 共享 history
                                                   │
                              load_skill(name) ────┘
                              → SKILL.md 作为 tool result 追加
                              → 不改写静态前缀
```

5 个角色（`roles.py`）：

下面的角色与专属工具表描述路径一；路径二复用这五个名字作为 Skill 目录，运行时工具可见性固定为上方表格所示。

| 角色 | 说明 | 专属工具集 |
|------|------|-----------|
| `triage` | 前台分诊 / 默认入口，拆解需求并按序移交、最后收尾 | 仅 `transfer_to_agent` |
| `research` | 信息检索 | `web_search`（真实 Tavily 检索，返回可追溯 URL） |
| `coding` | 编程 | `execute_python`（真实执行并捕获输出） |
| `data_analysis` | 数据分析 / 计算 | `calculate`、`descriptive_stats` |
| `writing` | 润色写作 | `count_characters` |

每个角色都额外持有 `transfer_to_agent`，可自主把控制权交给同事。

代码结构：

- `tools.py` —— 各角色专属工具的实现 + OpenAI function-calling schema
- `roles.py` —— 5 个角色定义（系统提示词 + 工具集）+ `transfer_to_agent` schema
- `orchestrator.py` —— 移交编排器（共享历史 + 换系统提示词/工具集的主循环，含防死循环/拒绝自我移交）
- `skills/*/SKILL.md` —— Skill 路径的五项角色能力
- `skill_orchestrator.py` —— 静态前缀的 Skill 加载器与 Agent 循环
- `evaluation.py` —— 确定性结果 Rubric 与轨迹前缀边界用例
- `experiment_protocol.json` —— 预注册控制变量、任务分层、指标与统计检验
- `tasks.example.json` —— 小型混合任务分层模板，用于 smoke run
- `tasks.complex.example.json` —— 八个含分支、冲突来源、显式停止、注入探针、无副作用和回退规则的复杂任务
- `run_comparison.py` —— 成对 A/B 运行器与机器可读报告
- `demo.py` —— 一条命令的演示入口
- `tests/` —— 工具分发与本地工具的离线回归测试

## 运行方式

```bash
# 从仓库根目录开始：使用共享的第 10 章环境
uv sync --locked --python 3.12 --extra ch10

# 切换目录前先激活环境：
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# 未安装 uv 时可用 pip 兜底：
# python -m pip install -e ".[ch10]"

cd chapter10/multi-role-transfer

# 迁移期间仍支持单项目兼容路径：
# python -m pip install -r requirements.txt

# 配置 key（二选一）
export OPENAI_API_KEY=your-openai-api-key        # 直接 export
export TAVILY_API_KEY=your-tavily-key            # research.web_search 必需；无 mock fallback
# 或： cp env.example .env 后填写

python demo.py
```

`demo.py` 保留为路径一的单次机制演示。正式对比运行：

```bash
python run_comparison.py \
  --model gpt-5.6-luna \
  --trials 5 \
  --output validation/comparison/luna-YYYYMMDD.json
```

正式成对 campaign 应用 `--task-file tasks.json` 传入任务 JSON 数组；每项除 `id/prompt/kind` 外，还可声明
`required_capabilities`、`required_tools`、`forbidden_tools`、`required_tool_order`、
`required_output_patterns`、`forbidden_output_patterns`、`min_source_urls`、`min_output_source_urls` 和
`max_deliverable_chars`。
`kind` 可为 `cagr`、`coding`、`writing` 或 `complex`，`--trials` 表示每个任务的重复次数。内置 `--task`
只用于单任务 smoke test，不能冒充 30 个样本。

例如，三行模板重复十次可形成 30 个配对单元的 pilot（正式架构决策前应继续扩展任务集）：

```bash
python run_comparison.py --model gpt-5.6-luna \
  --task-file tasks.example.json --trials 10 \
  --output validation/comparison/luna-pilot.json
```

更严格的规则遵循 pilot 使用八个复杂任务；它同时包含长链路和短任务/提前停止任务，因此不会把额外的 Skill
加载轮次自动当成成本优势：

```bash
python run_comparison.py --model gpt-5.6-luna \
  --task-file tasks.complex.example.json --trials 4 \
  --output validation/comparison/luna-complex-pilot.json
```

这些记录是预注册的任务规格，不是预先写好的答案。确定性门禁只检查可观察的工具调用、调用顺序、来源 URL、
禁止动作、不确定性表述和交付稿边界；数值正确性与实际可用性仍需下方的盲测质量评审。正式结论应扩展到至少
30 个成对样本，并保留每一条失败轨迹。

默认会完成五组端到端配对试验，并对两条路径各跑一遍边界集。`research` 使用真实 Tavily，
因此必须设置 `TAVILY_API_KEY`。金额成本不在代码里写死；运行时用服务商当日价格传入
`--input-price-per-million`、`--cached-input-price-per-million` 和
`--output-price-per-million`，原始 token 用量始终保留，日后可重新计价。

确定性 Rubric 更新后，可重放已有轨迹而不再次调用 API：

```bash
python run_comparison.py --replay validation/comparison/previous.json \
  --output validation/comparison/previous-rescored.json
```

### 预注册评估协议

固定模型、服务商、任务文本、温度、工具实现、角色规程、最大步数和重复次数；每个实验单元都使用
新会话，在每个 trial 内交替运行 A/B，并保留失败轨迹。至少应使用 30 个配对任务（五次只算 smoke test），
覆盖“检索→分析→写作”“编程→写作”、单角色短任务，以及用户明确要求在中间阶段停止的任务。
这是一项架构路径对比，不是只改变一行提示词的纯消融：路径一硬隔离工具，路径二固定工具全集以保持前缀。
若要单独估计提示词载体的因果效应，应再加入“固定工具全集 + 动态 system prompt”的第三臂。

- **成本**：记录 API 调用数、输入/输出 token、缓存/未缓存输入 token、墙钟时间 p50/p95 与按
  当日价格重算的金额。前缀长度和 hash 只是机制代理，服务商返回的 `cached_tokens` 才是目标测量。
- 区分模型 **KV/prompt cache** 与 **KB/Skill 文档缓存**：前者用服务商的 `cached_tokens` 测量；后者
  需要独立记录命中/未命中、`name@version` 缓存键和加载延迟。Skill 命中不代表模型前缀也命中。
- 本协议把 Skill 加载严格定义为通过 tool result 追加 `SKILL.md`。若某运行时会在加载时改写
  system/developer message 或工具 schema，它改变了前缀，应另设实验 arm，不能沿用这里的缓存假设。
- **实际效果**：先用确定性门禁检查来源 URL、真实计算调用、CAGR 合理范围、格式、交付稿长度和预期能力序列，再由
  盲测的人类或异源 LLM 做成对质量评审。若运行时给最终稿加了收尾包装，长度只计算传给
  `count_characters` 的交付稿，且两条路径口径相同；幻觉是一票否决项。
- **边界指令遵循**：冻结“首个错误之前”的轨迹前缀，检查当前用户指令覆盖、检索内容提示注入、
  证据缺失和角色/Skill 循环。只评分可观察的下一步动作、必需证据和禁止动作，不猜隐藏思维。

二元配对结果报告 Pass@1、Pass consecutive@k、配对 bootstrap 95% 区间和 McNemar 检验；token
与延迟报告配对中位数及 bootstrap 区间。成对质量评审须随机 A/B 展示位置，并交换顺序再评一次。
单条成功轨迹不足以证明任一路径更优。

可配环境变量（均有默认值）：
`OPENAI_API_KEY`、`OPENAI_BASE_URL`（默认 `https://api.openai.com/v1`）、
`OPENAI_MODEL`（默认 `gpt-5.6-luna`），以及供检索角色真实联网使用的 `TAVILY_API_KEY`。

**通用回退**：优先用 `OPENAI_API_KEY` 直连 OpenAI；若未设置该变量但设了
`OPENROUTER_API_KEY`，则自动改走 OpenRouter，并把模型名映射到其命名空间
（`gpt-5.6-luna` → `openai/gpt-5.6-luna`）。提示：`gpt-5.6` 系列直连 OpenAI 需组织验证，
只填 `OPENROUTER_API_KEY`（不填 `OPENAI_API_KEY`）即可强制走 OpenRouter，更省事。

### 命令行参数

所有参数均可选，不传则行为与最初版本完全一致（跑默认 `cagr` 场景）。运行
`python demo.py --help` 查看完整中文说明。

| 参数 | 作用 |
|------|------|
| `--list-roles` | **离线自检**：只打印角色花名册 + 内置场景后退出，**无需 API Key** |
| `--scenario {cagr,solar,coding}` | 选内置场景（默认 `cagr`）；`coding` 会路由到 `coding` 角色真正跑代码 |
| `--task "..."` | 自定义任务文本，覆盖 `--scenario` |
| `--role {triage,research,coding,data_analysis,writing}` | 指定**起始角色**（别名 `--starting-role`，默认 `triage`） |
| `--interactive` | **交互式多轮**：复用同一编排器，角色与共享历史跨轮保留 |
| `--model gpt-5.6-luna` | 临时覆盖 `OPENAI_MODEL` |
| `--max-steps 30` | 单条消息的最大 LLM 轮数硬上限（默认 20，防死循环） |

例：

```bash
python demo.py --list-roles            # 离线看角色/场景清单，不调用 API
python demo.py --scenario coding       # 路由到 coding 角色的场景
python demo.py --task "帮我调研并总结…" # 自定义任务
python demo.py --role research         # 从 research 角色起步
python demo.py --interactive           # 交互式多轮，输入 exit 退出
```

三个内置场景（`SCENARIOS`）：`cagr`（默认，新能源汽车销量→CAGR→投资总结）、
`solar`（同类链路换一组光伏装机数据）、`coding`（路由到 `coding` 角色用
`execute_python` 真正跑斐波那契脚本，再由 `writing`/`triage` 收尾）。

## 离线验证

```bash
# 从仓库根目录开始；pytest 需要 dev 依赖。
uv sync --locked --python 3.12 --extra ch10 --extra dev
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1

cd chapter10/multi-role-transfer
python -m pytest tests
python -m pytest tests/test_skill_comparison.py
python demo.py --list-roles
```

`tests/` 包含 `count_characters`、`execute_python` 超时和工具分发错误处理的离线回归测试，无需 API Key。

## 正式 v2 对照证据

权威运行包位于 [`validation/comparison/runs/exp10-1-qwen35flash-20260809-v2/`](validation/comparison/runs/exp10-1-qwen35flash-20260809-v2/)，并由 [`validate_comparison.py`](validate_comparison.py) 独立复核 12/12 门禁。该运行使用 `qwen/qwen3.5-flash-02-23`（OpenRouter），固定 30 个成对任务、温度 0、每单元最多 8 轮，保留 60 条主轨迹和 12 条边界轨迹；Skill 路径在运行时强制先加载 `triage`，再由 Skill 授权专业工具。

在这一模型/configuration 下，Skill 通过 15/30 确定性任务门禁，Transfer 通过 2/30；Skill 的中位未缓存输入多 6,855 token、延迟多 4.368 秒、重算成本多 $0.00044304。异源 Gemini 2.5 Flash Lite 以交换顺序评审 30 对、共 60 次回执（Skill 32、Transfer 20、平局 8）。这是有边界的架构对照结果，不应外推为与模型无关的优胜。

注意：Skill 的固定工具 schema 仍全部可见，以保持前缀稳定；Harness 策略门会拒绝未加载 Skill 或当前 Skill 未授权的工具调用。这样既能测量 Skill 渐进披露，又不会把“看得到工具”误当成“已经加载规程”。

## 路径一演示与历史证据

`demo.py` 抛出一个需要**多次跨领域切换**的复合任务：

> 查中国 2021—2023 三年新能源汽车销量 → 算出年均复合增长率(CAGR) → 写成一段面向投资人的中文总结

预期看到 Agent 自主完成移交链：

```
triage → research → data_analysis → writing
```

- `triage` 判断第一步要查数据，移交 `research`；
- `research` 用 `web_search` 查到三年销量，移交 `data_analysis`；
- `data_analysis` 用 `calculate` 算出 CAGR ≈ 64.22%，移交 `writing`；
- `writing` 综合**此前历史里**的销量数据与 CAGR，直接写出最终成稿。

`writing` 从未自己检索或计算，却能引用准确的销量数字和增长率——
这正是**共享上下文**的证据。运行结束会打印完整移交链、每次移交的 `from→to` 与 `reason`，
以及**各角色分工总览**（谁调用了哪些专属工具、谁产出了最终回复），一眼看清
「同一段历史上不同专业角色各司其职地接力」。

> 注：真实 LLM 输出有随机性，某次运行的具体措辞/步数可能略有不同，但移交机制一致。

### 预期输出形态

以下片段用于说明控制台输出格式。正式验收以
[`validation/runs/exp10-1-kimi-k2.5-tavily-receipts-20260730-v3/manifest.json`](validation/runs/exp10-1-kimi-k2.5-tavily-receipts-20260730-v3/manifest.json)
为准：该次运行记录 Moonshot `kimi-k2.5`、3 次带来源 URL 的真实 Tavily 检索、完整移交链、计算工具调用与
长度核对；9/9 行为门禁和 6/6 溯源门禁全通过。9 份 Moonshot 原始请求/响应均有唯一 response ID 与
usage，3 份 Tavily 原始响应已保留，5 个运行时源码 hash 和 4 个 artifact hash 均复核一致，凭据扫描为零。
旧 v2 JSON 仅作为脱敏汇总型历史运行保留。

```
=== 角色花名册（共 5 个专业角色）===
• triage — 前台分诊（默认入口）
    工具集: ['transfer_to_agent']
    系统提示词(首句): 你是通用助理系统的『前台分诊』角色，也是默认入口。
• research — 信息检索专家
    工具集: ['web_search', 'transfer_to_agent']
    ...（其余角色略，完整列表见上方角色表）

┌── 当前角色: 信息检索专家 (research)  工具: ['web_search', 'transfer_to_agent']
└── 🔧 调用工具 web_search args={'query': '中国 2021年 2022年 2023年 新能源汽车销量 乘联会 中汽协'}
    → 【检索结果·中国乘用车市场信息联席会/中汽协】…2021 年：352.1 万辆 / 2022 年：688.7 万辆 / 2023 年：949.5 万辆
┌── 当前角色: 数据分析专家 (data_analysis)  工具: ['calculate', 'descriptive_stats', 'transfer_to_agent']
└── 🔧 调用工具 calculate args={'expression': '(949.5/352.1)**(1/2)-1'}
    → (949.5/352.1)**(1/2)-1 = 0.6421562289791105

================ 运行汇总 ================
自主移交链: triage → research → data_analysis → writing → triage
移交次数: 4
  1. triage → research  |  reason: 需要先检索中国2021、2022、2023年新能源汽车销量及可靠来源，为后续CAGR计算和投资人摘要提供数据依据。
  2. research → data_analysis  |  reason: 已检索到2021、2022、2023年新能源汽车销量，请计算2021至2023年的两年CAGR，并给出结果供后续写作。
  3. data_analysis → writing  |  reason: 销量数据与CAGR已完成：2021年352.1万辆、2022年688.7万辆、2023年949.5万辆；2021—2023年CAGR=(949.5/352.1)^(1/2)-1=64.22%。请据此写不超过120字的投资人中文总结。
  4. writing → triage  |  reason: 已完成投资人摘要并核对篇幅（101字符，不超过120字）…请做最终收尾确认。

各角色分工（谁用了什么工具、谁产出最终回复）:
  triage        : （仅路由/移交，未用专属工具）  ⇒ 产出最终回复
  research      : web_search
  data_analysis : calculate
  writing       : count_characters

最终成果:
据中汽协公开数据，中国新能源汽车销量由2021年的352.1万辆增至2022年的688.7万辆、2023年的949.5万辆。2021—2023年两年CAGR达64.2%，市场保持高速扩张，成长潜力显著。
```

## 结论解释与局限

- 默认模型为 `gpt-5.6-luna`；移交是否按预期链路发生，很大程度依赖所选模型的指令遵循能力，换模型效果可能不同。
- KV Cache 是否跨请求复用由服务商实现决定。优先记录 API 返回的 `cached_tokens`；若服务商不提供，
  只能把前缀 hash 当机制代理，不能声称已测得缓存节省。
- Skill 路径为了稳定前缀而固定暴露全部工具。Skill 是软行为边界，不是权限边界；删除、付款、发信等
  高风险工具仍必须用 Harness allowlist、审批门或独立沙盒限制。
- `load_skill` 本身增加一次工具往返和轨迹 token。对于很短的单角色任务，这项开销可能大于缓存收益，
  所以数据集不能只选多次切换的长链任务。
- `research` 角色需要可用的 Tavily 凭据。缺少凭据、HTTP 失败或供应商返回空结果都会显式报错，不会用预置事实替代。
- 真实 LLM 输出存在随机性：具体移交步数、每次 `reason` 的措辞、是否途经 `coding` 角色等，不同次运行可能不同，但移交机制本身一致。
- `orchestrator.py` 设有 `max_steps`（默认 20）硬上限，以及「同一 (角色, 工具, 参数) 连续调用 ≥3 次」的纠偏提示，用于防止模型死循环；这是兜底保护，不代表每次运行都会用满这些步数。
