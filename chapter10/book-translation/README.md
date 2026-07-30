## English

# Experiment 10-3: Book Translation Agent — Orchestration Pattern

Accompanying code demonstrating how to use the **Orchestration Pattern** to delegate long-document translation to multiple specialized agents. The core principles are
**context isolation** and **controlling Manager context growth**: the Manager only stores tasks, plans, agent call records, and file indexes; **complete translations are all written to the file system**, so no matter how long the book is, the Manager's context remains essentially constant.

## Objective

Compare the "single agent translating an entire book in one conversation" approach with the "orchestration pattern multi-agent collaboration" approach, using
**real token counts** to show how the latter controls main/Manager context growth, and using a **shared glossary** to ensure terminology consistency throughout the book.

## Architecture: Four Agents

| Agent | Input (Independent Context) | Output | Context Characteristics |
| --- | --- | --- | --- |
| **Glossary Agent** | Full book content | Structured glossary `glossary.json` | Reads the entire book, context released after output |
| **Translation Agent** | Current chapter + glossary + translation guide | `chapterN_zh.md` | One independent instance per chapter, only sees its own chapter |
| **Proofreading Agent** | All translations + glossary | Proofreading report `proofreading_report.json` | Performs consistency/fluency checks |
| **Manager Agent** | Task + file index + report summary | Scheduling decisions (whether to send back for revision) | **Stores only meta-information, not the full text** |

Data flow: Manager schedules Glossary → chapter-by-chapter Translation (all sharing the same glossary file) → Proofreading → Manager decides based on the report whether to send individual chapters back to Translation for revision. Translations and the glossary are passed through the **file system**; the Manager only saves file paths in its context.

Key design: The Manager forces "house style" terms (e.g., token→词元, prompt→提示词, latency→时延) into the shared glossary, which is then distributed to each Translation Agent, thereby enforcing the specified translations throughout the entire book. A single agent cannot see the glossary and can only use its own default translations.

## Directory

```text
book-translation/
├── agents.py          # Four Agents + two execution modes + token tracking
├── consistency.py     # Terminology consistency / glossary adherence rate (deterministic string matching)
├── demo.py            # One-click demo: runs orchestration mode + single agent comparison, prints comparison table
├── sample_book/       # Bundled short English technical book (4 short chapters, includes terminology and code)
│   ├── chapter1.md ... chapter4.md
├── output/            # Generated at runtime: glossary / chapter translations / proofreading report (gitignored)
├── tests/             # Offline regressions for glossary/proofreading edge cases
├── requirements.txt
└── env.example
```

## Running

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

cd chapter10/book-translation

# Single-project compatibility path, still supported during migration:
# python -m pip install -r requirements.txt

cp env.example .env      # Fill in OPENAI_API_KEY
python demo.py
```

`python demo.py` will first print the **real-time trace of the four-agent collaboration** (Manager creates plan → schedules Glossary → chapter-by-chapter Translation → Proofreading → decides on revisions based on report), then print each agent's token consumption and the core comparison table between orchestration mode and single agent.

- The default model is `gpt-5.6-luna` (currently the cheap flagship), can be overridden with `OPENAI_MODEL`; if you need a custom/proxy endpoint, set `OPENAI_BASE_URL`.
- **Key and universal fallback**: It first tries `OPENAI_API_KEY` to connect directly to OpenAI; if this variable is not set but `OPENROUTER_API_KEY` is, it automatically switches to OpenRouter and maps the model name to its namespace (`gpt-5.6-luna` → `openai/gpt-5.6-luna`). Tip: The `gpt-5.6` series requires organization verification for direct OpenAI access; just setting `OPENROUTER_API_KEY` (without `OPENAI_API_KEY`) will force the use of OpenRouter, which is simpler.
- The task scale is intentionally small (4 short chapters), costing roughly a few hundredths of a US dollar per run.
- Running without any arguments behaves exactly like the old version.

### Command Line Arguments (`python demo.py --help`)

| Argument | Effect | Default |
| --- | --- | --- |
| `--dry-run` | **Offline rehearsal**: Only draws the four-agent collaboration diagram, Manager plan, house style terms, and token budget for each agent; **does not call any API, no Key required** | Off |
| `--sample-dir DIR` | Directory of the book to translate (reads `*.md` files, sorted by filename) | `sample_book/` |
| `--out-dir DIR` | Root directory for output (subdirectories `orchestration/`, `single_agent/` are created within) | `output/` |
| `--source-lang LANG` / `--target-lang LANG` | Source / target language (only affects prompt wording) | `English` / `Chinese` |
| `--no-glossary` | Disable the Glossary Agent (only keeps house style terms) | Enabled |
| `--no-proofreading` | Disable the Proofreading Agent and Manager revision loop | Enabled |
| `--model MODEL` | Temporarily override the model (equivalent to setting `OPENAI_MODEL`) | `gpt-5.6-luna` |
| `--skip-single` | Run only orchestration mode, skip the single agent control group | Off |

> Note: The built-in terminology consistency / adherence rate statistics (`consistency.py`) are calibrated for **English→Chinese**; changing the translation direction will still translate correctly, but the statistics table will be of limited significance.

**No Key / Offline Quick Architecture View**:

```bash
python demo.py --dry-run     # Prints four-agent collaboration diagram + Manager plan + token budget, no network required
```

This mode uses `tiktoken` to estimate the context size each agent will read offline, intuitively confirming that the "Manager context only grows by a few lines of records per chapter, independent of each chapter's text length," while the single agent's cumulative context grows linearly with the book's length.

## Offline Validation

```bash
# From the repository root; include dev tools for pytest.
uv sync --locked --python 3.12 --extra ch10 --extra dev
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1

cd chapter10/book-translation
python -m pytest tests
python demo.py --dry-run
```

`tests/` contains offline regressions for null/malformed glossary and proofreading issue payloads. The tests stub LLM calls and do not require an API key.

## Token Statistics Definitions

- Input and output tokens for sub-agents / single agent are taken from the **real usage** returned by OpenAI.
- "Context peak" = the maximum single-input context (prompt tokens) across all calls for a given agent, used to measure context growth.
- Manager context peak: the peak token count, calculated by `tiktoken`, of the serialized Manager state (task/plan/call records/file index) — it never contains the complete translation text.

## Results (Real Run, gpt-5.6-luna, 4 Chapters)

| Metric | Orchestration Mode | Single Agent |
| --- | --- | --- |
| Main/Manager Context Peak (tokens) | **697** | **2320** |
| Manager LLM Decision Call Context (tokens) | 783 | — |
| Total Pipeline Tokens | 11849 | 6886 |
| Internal Terminology Consistency Rate | 100% | 89% |
| Specified Term Adherence Rate | **100%** | **53%** |
| Number of Agent Types Involved | 4 | 1 |

1. **Controlling Context Growth**: The single agent's main context accumulates with each chapter, peaking at 2320 tokens; in orchestration mode, the Manager's context peaks at only 697 tokens (approximately a 3.3x difference). More importantly, the Manager's context is **essentially independent** of the book's length (it only adds one line of call record/file index), while the single agent's cumulative context grows linearly with the number of chapters — the longer the book, the larger the gap. Sub-agents' contexts are isolated from each other, preventing cross-contamination (each Translation instance peaks at only about 547 tokens).
2. **Terminology Consistency**: The orchestration mode writes house style terms into the shared glossary and enforces them, achieving **100%** adherence for the 4 specified terms across the entire book; the single agent, unable to see the glossary, achieves only **53%** adherence. After switching to the more powerful gpt-5.6-luna, the single agent **spontaneously** adopts some "common sense translations" (token→词元, prompt→提示词 both matched the specified translations), but still acts independently for terms without a single standard (latency was translated as "延迟" throughout the book instead of the specified "时延", embedding as "嵌入" instead of "嵌入向量", with 0/4 and 0/3 adherence respectively). More critically, even the same term **drifts across chapters** for the single agent — token is translated as "词元" in some chapters and left as "token" in others, causing the internal consistency rate to drop to 89%; the orchestration mode, using the shared glossary, eliminates both types of issues (internal consistency 100%, adherence 100%).
3. **Cost**: The orchestration mode uses significantly more tokens (11849 vs 6886, due to additional glossary extraction, proofreading, scheduling calls, and longer outputs from the reasoning model), in exchange for **controllable main context** and **enforceable terminology uniformity** — precisely the properties needed for long-document translation.

> Note: Terminology consistency is measured using deterministic string matching (see `consistency.py`), not model self-evaluation. Specific numbers may fluctuate slightly with each run, but the magnitude and conclusions are stable and reproducible.

## Limitations

- The table above was validated on `gpt-5.6-luna`; switching to a stronger/weaker model will change the gap between the two modes — a stronger single agent is more likely to spontaneously hit some common sense translations (adherence rate rising from nearly 0% for weaker models to 53% in this run), but it still cannot cover terms without a single standard, and cross-chapter drift still occurs; the orchestration mode's shared glossary consistently achieves 100%.
- The sample book is intentionally very small (4 short chapters) to clearly expose the mechanism; it does not represent the absolute token values for a large-scale real book.
- Glossary adherence rate and terminology consistency are both measured using deterministic string matching (`consistency.py`), not model self-evaluation, which may miss more flexible translation variants.
- Specific numbers for each run may fluctuate slightly due to the randomness of model output (the table above is from the most recent real run), but the magnitude and conclusions are stable and reproducible.

---

## 中文

# 实验 10-3：书籍翻译 Agent —— 管理者模式（Orchestration）

配套代码，演示如何用**管理者模式**把长文档翻译拆给多个专职 Agent。核心是
**上下文隔离**与**控制 Manager 上下文膨胀**：Manager 只保存任务、计划、各
Agent 调用记录和文件索引，**完整译文全部落盘到文件系统**，因此无论书有多长，
Manager 的上下文都基本恒定。

## 目的

对比「单 Agent 一条对话翻完整本书」与「管理者模式多 Agent 协作」两种方案，用
**真实 token 数**说明后者如何控制主/Manager 上下文膨胀，并用**共享术语表**保证
全书术语一致。

## 架构：四种 Agent

| Agent | 输入（独立上下文） | 产出 | 上下文特点 |
| --- | --- | --- | --- |
| **Glossary Agent** | 全书内容 | 结构化术语表 `glossary.json` | 读全书，产出后即释放 |
| **Translation Agent** | 当前章节 + 术语表 + 翻译指南 | `chapterN_zh.md` | 每章一个独立实例，只看到自己这一章 |
| **Proofreading Agent** | 所有译文 + 术语表 | 审校报告 `proofreading_report.json` | 做一致性 / 流畅性检查 |
| **Manager Agent** | 任务 + 文件索引 + 报告摘要 | 调度决策（是否发回修订） | **只存元信息，不存正文** |

数据流：Manager 调度 Glossary → 逐章 Translation（共享同一份术语表文件）→
Proofreading → Manager 依据报告决定是否把个别章节发回 Translation 修订。译文与
术语表都通过**文件系统**传递，Manager 只在上下文里保存文件路径。

关键设计：Manager 把「编辑部指定术语」（house style，如 token→词元、
prompt→提示词、latency→时延）强制写入共享术语表，下发给每个 Translation Agent，
从而把指定译法贯彻到全书。单 Agent 看不到术语表，只能用自己的默认译法。

## 目录

```
book-translation/
├── agents.py          # 四种 Agent + 两种运行方式 + token 追踪
├── consistency.py     # 术语一致性 / 术语表遵从率（确定性字符串匹配）
├── demo.py            # 一键演示：跑管理者模式 + 单 Agent 对照，打印对比表
├── sample_book/       # 自带英文技术小书（4 个短章节，含术语与代码）
│   ├── chapter1.md ... chapter4.md
├── output/            # 运行时生成：术语表 / 各章译文 / 审校报告（已 gitignore）
├── tests/             # 术语表 / 审校边界情况的离线回归测试
├── requirements.txt
└── env.example
```

## 运行

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

cd chapter10/book-translation

# 迁移期间仍支持单项目兼容路径：
# python -m pip install -r requirements.txt

cp env.example .env      # 填入 OPENAI_API_KEY
python demo.py
```

上面的四章小书只用于低成本入门，不是正文实验的正式验收对象。完整验收入口改用本仓库英文版技术书的第 1–2 章：它包含 242,090 字节正文、23 个真实插图引用和 14 个围栏代码块。runner 在 Markdown 安全边界把长章拆成有界翻译单元，分别调用 Agent 后再重组为完整章节；源码字节、图像目标、链接和代码块都会独立校验，不能用短摘要冒充翻译。

```bash
python run_official_experiment.py \
  --provider ark \
  --model doubao-seed-1-6-flash-250615
```

正式运行同时执行四角色管理者组和一条持续增长对话的单 Agent 组，保存每次真实 API 的 provider/model、输入/输出 token 与时延，并比较：完整 Markdown/代码保真度、术语一致性和指定译法遵从率、逐单元匿名质量评分、墙钟时间、总 token、Manager 与单 Agent 上下文峰值。产物写入 `validation/real_<UTC>/evidence.json`，`validation/latest.json` 只在所有执行门满足后标记 `complete`。管理者组是否胜出是实验结果，不是完成状态的先验条件。

### 2026-07-30 正式实跑结果

[v4 完整证据](validation/real_20260730T061500Z_v4/evidence.json)在英文版第 1–2 章上完成了 26 个 Markdown 安全翻译单元：242,090 字节、1,598 行、23 个插图引用、14 个围栏代码块。翻译组使用真实 ARK `doubao-seed-1-6-flash-250615`，匿名位置平衡裁判使用真实 ARK `doubao-seed-1-6-250615`；二者均显式关闭 thinking。12/12 执行与溯源门禁通过，[latest 指针](validation/latest.json)的证据 SHA-256 为 `9e765aa3d9b194346e1b9b5398018b99c369c2f8c79df231a433cc9e89ab1b5e`。

| 实测指标 | 四角色管理者组 | 单 Agent 组 |
| --- | ---: | ---: |
| 翻译 API 调用 | 29 | 26 |
| 翻译总 token | 203,277 | 1,317,808 |
| 主上下文峰值 | 4,618 | 94,355 |
| 翻译墙钟时间 | 270.829 秒 | 254.127 秒 |
| 匿名质量均分（5 分制） | 4.654 | 4.481 |
| 裁判偏好单元数 | 15 | 11 |
| 编辑部指定译法遵从率 | 75% | 0% |
| 确定性字符串术语一致率 | 50% | 87.5% |

这次结果支持“上下文隔离”而不是无条件支持“多 Agent 全面更优”：Manager 主上下文缩小 20.43 倍，翻译 token 减少 6.48 倍，匿名质量略高，但墙钟时间反而慢 6.57%。共享术语表显著提高指定译法遵从率，却没有保证更高的宽泛字符串一致率；`embedding` 也没有遵守指定的“嵌入向量”。结构保真同样出现真实负结果：两组都保留了代码块和插图的数量，却都改动了代码 payload 并增加了标题；管理者组还改动了插图目标，而单 Agent 组的插图目标序列保持不变。这里的 ✅ 表示完整对照与所有预注册测量已经执行，不表示每项质量假设都成立。

裁判阶段共有 39 次带完整原始请求/响应 ID/usage/时延的回执，另有一次在回执机制加入前发生的已声明格式失败；14 个带回执响应未通过严格 schema，8 个仅把偏好字段重复嵌套的响应做了有标记的无损本地归一化，另一次通过独立的格式修复 API 调用展平，未重新评分。26 份回执、三个 checkpoint、四份重组译文、三个当前验收源码和负溯源标记共 37 个声明 hash 均已重算一致。

`python demo.py` 会先打印**四 Agent 协作的实时轨迹**（Manager 制定计划 → 调度
Glossary → 逐章 Translation → Proofreading → 依报告决定修订），再打印各 Agent 的
token 消耗与管理者模式 vs 单 Agent 的核心对比表。

- 模型默认 `gpt-5.6-luna`（当前便宜旗舰），可用 `OPENAI_MODEL` 覆盖；如需自建/代理端点，设 `OPENAI_BASE_URL`。
- **Key 与通用回退**：优先用 `OPENAI_API_KEY` 直连 OpenAI；若未设置该变量但设了
  `OPENROUTER_API_KEY`，则自动改走 OpenRouter，并把模型名映射到其命名空间
  （`gpt-5.6-luna` → `openai/gpt-5.6-luna`）。提示：`gpt-5.6` 系列直连 OpenAI 需组织验证，
  只填 `OPENROUTER_API_KEY`（不填 `OPENAI_API_KEY`）即可强制走 OpenRouter，更省事。
- `demo.py` 的任务规模刻意很小（4 个短章节），只用于教学预演；正式验收必须运行上述真实书籍 campaign。
- 不带任何参数运行与旧版行为完全一致。

### 命令行参数（`python demo.py --help`）

| 参数 | 作用 | 默认 |
| --- | --- | --- |
| `--dry-run` | **离线预演**：只画四 Agent 协作图、Manager 计划、编辑部术语与各 Agent 的 token 预算，**不调用任何 API、无需 Key** | 关闭 |
| `--sample-dir DIR` | 待翻译书籍目录（读取其中 `*.md`，按文件名排序） | `sample_book/` |
| `--out-dir DIR` | 产物根目录（其下再分 `orchestration/`、`single_agent/`） | `output/` |
| `--source-lang LANG` / `--target-lang LANG` | 源 / 目标语言（仅影响提示词措辞） | `英文` / `中文` |
| `--no-glossary` | 关闭 Glossary Agent（仅保留编辑部指定术语） | 启用 |
| `--no-proofreading` | 关闭 Proofreading Agent 与 Manager 修订闭环 | 启用 |
| `--model MODEL` | 临时覆盖模型（等价于设 `OPENAI_MODEL`） | `gpt-5.6-luna` |
| `--skip-single` | 只跑管理者模式，跳过单 Agent 对照组 | 关闭 |

> 注意：内置的术语一致性 / 遵从率统计（`consistency.py`）针对 **英文→中文** 调校；
> 改翻译方向仍可正常翻译，但该统计表意义有限。

**无 Key / 离线快速查看架构**：

```bash
python demo.py --dry-run     # 打印四 Agent 协作图 + Manager 计划 + token 预算，不联网
```

该模式用 `tiktoken` 离线估算各 Agent 会读到的上下文规模，直观印证「Manager 上下文
只随章节数加几行记录、与每章正文长度无关」，而单 Agent 的累积上下文随书长线性膨胀。

## 离线验证

```bash
# 从仓库根目录开始；pytest 需要 dev 依赖。
uv sync --locked --python 3.12 --extra ch10 --extra dev
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1

cd chapter10/book-translation
python -m pytest tests
python demo.py --dry-run
```

`tests/` 包含 `glossary` 与审校报告的空值 / 非法结构回归测试。测试会打桩 LLM 调用，无需 API Key。

## token 统计口径

- 子 Agent / 单 Agent 的输入、输出 token 取 OpenAI 返回的**真实 usage**。
- 「上下文峰值」= 某 Agent 所有调用中，单次输入上下文（prompt tokens）的最大值，
  用来衡量上下文膨胀。
- Manager 上下文峰值：Manager 状态（任务/计划/调用记录/文件索引）序列化后用
  `tiktoken` 统计的 token 数峰值 —— 它从不包含完整译文。

## 结论（真实运行结果，gpt-5.6-luna，4 章）

| 指标 | 管理者模式 | 单 Agent |
| --- | --- | --- |
| 主/Manager 上下文峰值 (tokens) | **697** | **2320** |
| Manager LLM 决策调用上下文 (tokens) | 783 | — |
| 全流程总 token | 11849 | 6886 |
| 术语内部一致率 | 100% | 89% |
| 指定术语遵从率 | **100%** | **53%** |
| 参与 Agent 种类数 | 4 | 1 |

1. **控制上下文膨胀**：单 Agent 的主上下文随章节累积，峰值达 2320 tokens；管理者
   模式下 Manager 上下文峰值仅 697 tokens（约 3.3 倍差距）。更重要的是，Manager
   上下文与书的长度**基本无关**（只加一行调用记录/文件索引），而单 Agent 的累积
   上下文会随章节线性增长——书越长，差距越大。子 Agent 的上下文各自隔离、互不污染
   （每个 Translation 实例峰值仅约 547 tokens）。
2. **术语一致性**：管理者模式把编辑部指定术语写入共享术语表并强制下发，4 个指定
   术语在全书的遵从率 **100%**；单 Agent 看不到术语表，遵从率仅 **53%**。换用更强
   的 gpt-5.6-luna 后，单 Agent 会**自发**采用部分「常识译法」（token→词元、
   prompt→提示词都命中了指定译法），但对没有唯一标准的术语仍各行其是（latency 全书
   译成「延迟」而非规定的「时延」，embedding 译成「嵌入」而非「嵌入向量」，各 0/4、
   0/3 遵从）。更关键的是，单 Agent 即便同一个术语也会**跨章漂移**——token 在部分章
   译成「词元」、另一些章直接留「token」，术语内部一致率因此掉到 89%；管理者模式靠
   共享术语表把这两类问题一起消除（内部一致率 100%、遵从率 100%）。
3. **代价**：管理者模式花了明显更多 token（11849 vs 6886，额外的术语表抽取、审校、
   调度调用，且推理模型输出更长），换来的是**主上下文可控**与**术语可强制统一**——
   这正是长文档翻译真正需要的性质。

> 说明：术语一致性用确定性字符串匹配统计（见 `consistency.py`），不是让模型自评。
> 具体数字每次运行会有小幅波动，但上述量级与结论稳定复现。

## 局限

- 上表在 `gpt-5.6-luna` 上验证；换更强/更弱的模型，两种模式的差距会变化——越强的
  单 Agent 越容易自发命中部分常识译法（遵从率从更弱模型的近 0% 升到本次的 53%），
  但仍无法覆盖没有唯一标准的术语，也仍会跨章漂移，管理者模式的共享术语表始终 100%。
- 样例书刻意做得很小（4 个短章节），目的是清晰暴露机制，不代表大规模真实书籍的
  绝对 token 数值。
- 术语表遵从率、术语一致性都用确定性字符串匹配（`consistency.py`），不是模型自评，
  可能漏判措辞更灵活的译法变体。
- 每次运行的具体数字会因模型输出的随机性小幅波动（上表为最近一次真实运行结果），
  但量级与结论稳定复现。
