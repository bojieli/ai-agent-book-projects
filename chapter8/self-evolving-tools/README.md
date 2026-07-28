## English

# Supplementary Case: Agent Finds and Validates Tools from the Web (Alita Style)

> Companion code for "Deep Understanding of AI Agents" · ★★★
> Core concept: **"Minimum predefined, maximum self-evolution"**.

## Purpose

The capability ceiling of most agents is determined by "human-predefined tools". This experiment takes the opposite approach: the agent **has no domain-specific tools predefined**, only five generic "meta-tools". When it encounters a task it cannot handle, it will search the web for **open-source libraries/APIs**, **read documentation**, **test in a sandbox**, **package the viable solution as a new tool and store it in the tool library**, and then use the new tool to complete the task—evolving like Alita. When encountering a similar task again, it will first **reuse** the already-built tool from the library instead of reinventing the wheel.

The entire process emphasizes **hallucination control**: all numbers and conclusions must come from real search results, documentation, or code execution output.

## Five Base Tools (No Domain-Specific Tools)

| Tool | Purpose | Implementation |
| --- | --- | --- |
| `web_search` | Search for open-source libraries / APIs | DuckDuckGo, **no API key required** (lite + html dual endpoints, with backoff retry) |
| `read_webpage` | Read README / API documentation | requests + BeautifulSoup to extract main text |
| `code_interpreter` | Actually execute code in a sandbox to verify the solution | **Subprocess sandbox** + timeout; can `pip_install` to a temporary directory |
| `create_tool` | Package a verified function as a standard tool and persist it | Write to `tool_library/<name>.json` (metadata + code) |
| `search_tools` | Search the tool library by name/description for **reuse** | Keyword matching |

## Self-Evolution Pipeline

```text
Analyze task
  → search_tools (first check if a reusable tool already exists in the library)
      Hit ─────────────────► Directly call that tool to answer (tool reuse)
      Miss ↓
  → web_search  find open-source Python libraries requiring no API key
  → read_webpage read README / PyPI documentation
  → code_interpreter actually run in sandbox, print real data (can pip install dependencies)
  → create_tool package as a "generic, parameterized" standard tool
      └─ Pre-save validation: syntax compilation + actually run run() once with test_args, only register if it passes
  → Call the new tool, answer with real data
```

To suppress hallucinations and "laziness", several **guardrails** are built into the code:

- Without `code_interpreter` printing real data, `create_tool` is **prohibited**;
- If the code for `create_tool` contains words like `mock / simulated / sample data / fake`, it is **rejected** from the library;
- When real data has been verified but the agent tries to skip packaging and answer directly, it is forced to `create_tool` first;
- A tool in the library must first be hit by `search_tools` (or just created) to be "unlocked" as callable—thus enforcing the "retrieve before reuse" flow.

There is also a **"pre-save validation" gate** (corresponding to the "Test" step in the pipeline of Figure 8-7, and also addressing the chapter's warning about "tool quality degradation"—bad tools propagate errors to subsequent tasks through reuse): before `create_tool` persists the tool to disk, it will

- First perform a **syntax compilation check**; code with syntax errors is blocked from the library;
- If the caller provides `test_args` (a set of example input parameters), it will **actually run `run(**test_args)` once** in the sandbox; only if it successfully returns a result is it allowed into the library. The system prompt requires the model to provide `test_args` when creating a tool, thus keeping "broken tools that don't run" out of the tool library, rather than waiting for them to crash when reused by a subsequent task.

## Running

```bash
pip install -r requirements.txt
cp env.example .env        # Fill in OPENAI_API_KEY (default model gpt-5.6-luna)
# Fallback: if no OPENAI_API_KEY but OPENROUTER_API_KEY is set, automatically switch to OpenRouter (maps to openai/gpt-5.6-luna, etc.)
python demo.py             # Run the two default "evolution + reuse" tasks (requires API + internet)
python demo.py --fresh     # Clear tool_library/ first, then run, reproducing "evolution from scratch" (recommended for repeated demos)
python demo.py --offline   # Offline mechanism self-check: no API/network required, verify the evolution loop itself
python demo.py --help      # View all parameters
```

**Command-line arguments** (Chinese `--help`):

| Argument | Purpose |
| --- | --- |
| `--task task description` | Custom task; can be repeated multiple times to run several tasks in sequence. If not given, runs the default NVDA/AAPL two tasks |
| `--offline` | Offline mechanism self-check: does not call LLM/network, directly drives the "search miss → create tool → pre-save validation → register → reuse" loop |
| `--fresh` | Clears `tool_library/` before running, reproducing "evolution from scratch" |
| `--no-create` | Disables the ability to create tools (removes `create_tool`), used for comparison demos showing "without evolution ability, can only reuse/cannot complete" |
| `--model model name` | Override the LLM model name (higher priority than the `LLM_MODEL` environment variable) |
| `--output path` | Write tasks, answers, action traces, and reuse conclusions to this JSON file |

> The tool library is **persisted** to `tool_library/`. If `get_stock_price` was already packaged in a previous run, running again directly will have task one hit `search_tools` and reuse it at step 0, so you won't see the full "evolution" process; add `--fresh` to reproduce evolution.

**Without an API key / no internet access**, use `python demo.py --offline` for a mechanism self-check—it uses a purely offline, deterministic tool (calculating the number of days between two dates) to run through the complete loop: task one `search_tools` miss → `create_tool` (with pre-save validation) → register → call; task two `search_tools` hit → **direct reuse**, no reinventing the wheel; and additionally demonstrates that the pre-save validation gate will reject a "broken tool that doesn't run" from entering the library. The self-check runs in a temporary directory and **will not pollute** your real `tool_library/`. A real offline run output:

```text
[Validation Gate] Attempting to register a broken tool that will crash (with test_args)...
  Result: success=False  ->  Tool registration pre-validation failed: run(**test_args) did not return successfully...
  ✅ Pre-save validation blocked the broken tool (not stored), consistent with 'Don't save bad programs'.
[step 1] search_tools -> 0 hits (tool library empty, no hit)
[step 2] create_tool(days_between) -> success=True validated=True (pre-save validation actually ran run() once)
[step 3] days_between(...) -> {'start': '2020-01-01', 'end': '2020-03-01', 'days': 60}
[step 1] search_tools -> 1 hit: ['days_between'] (reuse!)
[step 2] days_between(...) -> {'start': '2021-01-01', 'end': '2021-12-31', 'days': 364}
Task one trace: ['search_tools', 'create_tool', 'days_between']
Task two trace: ['search_tools', 'days_between']
Did task two reuse the tool created by task one (did not re-create_tool): Yes ✅
Did the pre-save validation gate block the broken tool: Yes ✅
```

`demo.py` will run two tasks consecutively:

1. **NVDA** (demonstrates evolution): Starting from zero base tools, search → read documentation → sandbox test → package `get_stock_price` tool → provide NVIDIA's real stock price and weekly change.
2. **AAPL** (demonstrates reuse): `search_tools` hits the just-created `get_stock_price`, **directly reuses** it, no re-searching/creating.

> You can also switch to other OpenAI-compatible providers: `LLM_PROVIDER=moonshot|ark` (with corresponding `MOONSHOT_API_KEY` / `ARK_API_KEY`), or use `LLM_MODEL` to override the model name. Search uses DuckDuckGo, no search key required.

## A Real Run Trace (Excerpt, Real Internet + Real OpenAI Calls)

**Task One · NVDA** (Self-Evolution, Note Error Recovery):

```text
[step 1] search_tools("stock price")      -> 0 hits (tool library empty)
[step 2] web_search("open source python library stock price") -> yfinance · PyPI ...
[step 3] read_webpage(pypi.org/project/yfinance) / github.com/ranaroussi/yfinance
[step 4] code_interpreter(...)  -> stdout empty, note: "No real data printed, not considered verification passed"
[step 5] code_interpreter(...)  -> "Latest stock price: 205.91..., Change: 1.54"   ← Real data, verification passed
[step 6] create_tool("get_stock_price", parameterized ticker/period, internally calls yfinance)
[step 7] get_stock_price(ticker="NVDA") -> {latest_price: 205.71, change_percentage: 1.44}
[Final Answer] NVIDIA (NVDA) latest stock price $205.71, +1.44% compared to one week ago. Data source: yfinance.
```

**Task Two · AAPL** (Tool Reuse, No Re-Searching/Creating):

```text
[step 1] search_tools("stock price")  -> hit get_stock_price (reuse!)
[step 2] get_stock_price(ticker="AAPL") -> {latest_price: 330.48, change_percentage: 4.51}
[Final Answer] Apple (AAPL) latest stock price $330.48, +4.51% compared to one week ago.
Task two trace = ['search_tools', 'get_stock_price']  → No web_search / create_tool ✅ Reuse confirmed
```

(Numbers change in real-time with market data, different each run; above is the result of one real run.)

## Conclusion

- Starting from **zero domain tools**, with only five meta-tools, the agent autonomously discovered `yfinance`, packaged a generic `get_stock_price` tool, and provided **real** stock prices and changes.
- The second task **hit and reused** the already-built tool via `search_tools`, without re-searching/reinventing—the tool library makes the agent "stronger with use".
- Empty output reminder + anti-mock guard + "verify before package" effectively **suppressed hallucinations**: in one successful run, the model's first test code forgot to `print`, was reminded by the note, self-corrected, and ultimately answered based on real execution results.

## Regarding Task One in the Book (YouTube Subtitles)

The book's "Task One: YouTube subtitle understanding, answer 100000000" depends on `youtube-transcript-api` + a specific video. Internet connectivity, access controls, or video takedowns can cause instability, so this repository **uses a reliably reproducible real-time financial task to actually verify the mechanism**.
To reproduce the YouTube scenario, the same pipeline applies: let the agent `web_search` find `youtube-transcript-api` → read documentation → sandbox test → `create_tool` to package a subtitle fetching tool.

## ⚠️ Security Boundary Reminder (Must Read)

This experiment **executes model-generated code** and **installs third-party packages from the network**, which inherently carries risks:

- **Supply chain risk**: `code_interpreter` will `pip install` the package selected by the model. In real/production environments, package sources must have **whitelisting/auditing/pinned versions and hashes** to guard against typosquatting and malicious packages.
- **Code execution isolation**: The sandbox here is only **demonstration-grade** (subprocess isolation + timeout), **not a security sandbox**. Production environments should use containers / gVisor / seccomp / network-namespace isolation / read-only filesystems / resource limits for strong isolation, and ideally disable networking or only allow whitelisted domains.
- **Self-evolving tool library requires human review**: Tools persisted by `create_tool` will be reused by subsequent tasks, effectively turning "model-written code" into a permanent capability. It is recommended to perform manual/automated review of tools entering the library, and record sources and audit logs.
- This directory by default includes `tool_library/*.json` and `.sandbox_packages/` in `.gitignore` (runtime artifacts).

---

## 中文

# 补充案例：Agent 从网络寻找并验证工具（Alita 式）

> 《深入理解 AI Agent》配套代码 · ★★★
> 核心理念：**「最小预定义，最大自我进化」**。

## 目的

大多数 Agent 的能力上限由「人类预先写好的工具」决定。本实验反其道而行之：Agent **不预置任何领域工具**，
只有五个通用的「元工具」。当它遇到自己不会做的任务时，会自己上网**寻找开源库 / API**、**阅读文档**、
**在沙箱里测试**、把可行方案**封装成新工具存入工具库**，然后用新工具完成任务——像 Alita 一样自我进化。
再次遇到同类任务时，它会先在工具库里**复用**已造好的工具，而不是重新造轮子。

全程强调**幻觉控制**：所有数字与结论必须来自真实的搜索结果、文档或代码执行输出。

## 五个基础工具（没有任何领域工具）

| 工具 | 作用 | 实现 |
| --- | --- | --- |
| `web_search` | 搜索开源库 / API | DuckDuckGo，**无需 key**（lite + html 双端点，带退避重试） |
| `read_webpage` | 阅读 README / API 文档 | requests + BeautifulSoup 抽取正文 |
| `code_interpreter` | 沙箱里真实执行代码验证方案 | **子进程沙箱** + 超时；可 `pip_install` 到临时目录 |
| `create_tool` | 把验证过的功能封装为标准工具并持久化 | 写入 `tool_library/<name>.json`（元数据 + 代码） |
| `search_tools` | 从工具库按名称/描述检索，用于**复用** | 关键词匹配 |

## 自我进化流水线

```text
分析任务
  → search_tools（先查工具库是否已有可复用工具）
      命中 ─────────────────► 直接调用该工具作答（工具复用）
      未命中 ↓
  → web_search  找无需 key 的开源 Python 库
  → read_webpage 读 README / PyPI 文档
  → code_interpreter 在沙箱里真跑，print 出真实数据（可 pip 安装依赖）
  → create_tool 封装为「通用、参数化」的标准工具
      └─ 存前验证：语法编译 + 用 test_args 真跑一次 run()，通过才注册入库
  → 调用新工具，用真实数据作答
```

为抑制幻觉与「偷懒」，代码里内置了几道**守卫**：

- 未用 `code_interpreter` 打印出真实数据前，**禁止** `create_tool`；
- `create_tool` 的代码若含 `mock / 模拟 / 示例数据 / fake` 等字样，**拒绝**入库；
- 已验证真实数据却想跳过封装直接作答时，强制提醒先 `create_tool`；
- 工具库里的工具需先经 `search_tools` 命中（或刚创建）才「解锁」为可调用——从而强制「先检索复用」的流程。

还有一道**「存前验证」闸门**（对应图 8-7 流水线里的「测试」一步，也回应本章「工具质量退化」的告诫——
坏工具会通过复用把错误传播到后续任务）：`create_tool` 在把工具落盘之前会

- 先做**语法编译检查**，语法有误的代码一律挡在库外；
- 若调用方给了 `test_args`（一组示例入参），就在沙箱里**真跑一次 `run(**test_args)`**，
  只有成功返回结果才准入库。系统提示词要求模型造工具时一并给出 `test_args`，从而把
  「跑不通的坏工具」挡在工具库门外，而不是等它被后续任务复用时才崩。

## 运行

```bash
pip install -r requirements.txt
cp env.example .env        # 填入 OPENAI_API_KEY（默认模型 gpt-5.6-luna）
# 兜底：若无 OPENAI_API_KEY 但设置了 OPENROUTER_API_KEY，自动改走 OpenRouter（映射到 openai/gpt-5.6-luna 等）
python demo.py             # 跑「进化 + 复用」两个默认任务（需 API + 联网）
python demo.py --fresh     # 先清空 tool_library/ 再跑，重现「从零进化」（重复演示时推荐）
python demo.py --offline   # 离线机制自检：无需 API/网络，验证进化闭环本身
python demo.py --help      # 查看全部参数
```

**命令行参数**（Chinese `--help`）：

| 参数 | 作用 |
| --- | --- |
| `--task 任务描述` | 自定义任务；可重复多次以按顺序运行多个任务。不给则跑默认的 NVDA/AAPL 两任务 |
| `--offline` | 离线机制自检：不调用 LLM/网络，直接驱动「搜索未命中→造工具→存前验证→注册→复用」闭环 |
| `--fresh` | 运行前清空 `tool_library/`，重现「从零进化」 |
| `--no-create` | 禁用造工具能力（移除 `create_tool`），用于对照演示「没有进化能力时只能复用/无法完成」 |
| `--model 模型名` | 覆盖 LLM 模型名（优先级高于 `LLM_MODEL` 环境变量） |
| `--output 路径` | 把任务、答案、动作轨迹与复用结论写入该 JSON 文件 |

> 工具库会**持久化**到 `tool_library/`。若上一轮已封装出 `get_stock_price`，再次直接运行时任务一会在第 0 步
> 就 `search_tools` 命中并复用它，从而看不到"进化"全过程；想重现进化请加 `--fresh`。

**无 API key / 无法联网时**，用 `python demo.py --offline` 做机制自检——它用一个纯离线、确定性的工具
（计算两个日期相差的天数）跑通完整闭环：任务一 `search_tools` 未命中→`create_tool`（含存前验证）→注册→调用；
任务二 `search_tools` 命中→**直接复用**，不再造轮子；并额外演示存前验证闸门会拒绝一个「跑不通的坏工具」入库。
自检在临时目录里进行，**不会污染**你真实的 `tool_library/`。一次真实的离线运行输出：

```text
[验证闸门] 尝试注册一个运行会崩溃的坏工具（附 test_args）...
  结果: success=False  ->  工具注册前验证失败：run(**test_args) 没有成功返回...
  ✅ 存前验证挡住了坏工具（未入库），符合『别把坏程序存进去』。
[step 1] search_tools -> 命中 0 个（工具库为空，未命中）
[step 2] create_tool(days_between) -> success=True validated=True（存前验证已真跑一次 run()）
[step 3] days_between(...) -> {'start': '2020-01-01', 'end': '2020-03-01', 'days': 60}
[step 1] search_tools -> 命中 1 个：['days_between']（复用！）
[step 2] days_between(...) -> {'start': '2021-01-01', 'end': '2021-12-31', 'days': 364}
任务一轨迹: ['search_tools', 'create_tool', 'days_between']
任务二轨迹: ['search_tools', 'days_between']
任务二是否复用了任务一造的工具(未重新 create_tool): 是 ✅
存前验证闸门是否挡住了坏工具: 是 ✅
```

`demo.py` 会连续跑两个任务：

1. **NVDA**（演示进化）：从零基础工具出发，搜索→读文档→沙箱测试→封装 `get_stock_price` 工具→给出 NVIDIA 真实股价与周涨跌幅。
2. **AAPL**（演示复用）：`search_tools` 命中刚创建的 `get_stock_price`，**直接复用**，不再重新搜索/创建。

> 也可切换到其它 OpenAI 兼容供应商：`LLM_PROVIDER=moonshot|ark`（配合对应的 `MOONSHOT_API_KEY` / `ARK_API_KEY`），
> 或用 `LLM_MODEL` 覆盖模型名。搜索用 DuckDuckGo，不需要任何搜索 key。

## 一次真实运行的轨迹（节选，真实联网 + 真实调用 OpenAI）

**任务一 · NVDA**（自我进化，注意错误恢复）：

```text
[step 1] search_tools("stock price")      -> 命中 0 个（工具库为空）
[step 2] web_search("open source python library stock price") -> yfinance · PyPI ...
[step 3] read_webpage(pypi.org/project/yfinance) / github.com/ranaroussi/yfinance
[step 4] code_interpreter(...)  -> stdout 为空，note: “没有 print 出真实数据，不算验证通过”
[step 5] code_interpreter(...)  -> "最新股价: 205.91..., 涨跌幅: 1.54"   ← 真实数据，验证通过
[step 6] create_tool("get_stock_price", 参数化 ticker/period, 内部真调 yfinance)
[step 7] get_stock_price(ticker="NVDA") -> {latest_price: 205.71, change_percentage: 1.44}
[最终回答] NVIDIA(NVDA) 最新股价 205.71 美元，与一周前相比 +1.44%。数据来源 yfinance。
```

**任务二 · AAPL**（工具复用，未重新搜索/创建）：

```text
[step 1] search_tools("stock price")  -> 命中 get_stock_price（复用！）
[step 2] get_stock_price(ticker="AAPL") -> {latest_price: 330.48, change_percentage: 4.51}
[最终回答] Apple(AAPL) 最新股价 330.48 美元，与一周前相比 +4.51%。
任务二轨迹 = ['search_tools', 'get_stock_price']  → 没有 web_search / create_tool ✅ 复用成立
```

（数字随行情实时变化，每次运行不同；上面是某次真实运行的结果。）

## 结论

- Agent 从**零领域工具**出发，仅凭五个元工具，就自主发现了 `yfinance`、封装出通用 `get_stock_price` 工具，并给出**真实**股价与涨跌幅。
- 第二个任务通过 `search_tools` **命中并复用**了已造好的工具，未重复搜索/造轮子——工具库让 Agent「越用越强」。
- 空输出提醒 + 反 mock 守卫 + 「先验证再封装」有效**抑制了幻觉**：一次跑通中，模型第一次测试代码忘了 `print`，被 note 提醒后自行修正，最终基于真实执行结果作答。

## 关于书中任务一（YouTube 字幕）

书中「任务一：YouTube 字幕理解，答案 100000000」依赖 `youtube-transcript-api` + 特定视频，联网/风控/视频下架都可能导致不稳定，故本仓库**用可稳定复现的实时金融任务来实际验证机制**。
若要复现 YouTube 场景，同一套流水线适用：让 Agent `web_search` 找到 `youtube-transcript-api` → 读文档 → 沙箱测试 → `create_tool` 封装字幕抓取工具即可。

## ⚠️ 安全边界提醒（务必阅读）

本实验会**执行模型生成的代码**并**从网络安装第三方包**，天然带有风险：

- **供应链风险**：`code_interpreter` 会 `pip install` 模型选中的包。真实/生产环境必须对包来源做**白名单/审计/固定版本与哈希**，谨防拼写抢注（typosquatting）与恶意包。
- **代码执行隔离**：这里的沙箱仅为**演示级**（子进程隔离 + 超时），**不是安全沙箱**。生产环境应使用容器 / gVisor / seccomp / 无网络命名空间 / 只读文件系统 / 资源限额等强隔离，并最好断网或仅放通白名单域名。
- **自进化工具库需人审**：`create_tool` 落盘的工具会被后续任务反复复用，等于把「模型写的代码」变成常驻能力。建议对入库工具做人工/自动审查，并记录来源与审计日志。
- 本目录默认把 `tool_library/*.json` 与 `.sandbox_packages/` 纳入 `.gitignore`（运行时产物）。
