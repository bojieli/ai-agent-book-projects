# Experiment 5-11: Conversational UI Customization / 实验 5-11：对话式界面定制系统（★★）

> Companion lab for *AI Agents in Depth*, Chapter 5 — NL UI requests (color/font/copy/layout); Agent edits React source; Vite HMR applies live.  
> 《深入理解 AI Agent》第 5 章：自然语言提 UI 定制需求，Agent 改 React 源码，Vite HMR 即时生效。

← [Chapter 5 index / 返回第 5 章目录](../README.md)

---

## English

### Overview

Users describe UI customizations in **natural language** (color / font / copy / layout / component placement). The Agent **locates and edits front-end source**; dev-mode **HMR** applies changes instantly, with multi-turn iteration.

### Purpose

Turn a one-size-fits-all front end into a conversationally customizable UI:

- Base chatbot = **React (Vite) front end + FastAPI back end**;
- Both run in dev mode: Vite **HMR**, uvicorn **--reload**;
- User says “make the send button blue / monospace font / title = XXX”;
  Agent (OpenAI, default `gpt-5.6-luna`; if no `OPENAI_API_KEY`, set `OPENROUTER_API_KEY` for OpenRouter) reads the request → edits files under `frontend/src`;
- HMR picks up changes without a full page reload.

### Architecture (brief)

Four parts:

- **`agent.py` (customize Agent)**: core. NL requirement + current editable sources → OpenAI; function-calling `apply_edits` returns full rewritten file contents. Only whitelist files (`src/App.jsx`, `src/theme.css`); path checks after return. Produces rewrites **without writing disk** (for diff display + verification).
- **`baseline/src/`**: factory snapshot of front-end sources. Each `demo.py` run restores from here so runs are reproducible and isolated—also the baseline for diffs.
- **`frontend/` (React + Vite)**: what gets customized. Agent edits `src/*`; Vite **HMR** in dev; `vite build` checks “did not break the app”.
- **`backend/` (FastAPI)**: minimal chatbot (`/api/chat`) so the UI can actually chat; default **echo** mode (no key); `--model` switches to **real LLM chat**; CLI via `python main.py --help`; `--reload` demos backend HMR. Not part of UI customize—supporting actor only.

One line: **Agent reads request → edits front-end source → assert change applied + build still works**; `baseline` for reproducibility; `backend` for real chat.

### Hot reload (HMR)

- **Front end**: `npm run dev` Vite HMR. Agent edits `src/*.jsx` or `src/theme.css` → partial hot replace, state kept.
- **Back end**: `uvicorn main:app --reload` restarts on `.py` changes.
- Customization targets front-end sources; visual effect is front-end HMR.

### Directory layout

```
conversational-ui/
├── frontend/                 # React + Vite chatbot UI
│   ├── src/App.jsx           #   UI + copy (Agent: copy/components)
│   ├── src/theme.css         #   colors/fonts/layout (Agent: styles)
│   ├── src/main.jsx
│   ├── index.html
│   ├── vite.config.js        #   HMR + /api proxy to backend
│   └── package.json
├── backend/
│   ├── main.py               # FastAPI (/api/chat)
│   └── requirements.txt
├── baseline/src/             # initial snapshot (restored before each demo)
├── agent.py                  # NL → OpenAI rewrite sources
├── demo.py                   # e2e demo + auto verify (NL→code→assert→build)
├── requirements.txt          # backend + Agent deps
├── env.example
└── .gitignore                # node_modules / dist / .env ignored
```

### How to run

#### 1) Environment

```bash
# Python deps (Agent + backend)
pip install -r requirements.txt

# Front-end deps (first npm install can be slow)
cd frontend && npm install && cd ..

# OpenAI key
cp env.example .env   # OPENAI_API_KEY (or OPENROUTER_API_KEY fallback)
```

#### 2) Auto-verify loop (no browser)

```bash
python demo.py            # all 3 customize rounds + full verify
python demo.py --quick    # round 1 only (smoke)
python demo.py --rounds 2 # first 2 rounds
python demo.py --no-build # skip vite build (assert apply only; faster)
python demo.py -h
```

`demo.py` runs 3 NL customize rounds: real OpenAI rewrite → print diff → re-read sources and assert → `vite build`. First round may be slow (`npm install` / first build); use `--quick` or `--no-build`.

#### 3) Manual real HMR (optional; needs browser)

```bash
# Terminal A: backend (hot reload). Either:
cd backend && python main.py --reload --port 8000
#   or: cd backend && uvicorn main:app --reload --port 8000
#   real LLM chat (not echo): add --model gpt-5.6-luna (needs OPENAI_API_KEY or OPENROUTER_API_KEY)

# Terminal B: front end (HMR)
cd frontend && npm run dev
# open http://localhost:5173

# Terminal C: one customize request; watch the browser update
python -c "import agent,pathlib; c,m=agent.build_client_and_model(); \
r=agent.customize(c,m,pathlib.Path('frontend'),'把发送按钮改成橙色'); \
[pathlib.Path('frontend',f['path']).write_text(f['content']) for f in r['files']]"
```

Backend CLI (`cd backend && python main.py --help`):

| Flag | Description | Default |
| --- | --- | --- |
| `--host` | Bind address (`0.0.0.0` for external) | `127.0.0.1` |
| `--port` | Port (front end proxies `/api` here) | `8000` |
| `--reload` / `--no-reload` | Backend hot reload | on |
| `--model NAME` | Real LLM chat; omit = echo (`CHAT_MODEL` env also works) | none (echo) |
| `--log-level` | uvicorn log level | `info` |
| `--print-config` | Print effective config JSON and exit (no listen) | off |

> Echo vs LLM does not affect the UI customize loop—customize acts on **front-end sources**. LLM mode reuses `OPENAI_API_KEY` / `OPENAI_BASE_URL` from `agent.py`; missing key or call failure falls back to a placeholder reply (never invents).

### Verification and limits

- **This demo auto-verifies**: NL → code change **applied correctly** and **build not broken**.
  - Source asserts: e.g. blue `#2563eb` appears; monospace appears; new title string appears.
  - After each round `vite build` must succeed.
- **This demo does not verify**: real in-browser HMR **visual** refresh (no Playwright/browser here)—use step 3 manually.
- Agent may only rewrite whitelist files (`src/App.jsx`, `src/theme.css`); full-file rewrite is more stable than scattered patches on small files.

### Real run output (excerpt)

```
第 1 轮 NL 定制需求：把发送按钮和用户消息气泡的主题色从绿色改成蓝色，用 #2563eb 这个蓝。
[改动文件] src/theme.css
  - --color-primary: #16a34a;   /* 初始为绿色 */
  + --color-primary: #2563eb;   /* 改为蓝色 */
断言：源码中出现蓝色值 #2563eb -> 通过 ✅
构建结果：通过 ✅

第 2 轮 NL 定制需求：把整个界面的字体换成等宽字体（monospace）。
[改动文件] src/theme.css
  - --font-family: system-ui, "PingFang SC", ... sans-serif;
  + --font-family: monospace;
断言：源码中出现 monospace 等宽字体 -> 通过 ✅
构建结果：通过 ✅

第 3 轮 NL 定制需求：把顶部的标题文案改成"我的专属客服"。
[改动文件] src/App.jsx
  - const HEADER_TITLE = "智能助手";
  + const HEADER_TITLE = "我的专属客服";
断言：源码中出现新标题文案"我的专属客服" -> 通过 ✅
构建结果：通过 ✅

多轮定制总结：全部通过 ✅
```

### Environment variables

| Variable | Description |
| --- | --- |
| `OPENAI_API_KEY` | One of required; this lab reads it (`OPENROUTER_API_KEY` fallback) |
| `OPENAI_BASE_URL` | Optional OpenAI-compatible endpoint |
| `MODEL` | Optional; default `gpt-5.6-luna` |

### Adapt / extend

- **Model / provider**: standard OpenAI SDK; set `OPENAI_BASE_URL` + `MODEL` + `OPENAI_API_KEY`, e.g. Kimi / ARK / local vLLM / Ollama.
- **Editable surface**: default whitelist `src/App.jsx`, `src/theme.css`—edit `EDITABLE_FILES` in `agent.py` (larger = more flexible, more risk).
- **New verify rounds**: append `{"requirement": ..., "verify": ...}` to `ROUNDS` in `demo.py`.
- **Own UI**: replace `frontend/src/*` and update whitelist + `baseline/`.
- **Own backend / real LLM chat**: `/api/chat` is echo by default; `--model <name>` or `CHAT_MODEL` for real chat; customize `_llm_reply` / `chat` for business logic.

---

## 中文

### 概述

用户用**自然语言**提出 UI 定制需求（颜色 / 字体 / 文案 / 布局 / 组件位置），
Agent 自主**定位并修改前端源码**，开发模式下的**热加载（HMR）**让改动即时生效，
支持多轮迭代定制。

### 目的

把"一刀切"的标准前端，变成"千人千面"的可对话定制界面：

- 基础 chatbot 应用 = **React(Vite) 前端 + FastAPI 后端**；
- 前后端都跑在开发模式：前端 Vite **HMR**、后端 uvicorn **--reload**；
- 用户说"把发送按钮改成蓝色 / 换成等宽字体 / 标题改成 XXX"，
  Agent（OpenAI，默认 `gpt-5.6-luna`；未配置 `OPENAI_API_KEY` 时设 `OPENROUTER_API_KEY` 自动改走 OpenRouter）读懂需求 → 改 `frontend/src` 里的源码文件；
- 热加载检测到文件变化，浏览器无需整页刷新即可看到界面变化。

### 原理 / 架构（简述）

整个系统由四部分组成，各司其职：

- **`agent.py`（定制 Agent）**：核心。把一条自然语言需求 + 当前可编辑源码喂给 OpenAI，
  用 function calling 的 `apply_edits` 工具让模型返回"改写后的文件全文"。
  只暴露白名单文件（`src/App.jsx`、`src/theme.css`）给模型，并在返回后校验路径，
  防止模型改错/新增文件。它只产出改写方案，**不落盘**（便于展示 diff 与验证）。
- **`baseline/src/`（基线快照）**：前端源码的"出厂原样"。`demo.py` 每轮开始前把它
  拷回 `frontend/src`，保证多次运行结果可重复、互不污染——这也是 Agent 改动与
  原始界面做 diff 的对照基准。
- **`frontend/`（React + Vite 前端）**：被定制的对象。Agent 改的就是这里的 `src/*`；
  开发模式下 Vite **HMR** 让改动即时可见，`vite build` 用于验证"改动没破坏应用"。
- **`backend/`（FastAPI 后端）**：最小 chatbot 服务（`/api/chat`），为前端提供可对话的载体；
  默认 **echo 回声**模式（开箱即用、无需任何 Key），也可用 `--model` 一键切到**真实 LLM 对话**；
  自带命令行入口（`python main.py --help`），`--reload` 演示"后端热加载"。它不参与 UI 定制，
  是让整套界面能真实跑起来的配角。

一句话：**Agent 读需求 → 改前端源码 → 断言改动生效 + 构建不破坏**，
`baseline` 保证可重复，`backend` 让界面能真实对话。

### 关于热加载（HMR）

- **前端**：`npm run dev` 启动的 Vite dev server 自带 HMR。Agent 一改 `src/*.jsx`
  或 `src/theme.css`，浏览器局部热替换、保留应用状态，界面即时更新。
- **后端**：`uvicorn main:app --reload` 监听 `.py` 变化自动重启。
- 本实验的定制主要作用于前端源码，所以视觉效果靠前端 HMR 体现。

### 目录结构

```
conversational-ui/
├── frontend/                 # React + Vite 前端（基础 chatbot 界面）
│   ├── src/App.jsx           #   界面与 UI 文案（Agent 改"文案/组件"）
│   ├── src/theme.css         #   颜色/字体/布局样式（Agent 改"样式"）
│   ├── src/main.jsx
│   ├── index.html
│   ├── vite.config.js        #   开启 HMR + /api 代理到后端
│   └── package.json
├── backend/
│   ├── main.py               # FastAPI 后端（/api/chat）
│   └── requirements.txt
├── baseline/src/             # 前端源码初始快照（demo 每次运行前恢复，保证可重复）
├── agent.py                  # 定制 Agent：NL 需求 → 用 OpenAI 改写源码
├── demo.py                   # 端到端演示 + 自动验证（NL→代码→断言→构建）
├── requirements.txt          # 后端 + Agent 依赖
├── env.example
└── .gitignore                # node_modules / dist / .env 均已忽略
```

### 运行方式

#### 1) 准备环境

```bash
# Python 依赖（Agent + 后端）
pip install -r requirements.txt

# 前端依赖（首次 npm install 较慢属正常）
cd frontend && npm install && cd ..

# 配置 OpenAI Key
cp env.example .env   # 然后填入 OPENAI_API_KEY（或设 OPENROUTER_API_KEY 兜底）
```

#### 2) 自动验证闭环（无需浏览器）

```bash
python demo.py            # 跑全部 3 轮定制并做完整验证
python demo.py --quick    # 只跑第 1 轮（省时，用于快速冒烟）
python demo.py --rounds 2 # 只跑前 2 轮
python demo.py --no-build # 跳过 vite build（仅验证"改动被正确应用"，更快）
python demo.py -h         # 查看全部参数
```

`demo.py` 会连续跑 3 轮自然语言定制，每轮：
调用真实 OpenAI 改写源码 → 打印改动 diff → 读回源码断言"改动符合需求" →
`vite build` 验证"没破坏应用"。首轮较慢多因 `npm install` 或首次构建，
想快速验证可用 `--quick` 或 `--no-build`。

#### 3) 手动体验真实 HMR（可选，需要浏览器）

```bash
# 终端 A：后端（热加载）。两种启动方式行为一致，任选其一：
cd backend && python main.py --reload --port 8000          # 本文件自带命令行入口
#   或： cd backend && uvicorn main:app --reload --port 8000   # 书中示例写法
#   想让运行起来的 chatbot 真会说话（而非回声）：加 --model gpt-5.6-luna（需 OPENAI_API_KEY 或 OPENROUTER_API_KEY）

# 终端 B：前端（HMR）
cd frontend && npm run dev
# 打开 http://localhost:5173

# 终端 C：跑一条定制需求，回到浏览器即可看到界面即时变化
python -c "import agent,pathlib; c,m=agent.build_client_and_model(); \
r=agent.customize(c,m,pathlib.Path('frontend'),'把发送按钮改成橙色'); \
[pathlib.Path('frontend',f['path']).write_text(f['content']) for f in r['files']]"
```

后端命令行参数（`cd backend && python main.py --help`）：

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `--host` | 监听地址（对外可用 `0.0.0.0`） | `127.0.0.1` |
| `--port` | 监听端口（前端把 `/api` 代理到此端口） | `8000` |
| `--reload` / `--no-reload` | 是否开启后端热加载 | 开启 |
| `--model NAME` | 指定模型名，切到真实 LLM 对话；缺省为 echo 回声模式（也可用环境变量 `CHAT_MODEL`） | 无（echo） |
| `--log-level` | uvicorn 日志/输出级别 | `info` |
| `--print-config` | 只打印生效配置(JSON)后退出，不监听端口（便于无端口环境下校验） | 关 |

> echo 与 LLM 两种模式都不影响 UI 定制闭环——定制作用于**前端源码**，后端只是让界面能真实对话的载体。
> LLM 模式复用与 `agent.py` 相同的 `OPENAI_API_KEY` / `OPENAI_BASE_URL` 配置；缺 Key 或调用失败会自动回退占位提示，绝不编造回复。

### 验证方式与局限

- **本 demo 自动验证的是**：自然语言 → 代码修改被**正确应用**且**不破坏构建**的闭环。
  - 读回源码断言：如"改成蓝色 #2563eb"→ 源码里确实出现该色值；
    "换成等宽字体"→ 出现 `monospace`；"标题改成 XXX"→ 出现该文案。
  - 每轮改动后 `vite build` 必须编译通过，证明改动没破坏应用。
- **本 demo 不做的**：真实浏览器内 HMR 的**视觉**即时刷新。
  本机无 Playwright/浏览器，无法自动截图验证视觉效果——
  这部分需手动 `npm run dev` + 打开浏览器查看（见上文第 3 步）。
- Agent 只被允许改写白名单文件（`src/App.jsx`、`src/theme.css`），
  降低改错文件的风险；改写采用"整文件重写"，对小文件比零散替换更稳。

### 真实运行输出（节选）

```
第 1 轮 NL 定制需求：把发送按钮和用户消息气泡的主题色从绿色改成蓝色，用 #2563eb 这个蓝。
[改动文件] src/theme.css
  - --color-primary: #16a34a;   /* 初始为绿色 */
  + --color-primary: #2563eb;   /* 改为蓝色 */
断言：源码中出现蓝色值 #2563eb -> 通过 ✅
构建结果：通过 ✅

第 2 轮 NL 定制需求：把整个界面的字体换成等宽字体（monospace）。
[改动文件] src/theme.css
  - --font-family: system-ui, "PingFang SC", ... sans-serif;
  + --font-family: monospace;
断言：源码中出现 monospace 等宽字体 -> 通过 ✅
构建结果：通过 ✅

第 3 轮 NL 定制需求：把顶部的标题文案改成"我的专属客服"。
[改动文件] src/App.jsx
  - const HEADER_TITLE = "智能助手";
  + const HEADER_TITLE = "我的专属客服";
断言：源码中出现新标题文案"我的专属客服" -> 通过 ✅
构建结果：通过 ✅

多轮定制总结：全部通过 ✅
```

### 环境变量

| 变量 | 说明 |
| --- | --- |
| `OPENAI_API_KEY` | 必填其一，本实验读取此项（未配置时用 `OPENROUTER_API_KEY` 兜底） |
| `OPENAI_BASE_URL` | 可选，切换到兼容 OpenAI 协议的服务端点 |
| `MODEL` | 可选，默认 `gpt-5.6-luna` |

### 如何适配 / 扩展

- **换模型 / 换供应商**：Agent 走标准 OpenAI SDK，任何"兼容 OpenAI 协议"的服务都能接。
  只需在 `.env` 或环境变量里设置 `OPENAI_BASE_URL` + `MODEL` + 对应的 `OPENAI_API_KEY`，
  代码无需改动。例如：
  - Kimi / Moonshot：`OPENAI_BASE_URL=https://api.moonshot.cn/v1`、`MODEL=kimi-k3`；
  - 火山方舟(ARK)：`OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3`、`MODEL=<endpoint-id>`；
  - 本地 vLLM / Ollama 等：把 `OPENAI_BASE_URL` 指向本地端点即可。
- **扩展可定制范围**：默认只允许改 `src/App.jsx`、`src/theme.css`。想让 Agent 能改更多文件，
  在 `agent.py` 的 `EDITABLE_FILES` 白名单里增删路径即可（白名单越大越灵活，但改错风险也越大）。
- **新增验证轮次**：在 `demo.py` 的 `ROUNDS` 里追加 `{"requirement": ..., "verify": ...}`，
  即可把自己的定制需求纳入自动断言闭环。
- **接前端**：`frontend/` 是标准 Vite 工程，`npm run dev` 起 HMR、`npm run build` 出静态产物。
  想接自己的界面，替换 `src/*` 并同步更新白名单与 `baseline/` 快照即可。
- **接后端 / 真实 LLM 对话**：`backend/main.py` 的 `/api/chat` 默认是回声式占位回复，
  加 `--model <模型名>`（或设 `CHAT_MODEL`）即可切到真实 LLM 对话（复用上面的 `OPENAI_*` 配置）变成真实客服；
  想换成自定义业务逻辑，改写 `_llm_reply` 或 `chat` 里的返回即可。

---

## Notes / 说明

- `demo.py --quick` / `--no-build` for cheap smoke; step 3 for real HMR. / 冒烟用 `--quick`/`--no-build`；真实 HMR 见手动第 3 步。
- Commands/code/paths/env vars are identical in both language sections. / 命令、代码、路径与环境变量在中英文两侧保持一致。
