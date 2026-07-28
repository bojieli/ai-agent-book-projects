# Agent Skills PPT Demo / 使用 Agent Skills 从论文生成演示文稿

> Companion material for *AI Agents in Depth*, Chapter 2 — **Experiment 2-6 ★★: Generate a presentation from a paper using Agent Skills**.  
> 配套《深入理解 AI Agent》第 2 章 **实验 2-6 ★★：使用 Agent Skills 从论文生成演示文稿**。

← [Chapter 2 index / 返回第 2 章目录](../README.md)

---

## English

### Purpose

Validates a core claim from the book: **an Agent can complete complex work by loading domain Skills on demand via progressive disclosure**, without stuffing all knowledge into the system prompt at once.

This demo lets an Agent turn a (bundled) short paper into an 8–12 page PowerPoint. At startup the Agent sees only a **thin Skill catalog**; when it decides the task needs the `pptx` Skill, it loads the full workflow, sub-docs, and bundled scripts layer by layer, then generates a real `.pptx` with **python-pptx**.

### Relation to Anthropic’s PPTX Skill

The original book experiment ran on **Claude Code + Anthropic’s official PPTX Skill**. Because Anthropic access is not always available, this project **implements an isomorphic Skills mechanism** (not Anthropic’s runtime):

| Dimension | Anthropic PPTX Skill (book) | This project (isomorphic) |
|-----------|-----------------------------|---------------------------|
| Runtime | Claude Code | Python + OpenAI SDK (`gpt-5.6-luna`) |
| Layer 1 · metadata | Inject name+description of all Skills at start | `scan_skill_catalog()` reads frontmatter into the system prompt |
| Layer 2 · core flow | Skill tool loads full `SKILL.md` | `read_skill` loads `skills/pptx/SKILL.md` |
| Layer 3 · details | Refs like `html2pptx.md` / `reference.md` | `read_skill_file` reads `reference.md` / script sources |
| Bundled scripts | e.g. `scripts/thumbnail.py` | `scripts/generate_pptx.py` (python-pptx generator) |

The mechanism maps one-to-one; the built-in Skill loader is replaced by explicit read/execute tools so progressive disclosure still works without Anthropic access.

> **OpenRouter fallback:** Primary path is OpenAI (default model `gpt-5.6-luna`). If `OPENAI_API_KEY` is unset but `OPENROUTER_API_KEY` is set, requests go through OpenRouter (`gpt-*` → `openai/…`). With `OPENAI_API_KEY` set, behavior is unchanged.

### Three-layer progressive disclosure

```
skills/
└── pptx/
    ├── SKILL.md              # L1: YAML frontmatter (name+description) only in system prompt
    │                         # L2: body core flow — loaded via read_skill
    ├── reference.md          # L3: layout/color/tech details — via read_skill_file
    └── scripts/
        └── generate_pptx.py  # Bundled script — via run_skill_script
```

- **Layer 1 (metadata):** At startup the system prompt only has each Skill’s `name + description` (~hundreds of tokens). The Agent does not yet know how to build a PPT.
- **Layer 2 (core flow):** When the task needs `pptx`, it calls `read_skill("pptx")` and loads full `SKILL.md` as a tool result (page plan + script conventions).
- **Layer 3 (details):** For implementation/style detail, call `read_skill_file("pptx", "reference.md")` or read script sources.
- **Execute:** Build a slide-outline JSON, call `run_skill_script` → `generate_pptx.py` → `output/presentation.pptx`.

### Run

```bash
pip install -r requirements.txt
cp env.example .env        # or export directly
export OPENAI_API_KEY=sk-...   # default model gpt-5.6-luna; override with OPENAI_MODEL
python demo.py
python demo.py --paper papers/your_paper.md    # different paper/outline
python demo.py -o output/deck.pptx --model gpt-5.6-luna   # output path / model
python demo.py --help                          # full flag list
```

One command `python demo.py` runs the full path: real OpenAI calls, prints each progressive-disclosure step, writes `output/presentation.pptx`, and re-opens the file with python-pptx to verify page count and titles.

#### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--paper` | `papers/sample_paper.md` | Input paper/outline (markdown) path |
| `--output` / `-o` | `output/presentation.pptx` | Output `.pptx` path |
| `--model` | `OPENAI_MODEL` or `gpt-5.6-luna` | OpenAI model name |
| `--max-turns` | `8` | Max agentic-loop turns |
| `--offline` | off | Offline demo, no OpenAI (see below) |

#### Offline mode (no API key, reproducible)

Without an OpenAI key, `--offline` runs the same three-layer progressive disclosure: it reads the bundled outline `papers/sample_outline.json` and uses the **same tool path** (`read_skill` → `read_skill_file` → `run_skill_script`) to generate and verify the pptx deterministically. The only difference is that which Skill/outline to use is fixed by files, not live model decisions—good for teaching demos and smoke tests.

```bash
python demo.py --offline                       # writes output/presentation.pptx, no network
python demo.py --offline -o output/deck.pptx   # custom output path
```

The bundled script can also run alone (no Agent):

```bash
python skills/pptx/scripts/generate_pptx.py papers/sample_outline.json output/deck.pptx
```

### Sample run output (excerpt)

```
【第一层·元数据】Agent 启动时只看到这份薄 Skill 目录（system prompt）：
== 已安装的 Skills（薄目录，仅元数据）==
- pptx: 从论文...生成 PowerPoint...Use when...Don't use when...

[Agent 第 1 轮] 调用工具 -> read_skill(name=pptx)
  >>> [渐进式披露·第二层] 加载完整 SKILL.md（1150 字符）
[Agent 第 2 轮] 调用工具 -> read_skill_file(name=pptx, path=scripts/generate_pptx.py)
  >>> [渐进式披露·第三层] 加载子文档（4270 字符）
[Agent 第 3 轮] 调用工具 -> run_skill_script(name=pptx, script=generate_pptx.py, ...)
  >>> 生成 presentation.pptx ...

【校验】用 python-pptx 重新打开生成的文件，读回页数与每页标题：
总页数: 9
  第  1 页标题: 精简论文：渐进式披露式 Agent Skills 对上下文效率的影响
  ...
校验通过：这是一个可被 python-pptx / PowerPoint 打开的有效 .pptx（9 页）。
```

(Page count/titles are planned live by the model and may vary slightly, usually within 8–12 pages.)

### Files

| File | Role |
|------|------|
| `demo.py` | Main: thin catalog scan → agentic loop → progressive disclosure → generate & verify pptx |
| `skills/pptx/SKILL.md` | pptx Skill: frontmatter (metadata) + core flow |
| `skills/pptx/reference.md` | Layer 3: layout/color/python-pptx notes |
| `skills/pptx/scripts/generate_pptx.py` | Bundled generator: outline → `.pptx` |
| `papers/sample_paper.md` | Bundled short paper/outline (online input) |
| `papers/sample_outline.json` | Slide outline for offline mode (payload schema example) |
| `output/presentation.pptx` | Generated deck (created at runtime) |

### Use another paper

Replace `papers/sample_paper.md` or pass `python demo.py --paper your_paper.md`.

---

## 中文

### 目的

验证书中的核心命题：**Agent 通过「渐进式披露（Progressive Disclosure）」按需加载专业领域 Skill，即可完成复杂任务，而无需把所有知识一次性塞进系统提示词。**

本 demo 让一个 Agent 从一篇（自带的）精简论文生成一份 8-12 页的 PowerPoint。Agent 启动时**只看到一份薄 Skill 目录**，当它识别出任务需要 `pptx` Skill 后，才逐层加载该 Skill 的完整流程、子文档与捆绑脚本，最后用 **python-pptx** 生成真实的 `.pptx` 文件。

### 与 Anthropic PPTX Skill 的关系

书中原实验跑在 **Claude Code + Anthropic 官方 PPTX Skill** 上。由于当前环境的 Anthropic key 未必可用，本项目**自建了一套同构的 Skills 机制**来复现同样的思想，而非调用 Anthropic：

| 维度 | Anthropic PPTX Skill（书中） | 本项目（自建同构版） |
|------|------------------------------|----------------------|
| 运行时 | Claude Code | Python + OpenAI SDK（`gpt-5.6-luna`） |
| 第一层·元数据 | 启动注入所有 Skill 的 name+description | `scan_skill_catalog()` 只读 frontmatter 拼进 system prompt |
| 第二层·核心流程 | Skill 工具加载完整 `SKILL.md` | `read_skill` 工具加载 `skills/pptx/SKILL.md` |
| 第三层·细则 | 引用 `html2pptx.md` / `reference.md` | `read_skill_file` 读 `reference.md` / 脚本源码 |
| 捆绑脚本 | `scripts/thumbnail.py` 等 | `scripts/generate_pptx.py`（python-pptx 生成器） |

机制一一对应，只是把「Claude 内置的 Skill 加载器」换成了几个显式的读取/执行工具，从而在没有 Anthropic 访问权限时，依然能真实演示渐进式披露的三层加载过程。

> 说明：本项目主用 OpenAI（默认模型 gpt-5.6-luna）。**通用回退**：未设置 `OPENAI_API_KEY` 时，只要配置了 `OPENROUTER_API_KEY`，会自动改走 OpenRouter（`gpt-*` 映射为 `openai/…`）。设置了 `OPENAI_API_KEY` 时行为完全不变。

### 渐进式披露的三层结构

```
skills/
└── pptx/
    ├── SKILL.md              # 第一层：顶部 YAML frontmatter(name+description) —— 只有它进 system prompt
    │                         # 第二层：正文核心流程 —— read_skill 时才加载
    ├── reference.md          # 第三层：版式/配色/技术细则 —— read_skill_file 时才加载
    └── scripts/
        └── generate_pptx.py  # 捆绑可执行脚本 —— run_skill_script 时才执行
```

- **第一层（元数据）**：Agent 启动时，`system prompt` 里只有各 Skill 的 `name + description`（约数百 token）。此刻它并不知道怎么做 PPT。
- **第二层（核心流程）**：Agent 判断任务需要 `pptx`，调用 `read_skill("pptx")` 把完整 `SKILL.md` 作为 tool result 载入上下文，得到页序规划与脚本调用约定。
- **第三层（细则）**：如需实现/样式细节，Agent 再用 `read_skill_file("pptx", "reference.md")` 或读取脚本源码。
- **执行**：Agent 组织好幻灯片大纲 JSON，通过 `run_skill_script` 调用捆绑的 `generate_pptx.py`，用 python-pptx 落地为 `output/presentation.pptx`。

### 运行

```bash
pip install -r requirements.txt
cp env.example .env        # 或直接 export
export OPENAI_API_KEY=sk-...   # 默认模型 gpt-5.6-luna，可用 OPENAI_MODEL 覆盖
python demo.py
python demo.py --paper papers/your_paper.md    # 换一篇论文/大纲
python demo.py -o output/deck.pptx --model gpt-5.6-luna   # 指定输出路径 / 模型
python demo.py --help                          # 查看全部参数
```

一条命令 `python demo.py` 即可跑通：真实调用 OpenAI，打印渐进式披露的每一步，生成 `output/presentation.pptx`，并用 python-pptx 重新打开该文件读回页数与每页标题作为校验。

#### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--paper` | `papers/sample_paper.md` | 输入论文/大纲（markdown）路径 |
| `--output` / `-o` | `output/presentation.pptx` | 输出 `.pptx` 路径 |
| `--model` | `OPENAI_MODEL` 或 `gpt-5.6-luna` | OpenAI 模型名 |
| `--max-turns` | `8` | agentic loop 的最大轮数 |
| `--offline` | 关 | 离线演示，不调用 OpenAI（见下） |

#### 离线模式（无需 API key，可复现）

没有 OpenAI key 时，用 `--offline` 即可跑通同一套三层渐进式披露：它读取内置大纲 `papers/sample_outline.json`，走**与在线完全相同**的工具通道（`read_skill` → `read_skill_file` → `run_skill_script`）确定性地生成并校验 pptx。唯一区别是「用哪个 Skill、大纲写什么」由预置文件给定，而非模型即时决策——因此它适合作为可复现的教学演示与冒烟测试。

```bash
python demo.py --offline                       # 生成 output/presentation.pptx，全程无网络
python demo.py --offline -o output/deck.pptx   # 指定输出路径
```

捆绑脚本本身也可脱离 Agent 单独运行，直接把大纲 JSON 落地为 pptx：

```bash
python skills/pptx/scripts/generate_pptx.py papers/sample_outline.json output/deck.pptx
```

### 真实运行输出（节选）

```
【第一层·元数据】Agent 启动时只看到这份薄 Skill 目录（system prompt）：
== 已安装的 Skills（薄目录，仅元数据）==
- pptx: 从论文...生成 PowerPoint...Use when...Don't use when...

[Agent 第 1 轮] 调用工具 -> read_skill(name=pptx)
  >>> [渐进式披露·第二层] 加载完整 SKILL.md（1150 字符）
[Agent 第 2 轮] 调用工具 -> read_skill_file(name=pptx, path=scripts/generate_pptx.py)
  >>> [渐进式披露·第三层] 加载子文档（4270 字符）
[Agent 第 3 轮] 调用工具 -> run_skill_script(name=pptx, script=generate_pptx.py, ...)
  >>> 生成 presentation.pptx ...

【校验】用 python-pptx 重新打开生成的文件，读回页数与每页标题：
总页数: 9
  第  1 页标题: 精简论文：渐进式披露式 Agent Skills 对上下文效率的影响
  第  2 页标题: 目录
  ...
  第  9 页标题: 小结
校验通过：这是一个可被 python-pptx / PowerPoint 打开的有效 .pptx（9 页）。
```

（页数/标题由模型即时规划，每次运行可能略有差异，但均落在 8-12 页区间。）

### 文件说明

| 文件 | 作用 |
|------|------|
| `demo.py` | 主程序：扫描薄目录 → agentic loop → 渐进式披露 → 生成并校验 pptx |
| `skills/pptx/SKILL.md` | pptx Skill：frontmatter（元数据）+ 核心流程 |
| `skills/pptx/reference.md` | 第三层细则：版式/配色/python-pptx 技术点 |
| `skills/pptx/scripts/generate_pptx.py` | 捆绑生成器，用 python-pptx 从大纲生成 .pptx |
| `papers/sample_paper.md` | 自带的精简论文/大纲（在线模式输入） |
| `papers/sample_outline.json` | 内置幻灯片大纲（离线模式输入，同时是 payload schema 的范例） |
| `output/presentation.pptx` | 生成的演示文稿（输出，运行后产生） |

### 换一篇论文

把 `papers/sample_paper.md` 替换为你自己的论文/大纲（markdown），或直接 `python demo.py --paper 你的论文.md` 指定路径即可。

---

## Notes / 说明

- Commands, paths, env vars, and model names are identical in both language sections.  
- 命令、路径、环境变量与模型名在中英文两节中保持一致。
