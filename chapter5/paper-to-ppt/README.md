# Experiment 5-4: Paper → PPT (Proposer–Reviewer) / 实验 5-4：基于论文的 PPT 自动生成（提议者-审核者机制）

> Companion lab for *AI Agents in Depth*, Chapter 5 — generate Slidev decks from a paper; Proposer writes code, Reviewer renders PNG and reviews with Vision LLM.  
> 《深入理解 AI Agent》第 5 章：把「做 PPT」重构为代码生成；Proposer 写 Slidev，Reviewer 真渲染 PNG 并用 Vision 审查迭代。

← [Chapter 5 index / 返回第 5 章目录](../README.md)

---

## English

### One-line takeaway

Proposer only writes Slidev code; Reviewer **renders each page to PNG** and uses a **Vision LLM** to flag issues (text overflow / overcrowding / image size). Proposer revises from structured feedback. Versus single-agent self-review (stacking every rendered image in one context), dual-agent **peak context is much smaller**—Proposer never sees images; Reviewer each round only sees the latest screenshots.

The canonical completed run is
[`validation/runs/exp5-4-real-pdf-both-20260730-v9/comparison_summary.json`](validation/runs/exp5-4-real-pdf-both-20260730-v9/comparison_summary.json)
(SHA-256 `bfd913d311ab4d6ad5a8cae93b61ce54ce6d19f9d2d10ee2afdef06becd1e09f`).
Both twenty-page decks used the pinned real PDF and three original,
provenance-tracked figure crops, rendered every page, and scored 95/pass under
the same independent Vision judge. Quality tied; dual-agent peak context was
24,186 tokens versus 92,601 for single-agent self-review (3.83×), with total
usage 73,227 versus 298,259 tokens. Every formal gate is true.

### Why render before judging

When the Agent finishes Slidev source it **does not know the real layout**: crowding, overflow, image size only appear after pixel render. Reviewer therefore receives **new information** the Proposer never saw—the value of the mechanism.

### Proposer–Reviewer split

| Role | Duty | Context contents |
|---|---|---|
| **Proposer** (configured text model) | Read paper → plan pages → write/revise `slides.md` | Paper text + **accumulated structured text feedback** (never images) |
| **Reviewer** (configured Vision model) | Look at latest per-page PNGs; structured JSON advice | **Fresh call each round**, latest screenshots only |

Reviewer advice is structured and actionable, not vague “looks bad”: fields `page`, `issue_type` (`text_overflow` / `overcrowded` / `image_size` / `readability` / `layout`), `severity` (high/medium/low), `suggestion`, plus deck-level `overall_score` and `pass`.

Loop: feedback → revise → re-submit until `pass` or max rounds.

### Ablation: single-agent self-review vs dual-agent

`demo.py` runs both and scores both final decks with the **same independent Vision judge** (comparable quality):

- **A dual-agent**: as above. Proposer context grows in text only; Reviewer resets each round.
- **B single-agent self-review**: one agent in **one conversation** generates → sees its own renders → revises. Past images **stay in context** and inflate quickly (book: “context blows past limits”).

The script prints per-call prompt token series, totals, and **peak context** (max single prompt tokens). More pages/rounds → larger B vs A peak gap.

### Run

```bash
# 1) From the repository root: Python deps
uv sync --locked --python 3.12 --extra ch5

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch5]"

cd chapter5/paper-to-ppt

# Single-project compatibility path, still supported during migration:
# python -m pip install -r requirements.txt

# 2) Slidev + render deps (Node). First time ~1–2 min:
npm install
#   - @slidev/cli
#   - playwright-chromium (under slidev export --format png)
#   - typescript (twoslash highlighting; else export may ERR_MODULE_NOT_FOUND)
#   If chromium binary missing:
#     npx playwright install chromium

# 3) Keys
cp env.example .env    # OPENAI_API_KEY (or OPENROUTER_API_KEY fallback)

# 4) Canonical manuscript campaign: pinned real arXiv PDF, three original
#    PDF figures, both comparison arms, real Slidev rendering and Vision review
python demo.py --provider ark --text-model doubao-seed-1-6-250615 \
  --vision-model doubao-seed-1-6-250615 --mode both --max-rounds 4 \
  --out-dir validation/runs/my-real-run
```

#### Common flags (`python demo.py --help`)

A full run may call gpt-5.6-luna Vision dozens of times (slow/costly). Flags for faster paths, other papers, output dirs, models:

| Flag | Role |
|---|---|
| `--paper PATH` | Legacy/non-canonical local Markdown input. Omit it for the pinned real arXiv PDF used by the formal campaign. |
| `--out-dir DIR` | Artifacts dir (default `output/`): per-round `slides.md` / `review.json` / `comparison_summary.json`. Rendered PNGs always under `slidev_workspace/exports/` |
| `--text-model NAME` | Proposer / single-agent text model; overrides `TEXT_MODEL` (default `gpt-5.6-luna`) |
| `--vision-model NAME` | Reviewer / judge vision model (must support images); overrides `VISION_MODEL` (default `gpt-5.6-luna`) |
| `--mode {both,dual,single}` | One scheme only (`dual` / `single`) to cut time/cost; `both` (default) for cross-scheme compare |
| `--max-rounds N` | Max iterations per scheme (default 3). `--max-rounds 1` = first draft only—fastest real-LLM smoke |
| `--dry-run` | **Offline** Proposer–Reviewer loop: real render of two scripted `slides.md` (crowded draft → split revision); **deterministic heuristics** (char count per page, not Vision LLM) as Reviewer. **No LLM, no API key** |
| `--smoke` | **Only** Slidev render path (2-page deck); **no LLM, no API key** |

```bash
python demo.py --smoke                 # free: Node/Slidev/chromium OK?
python demo.py --dry-run               # free: offline dual-agent loop with real renders
python demo.py --mode dual --max-rounds 1   # one real LLM smoke (needs API key)
python demo.py --paper my_paper.md --out-dir run_my
```

> In `--dry-run`, both `slides.md` versions are **scripted** (not LLM); Reviewer is a **heuristic** on char counts—not Vision. It only runs the **structure** of the loop offline and produces real PNGs. For real pixel review with gpt-5.6-luna use `python demo.py` (needs `OPENAI_API_KEY`). One offline dry-run: draft 4 pages (pages 2/3/4 high overcrowded, score=55, pass=False) → revised 18 pages (score=100, pass=True); PNGs under `slidev_workspace/exports/dryrun_round*/`.

### Files

| File | Role |
|---|---|
| `demo.py` | Main: both schemes, independent judge, token comparison |
| `agents.py` | `Proposer` / `Reviewer` / `SelfReviewAgent` + `TokenMeter` |
| `renderer.py` | `slidev export --format png` → per-page PNGs |
| `paper_source.py` | Downloads the hash-pinned paper PDF, extracts its text, and crops three original paper figures with provenance |
| `make_figures.py` / `paper/sample_paper.md` | Legacy local-Markdown compatibility path; never satisfies the formal campaign gate |
| `package.json` | Slidev + render deps |
| `output/` | Per-round `slides.md`, `review.json`, `comparison_summary.json` |
| `slidev_workspace/exports/` | Per-round PNG folders (`dual_round1/`, `single_round1/`, …) |

### Sample outputs

After a full run (excerpt of real artifacts):

```
output/
├── dual_round1_slides.md
├── dual_round1_review.json
├── dual_round2_slides.md
├── dual_round2_review.json
├── dual_round3_slides.md
├── single_round1_slides.md
├── single_round2_slides.md
├── single_round3_slides.md
└── comparison_summary.json

slidev_workspace/exports/
├── dual_round1/1.png … 5.png
├── dual_round2/1.png … 8.png
└── single_round1/1.png …
```

> Slidev PNG export is **one PNG per page** (`1.png`, `2.png`, …), not a single PDF; change `--format png` to `--format pdf` in `renderer.py` if needed. `comparison_summary.json` holds `iteration_scores`, `final_quality`, and `peak_context_prompt_tokens`—the book’s core comparison numbers.

### Adapt / extend

- **Model / provider**: env (`env.example`) or CLI (CLI wins); no code change.
  - `OPENAI_API_KEY` (or `OPENROUTER_API_KEY` fallback).
  - `OPENAI_BASE_URL`: any OpenAI-compatible endpoint.
  - `TEXT_MODEL` / `--text-model` (default `gpt-5.6-luna`).
  - `VISION_MODEL` / `--vision-model` must support images (default `gpt-5.6-luna`).
- **Paper / out dir**: omit `--paper` for the canonical hash-pinned arXiv PDF; `--paper PATH` is a legacy compatibility path that cannot pass the formal source-provenance gate. `--out-dir DIR` selects the evidence directory.
- **Slidev deps**: need **Node** + local `node_modules/` (`@slidev/cli`, `playwright-chromium`, `typescript`). Re-run `npm install`; if browser binary missing, `npx playwright install chromium`. Then `python demo.py --smoke` before a full run.

### Canonical source and layout preflight

The formal mode does not manufacture an intentionally bad first draft.
Before paying for pixel review, a deterministic source preflight requires
18–20 pages, at most four bullets per page, dedicated source-figure pages,
short one-line figure titles, and bounded inline image layout. Vision remains
the authority for actual overflow, readability and layout. The two attention
figures retain the published pixels and exact PDF crop rectangles; a recorded
90-degree presentation transform makes the original vertical labels readable
on a landscape slide. Failed refinement runs remain under `validation/runs/`
and are never promoted when the independent judge reports a blocking defect.

### Limitations

- **Subjective taste**: Reviewer preferences ≠ user preferences; may converge to Reviewer-local optima (see book thinking questions).
- **Input modes**: the canonical mode parses a real hash-pinned PDF and uses three crops from that PDF. `--paper PATH` deliberately remains a non-canonical compatibility mode with programmatic figures.
- **Cost/time**: up to 20 screenshots per Reviewer round; screenshots are scaled to 1280px wide before the Vision call.
- **Non-determinism**: LLM/Vision scores vary; `temperature` lowered but “pass in 1 round” depends on first draft.
- **Render deps**: `slidev export` needs playwright-chromium; fix binary issues before running (see step 2).

---

## 中文

### 一句话结论

Proposer 只写 Slidev 代码、Reviewer 真正把每页**渲染成 PNG** 再用 **Vision LLM 看图**
挑毛病（文字溢出 / 内容拥挤 / 图片尺寸），Proposer 据结构化反馈迭代修订。相比"单 Agent
自审"（把历次渲染图片都堆在同一上下文里），双 Agent 分工的**上下文峰值显著更小**——
因为 Proposer 全程不看图片、Reviewer 每轮只看最新一版截图。

### 为什么需要"渲染出来再看"

Agent 写完 Slidev 代码时**并不知道实际渲染效果**：内容会不会太挤、文字会不会溢出、
图片尺寸是否合适——这些只有真正渲染成像素才看得出来。所以 Reviewer 接触到的是
Proposer 看不到的**新信息**（渲染结果），这正是本机制的价值所在。

### 提议者-审核者分工

| 角色 | 职责 | 上下文里有什么 |
|---|---|---|
| **Proposer**（`gpt-5.6-luna`，纯文本） | 读论文 → 规划页面 → 生成/修订 `slides.md` | 论文正文 + **累积的结构化文字反馈**（永不含图片） |
| **Reviewer**（`gpt-5.6-luna`，Vision） | 看最新一版每页 PNG，输出结构化建议 JSON | **每轮全新调用**，只含最新一版截图 |

Reviewer 的建议是结构化、可执行的，而非模糊的"不好看"，包含字段：
`page`（页码）、`issue_type`（`text_overflow`/`overcrowded`/`image_size`/`readability`/`layout`）、
`severity`（high/medium/low）、`suggestion`（具体修改建议）、以及整份的 `overall_score` 与 `pass`。

Proposer 收到反馈 → 理解意图 → 修订代码 → 再次提交 Reviewer，循环直到 `pass` 或达最大轮数。

### 对照实验：单 Agent 自审 vs 双 Agent 分工

`demo.py` 同时跑两种方案，并用**同一位独立 Vision 评委**给两者的最终 PPT 打分（保证质量可比）：

- **方案 A 双 Agent**：如上。Proposer 上下文只增文本；Reviewer 每轮重置、只看最新截图。
- **方案 B 单 Agent 自审**：一个 Agent 在**同一段对话**里生成 → 看自己的渲染截图自审 → 修订。
  历次渲染的图片会**一直留在上下文里**，随迭代快速膨胀（书中所述"上下文迅速超限"）。

脚本打印每次调用的 prompt token 序列、总量、以及**上下文峰值**（单次 prompt token，
决定是否撑爆上下文窗口）。页数越多、迭代越多，方案 B 的峰值相对方案 A 越夸张。

### 运行

```bash
# 1) 在仓库根目录安装 Python 依赖
uv sync --locked --python 3.12 --extra ch5

# 切换目录前先激活环境：
# macOS/Linux：
source .venv/bin/activate
# Windows PowerShell：.\.venv\Scripts\Activate.ps1
# Windows cmd：.venv\Scripts\activate.bat

# 未安装 uv 时可用 pip 兜底：
# python -m pip install -e ".[ch5]"

cd chapter5/paper-to-ppt

# 迁移期间仍支持单项目兼容路径：
# python -m pip install -r requirements.txt

# 2) Slidev + 渲染依赖（Node）。首次约 1-2 分钟：
npm install
#   - @slidev/cli：Slidev 命令行
#   - playwright-chromium：slidev export --format png 的底层浏览器
#   - typescript：Slidev 的 twoslash 代码高亮所需（否则 export 会 ERR_MODULE_NOT_FOUND）
#   若 npm install 没有自动装好 chromium 浏览器二进制，运行：
#     npx playwright install chromium

# 3) 配置 Key
cp env.example .env    # 填入 OPENAI_API_KEY（未配置时设 OPENROUTER_API_KEY 自动改走 OpenRouter）

# 4) 正式活动：固定哈希的真实 arXiv PDF、三张原论文图、两种对照方案、
#    真实 Slidev 渲染与 Vision 审查
python demo.py --provider ark --text-model doubao-seed-1-6-250615 \
  --vision-model doubao-seed-1-6-250615 --mode both --max-rounds 4 \
  --out-dir validation/runs/my-real-run
```

#### 常用参数（`python demo.py --help`）

一次完整运行会做数十次 gpt-5.6-luna Vision 调用，较慢较贵。下列参数提供更快的路径，并允许更换论文、输出目录与模型：

| 参数 | 作用 |
|---|---|
| `--paper PATH` | 非正式兼容入口：使用本地 Markdown。正式活动须省略该参数，以使用固定哈希的真实 arXiv PDF。 |
| `--out-dir DIR` | 产物输出目录（默认 `output/`）：各轮 `slides.md`/`review.json`/`comparison_summary.json`。渲染 PNG 始终在 `slidev_workspace/exports/`。 |
| `--text-model NAME` | Proposer / 单 Agent 文本模型，**覆盖** `TEXT_MODEL` 环境变量（默认 `gpt-5.6-luna`）。 |
| `--vision-model NAME` | Reviewer / 独立评委看图模型（须支持图像），**覆盖** `VISION_MODEL` 环境变量（默认 `gpt-5.6-luna`）。 |
| `--mode {both,dual,single}` | 只跑一种方案（`dual`=提议者-审核者，`single`=单 Agent 自审），省一半时间/费用；`both`（默认）才做跨方案对比。 |
| `--max-rounds N` | 每种方案的最大迭代轮数（默认 3）。`--max-rounds 1` 只出首版、不修订，是最快的**真实 LLM** 冒烟。 |
| `--dry-run` | **离线走通提议者-审核者循环**：真实渲染两版脚本化 `slides.md`（拥挤初稿→拆页修订稿），用**确定性启发式规则**（按每页文字量判定，非 Vision LLM）扮演 Reviewer，完整展示“生成→渲染→审查→修订”闭环。**不调用任何 LLM、无需 API Key**。 |
| `--smoke` | **只**验证 Slidev 渲染链路（渲染一个两页 deck），**不调用任何 LLM、无需 API Key**。最快的“没搞坏渲染”自检。 |

```bash
python demo.py --smoke                 # 不花钱，验证 Node/Slidev/chromium 可用
python demo.py --dry-run               # 不花钱，离线看清提议者-审核者闭环（真实渲染）
python demo.py --mode dual --max-rounds 1   # 一次真实 LLM 冒烟（需 API Key）
python demo.py --paper my_paper.md --out-dir run_my   # 换论文、换输出目录
```

> `--dry-run` 里的两版 `slides.md` 是**脚本化**的（不是 LLM 生成），Reviewer 也只是按字符数判定拥挤的**启发式规则**、并非 Vision LLM——它只用来在没有 API Key 时把闭环**结构**跑通、产出真实渲染的 PNG。要看 gpt-5.6-luna **真的看像素**审查，请用 `python demo.py`（需 `OPENAI_API_KEY`）。一次离线 dry-run 的真实结果：初稿 4 页（第 2/3/4 页被判 high 级 overcrowded、score=55、pass=False）→ 拆页修订稿 18 页（score=100、pass=True），渲染 PNG 见 `slidev_workspace/exports/dryrun_round*/`。

### 文件说明

| 文件 | 作用 |
|---|---|
| `demo.py` | 主流程：跑两种方案、独立评委打分、打印 token 对比 |
| `agents.py` | `Proposer` / `Reviewer` / `SelfReviewAgent` 三个 Agent + `TokenMeter` 计量 |
| `renderer.py` | 调 `slidev export --format png` 把 `slides.md` 渲染成逐页 PNG |
| `paper_source.py` | 下载固定哈希的真实论文 PDF、直接提取正文，并裁出三张带来源信息的原论文图 |
| `paper/sample_paper.md` / `make_figures.py` | 旧版本地 Markdown 兼容路径；不会通过正式实验的来源门禁 |
| `package.json` | Slidev 与渲染依赖 |
| `output/` | 运行产物：各轮 `slides.md`、`review.json`、`comparison_summary.json` |
| `slidev_workspace/exports/` | 各轮渲染出的 PNG（`dual_round1/`、`single_round1/` …） |

### 预期输出示例

一次完整运行后，`output/` 与 `slidev_workspace/exports/` 下的真实产物（节选）：

```
output/
├── dual_round1_slides.md      # 双 Agent 第 1 版 slidev 源码（首版故意很挤）
├── dual_round1_review.json    # Reviewer 对第 1 版的结构化建议 JSON
├── dual_round2_slides.md      # 据反馈修订后的第 2 版
├── dual_round2_review.json
├── dual_round3_slides.md
├── single_round1_slides.md    # 单 Agent 自审各版
├── single_round2_slides.md
├── single_round3_slides.md
└── comparison_summary.json    # 两方案质量分 + token 消耗汇总

slidev_workspace/exports/
├── dual_round1/1.png … 5.png      # 首版渲染：段落太长、图表底部超出页面
├── dual_round2/1.png … 8.png      # 修订版：拆页后每页 8 张更干净
└── single_round1/1.png …          # 单 Agent 各版渲染
```

> 说明：Slidev 的 PNG 导出是**逐页一张 PNG**（`1.png`、`2.png`…），本实验不产出单一 PDF；
> 如需 PDF，可把 `renderer.py` 里的 `--format png` 改为 `--format pdf`。
> `comparison_summary.json` 里记录两方案的 `iteration_scores`、`final_quality` 与
> `peak_context_prompt_tokens`（上下文峰值），即书中的核心对比数据。

### 如何适配 / 扩展

- **换模型 / 换供应商**：通过环境变量（见 `env.example`）或命令行参数（优先级更高），代码无需改动。
  - `OPENAI_API_KEY`：密钥（必填其一；未配置时用 `OPENROUTER_API_KEY` 兜底，自动改走 OpenRouter）。
  - `OPENAI_BASE_URL`：指向任何兼容 OpenAI 协议的端点（自建网关 / 其它供应商）。
  - `TEXT_MODEL` / `--text-model`：Proposer / 单 Agent 文本部分用的模型（默认 `gpt-5.6-luna`）。
  - `VISION_MODEL` / `--vision-model`：Reviewer / 独立评委看图用的模型，**必须支持图像输入**（默认 `gpt-5.6-luna`）。
- **换输入论文 / 输出目录**：正式活动省略 `--paper`，使用固定哈希的真实 arXiv PDF 与三张原论文图；
  `--paper my.md` 只用于兼容自定义 Markdown，不会被标记为正式完成。`--out-dir DIR` 指定证据目录。
- **Slidev 渲染依赖（重要）**：渲染链路依赖 **Node** + 本目录内 `node_modules/`，其中包含
  `@slidev/cli`、`playwright-chromium`（`slidev export --format png` 的底层浏览器）、`typescript`
  （twoslash 代码高亮所需）。若 `node_modules/` 缺失或损坏，在本目录执行 `npm install` 重装；
  若浏览器二进制没装好，补跑 `npx playwright install chromium`。装好后先 `python demo.py --smoke`
  验证渲染链路，再跑完整流程。

### 关于"第一版故意写得很挤"

为了**稳定复现**"渲染 → 发现问题 → 修订"的闭环，`agents.py` 里让 Proposer/单 Agent 的
**首版**先把整篇论文塞进约 4 页、成段贴原文（一种常见的"先把内容倒进去"的初稿写法）。
这会产生**真实的**文字溢出与图表被裁切（见 `slidev_workspace/exports/dual_round1/2.png`：
段落太长、图表底部超出页面）。Reviewer 的问题都是视觉模型（默认 gpt-5.6-luna）**看真实像素**得出的，修订也是
真实的——不是预设脚本。若把首版指令改成"直接生成 8-12 页精简版"，视觉模型往往一版就过关，
反而看不到迭代过程。一次真实运行的结果（会有随机波动）：

```
双 Agent：round1 score=85 pass=False（4 个 medium：p2/p3/p4 overcrowded、p2 image_size）
          → Proposer 拆页精简 → round2 score=95 pass=True（+10 改善）
上下文峰值：双 Agent = 9308 tok，单 Agent 自审 = 14179 tok（单 Agent 图片累积：1640→8069→14179）
```

### 局限

- **审美主观**：Reviewer 的偏好未必等于目标用户的偏好，反馈循环可能收敛到 Reviewer
  认可但用户嫌挤的局部最优（见书末思考题：如何让用户偏好也进入循环）。
- **输入模式**：正式模式解析固定哈希的真实 PDF，并直接裁出三张原论文图；只有显式使用
  `--paper PATH` 时才走程序化图表的旧版兼容路径。
- **成本/时长**：每轮 Reviewer 要把约 10 张截图发给视觉模型（默认 gpt-5.6-luna），单次运行需数十次
  API 调用；已把截图统一缩放到 1280px 宽以控制 token。
- **确定性**：LLM 与 Vision 判定有随机性，具体分数/建议每次略有不同；`temperature`
  已调低，但迭代是否恰好"1 轮达标"取决于首版质量。
- **渲染依赖**：`slidev export` 依赖 playwright-chromium；无网络/无法装 chromium 的
  环境需先解决浏览器二进制问题（见"运行"第 2 步）。

---

## Notes / 说明

- Start with `--smoke` / `--dry-run` before a full Vision run. / 完整 Vision 跑前先 `--smoke` / `--dry-run`。
- Commands/code/paths/env vars are identical in both language sections. / 命令、代码、路径与环境变量在中英文两侧保持一致。
