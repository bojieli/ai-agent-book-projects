## English

# Experiment 10-2: Multi-Role Transfer / `transfer_to_agent` (★★)

Companion code for *Deep Understanding of AI Agents*. Demonstrates **chained handoff under shared context**:
a single conversation contains multiple specialized agent roles (each with its own system prompt and dedicated tool set),
and control is **autonomously handed off** between roles via a `transfer_to_agent(target_role, reason)` tool.

## What This Experiment Illustrates

- Unlike 10-1 (a **predefined stage pipeline** for a single software development task), 10-2 emphasizes **cross-domain**,
  **agent-driven judgment** about which specialized role to switch to — not a pre-planned linear flow,
  but dynamic switching based on task progress.
- Because **the same conversation history is shared**, the full history is naturally preserved upon handoff,
  and the new role automatically inherits all prior context (no explicit parameter passing required).
- The core mechanism is **autonomous role handoff**, not the sophistication of the tools themselves,
  so the tools use lightweight real implementations / controllable mocks.

## Architecture

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

5 roles (`roles.py`):

| Role | Description | Dedicated Tool Set |
|------|-------------|-------------------|
| `triage` | Front-desk triage / default entry point, decomposes requests and hands off sequentially, final wrap-up | Only `transfer_to_agent` |
| `research` | Information retrieval | `web_search` (built-in knowledge base mock) |
| `coding` | Programming | `execute_python` (real execution with output capture) |
| `data_analysis` | Data analysis / computation | `calculate`, `descriptive_stats` |
| `writing` | Polishing and writing | `count_characters` |

Each role additionally holds `transfer_to_agent`, enabling autonomous handoff of control to colleagues.

Code structure:

- `tools.py` — Implementation of each role's dedicated tools + OpenAI function-calling schema
- `roles.py` — 5 role definitions (system prompts + tool sets) + `transfer_to_agent` schema
- `orchestrator.py` — Handoff orchestrator (shared history + main loop for swapping system prompts/tool sets, with deadlock prevention and self-handoff rejection)
- `demo.py` — Single-command demo entry point

## How to Run

```bash
pip install -r requirements.txt

# Configure API key (choose one)
export OPENAI_API_KEY=sk-...        # Direct export
# or: cp env.example .env and fill in

python demo.py
```

Configurable environment variables (all have defaults):
`OPENAI_API_KEY`, `OPENAI_BASE_URL` (default `https://api.openai.com/v1`),
`OPENAI_MODEL` (default `gpt-5.6-luna`).

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

Three built-in scenarios (`SCENARIOS`): `cagr` (default, new energy vehicle sales → CAGR → investment summary),
`solar` (same chain with a different set of photovoltaic installation data), `coding` (routes to the `coding` role
to actually run a Fibonacci script via `execute_python`, then `writing`/`triage` wraps up).

## Demo Description

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

### Expected Output Example (from a real run)

The following is a key excerpt from an actual `python demo.py` run (`model=gpt-5.6-luna`, routed via OpenRouter), unedited and unembellished:

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

## Limitations

- The default model is `gpt-5.6-luna`; whether the handoff follows the expected chain depends heavily on the selected model's instruction-following ability. Switching models may yield different results.
- The `research` role's `web_search` is a **built-in knowledge base mock**, not a real web search; it only matches a small set of predefined keywords (new energy vehicle sales, photovoltaic installations, Python GIL). Changing the query may return no results.
- Real LLM output has randomness: the exact number of handoff steps, the wording of each `reason`, whether the `coding` role is visited, etc., may vary between runs, but the handoff mechanism itself is consistent.
- `orchestrator.py` has a hard `max_steps` limit (default 20) and a correction prompt for "same (role, tool, arguments) called ≥3 times consecutively" to prevent model infinite loops; this is a safety net, not an indication that every run will use all these steps.

---

## 中文

# 实验 10-2：多角色转换 / `transfer_to_agent`（★★）

《深入理解 AI Agent》配套代码。演示**共享上下文下的链式移交（handoff）**：
一个会话里存在多个专业角色 Agent（各有独立系统提示词与专属工具集），
通过一个 `transfer_to_agent(target_role, reason)` 工具在角色间**自主移交**控制权。

## 这个实验想说明什么

- 与 10-1（软件开发单任务的**预定义阶段流水线**）不同，10-2 强调**跨领域**、
  由 Agent **自主判断**该切换到哪个专业角色——不是预先规划好的线性流程，
  而是根据任务进展动态切换。
- 因为**共享同一段对话历史**，移交时完整历史天然保留，
  新角色自动继承此前所有内容（无需显式传参）。
- 机制重点是「自主角色移交」，而非工具本身多强，因此工具用轻量真实实现 / 可控 mock。

## 架构

```
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

5 个角色（`roles.py`）：

| 角色 | 说明 | 专属工具集 |
|------|------|-----------|
| `triage` | 前台分诊 / 默认入口，拆解需求并按序移交、最后收尾 | 仅 `transfer_to_agent` |
| `research` | 信息检索 | `web_search`（内置知识库 mock） |
| `coding` | 编程 | `execute_python`（真实执行并捕获输出） |
| `data_analysis` | 数据分析 / 计算 | `calculate`、`descriptive_stats` |
| `writing` | 润色写作 | `count_characters` |

每个角色都额外持有 `transfer_to_agent`，可自主把控制权交给同事。

代码结构：

- `tools.py` —— 各角色专属工具的实现 + OpenAI function-calling schema
- `roles.py` —— 5 个角色定义（系统提示词 + 工具集）+ `transfer_to_agent` schema
- `orchestrator.py` —— 移交编排器（共享历史 + 换系统提示词/工具集的主循环，含防死循环/拒绝自我移交）
- `demo.py` —— 一条命令的演示入口

## 运行方式

```bash
pip install -r requirements.txt

# 配置 key（二选一）
export OPENAI_API_KEY=sk-...        # 直接 export
# 或： cp env.example .env 后填写

python demo.py
```

可配环境变量（均有默认值）：
`OPENAI_API_KEY`、`OPENAI_BASE_URL`（默认 `https://api.openai.com/v1`）、
`OPENAI_MODEL`（默认 `gpt-5.6-luna`）。

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

## 演示说明

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

### 预期输出示例（真实运行截取）

以下是一次 `python demo.py`（`model=gpt-5.6-luna`，经 OpenRouter 路由）真实运行的关键片段，未做任何编造或修饰：

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

## 局限

- 默认模型为 `gpt-5.6-luna`；移交是否按预期链路发生，很大程度依赖所选模型的指令遵循能力，换模型效果可能不同。
- `research` 角色的 `web_search` 是**内置知识库 mock**，并非真实联网检索，仅能命中预置的少量关键词（新能源汽车销量、光伏装机、Python GIL），换查询词可能查不到。
- 真实 LLM 输出存在随机性：具体移交步数、每次 `reason` 的措辞、是否途经 `coding` 角色等，不同次运行可能不同，但移交机制本身一致。
- `orchestrator.py` 设有 `max_steps`（默认 20）硬上限，以及「同一 (角色, 工具, 参数) 连续调用 ≥3 次」的纠偏提示，用于防止模型死循环；这是兜底保护，不代表每次运行都会用满这些步数。
