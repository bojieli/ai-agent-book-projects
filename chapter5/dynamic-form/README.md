# Experiment 5-9: Dynamic Form Intent Clarification / 实验 5-9：动态表单生成的意图澄清系统（★★）

> Companion lab for *AI Agents in Depth*, Chapter 5 — incomplete user intent → one self-contained HTML form with cascading logic; submit JSON back to the Agent.  
> 《深入理解 AI Agent》第 5 章：信息不完整时动态生成含级联逻辑的 HTML 表单，一次提交 JSON 交回 Agent。

← [Chapter 5 index / 返回第 5 章目录](../README.md)

---

## English

### Purpose

When user requests are **incomplete**, the Agent does not ask one field at a time—it **dynamically generates a self-contained HTML form** to clarify intent in one shot. The form has **cascading logic** (fields shown only under certain choices; dropdown options depend on another field). User **submits once**; the front end returns JSON; the Agent continues the task.

Acceptance scenario: user says “我想订一张去北京的机票” (book a flight to Beijing). Generated form includes:

- Departure city (text)
- Departure date (date picker)
- Trip type (radio: one-way / round-trip)
- **Return date (shown only for round-trip)** ← cascade ①: show/hide
- Cabin (select: economy / business / first)
- **Free checked baggage quota (options depend on cabin)** ← cascade ②: dynamic options

### Mechanism

`demo.py` validates in three steps; online and offline share the same mechanism—only “who writes the form” differs:

- **Online (default)**: send the request to OpenAI; system prompt requires a self-contained HTML (inline `<style>` + `<script>`, cascade show/hide + “submit as JSON”). Needs `OPENAI_API_KEY`.
- **Offline (`--offline`)**: no LLM; built-in flight schema **deterministically renders** the same cascading form. No API key. Form is real and browser-usable with **both** cascade types. Auto-falls back offline when `OPENAI_API_KEY` is unset.

Three steps:

1. **Generate form**: online model or offline schema → `generated_form.html` (override with `--output`).
2. **Structural validation (no browser)**: BeautifulSoup + regex ensure required fields; return-date field has “round-trip only” JS toggle; print script evidence of cascade logic.
3. **Simulated submit**: construct user JSON (round-trip), feed Agent; Agent outputs booking summary (model online; template offline)—closes “parse JSON → continue task”.

### Run

```bash
pip install -r requirements.txt
cp env.example .env                 # OPENAI_API_KEY (or OPENROUTER_API_KEY fallback)

python demo.py                      # online: OpenAI generates (needs API key)
python demo.py --offline            # offline schema render; no key
python demo.py --offline --serve    # offline + local server; browser cascade/submit
python demo.py --model gpt-5.6     # optional online model override (--offline ignores)
python demo.py --request "我想订去东京的机票"   # custom vague request
python demo.py --help
```

CLI:

| Flag | Description | Default |
| --- | --- | --- |
| `-r` / `--request TEXT` | Vague user intent | `我想订一张去北京的机票` |
| `-o` / `--output PATH` | HTML output path (relative paths resolve vs script dir) | `generated_form.html` |
| `--model NAME` | Online model override (`--offline` ignores) | env `MODEL`, else `gpt-5.6-luna` |
| `--offline` | Offline deterministic schema | off (auto-on if no key) |
| `--serve` | Local HTTP + open browser after generate | off |
| `--port N` | Port for `--serve` | `8000` |

After a successful run:

- Form at `generated_form.html`—open in a browser (or `--serve`); toggle one-way/round-trip for return-date cascade; change cabin for baggage options; submit prints summary JSON at page bottom.
- Terminal prints field checks, cascade evidence, and Agent summary of submitted JSON.

Env:

- `OPENAI_API_KEY` (required online; auto offline if missing)
- `OPENAI_BASE_URL` (optional OpenAI-compatible endpoint)
- `MODEL` (optional; default `gpt-5.6-luna`)

### Real run output

**Offline (`--offline`, deterministic, no key)**

```
[步骤 2] 结构化校验表单字段与级联逻辑：
  [PASS] 出发城市(文本输入)
  [PASS] 出发日期(日期选择器)
  [PASS] 旅行类型(单选:单程)
  [PASS] 旅行类型(单选:往返)
  [PASS] 返程日期(日期选择器)
  [PASS] 返程字段级联逻辑(仅往返显示)

[步骤 3] 解析 JSON 并继续任务，输出订票摘要：
已收到您的订票信息：上海 → 北京，出发日期 2026-08-01。
行程类型：往返，返程日期 2026-08-07。
舱位：公务舱，免费托运 2 件。
正在为您检索航班...
```

**Online (default, model `gpt-5.6-luna`)**

```
[步骤 2] 结构化校验表单字段与级联逻辑：
  [PASS] 出发城市(文本输入) / [PASS] 出发日期(日期选择器)
  [PASS] 旅行类型(单选:单程/往返) / [PASS] 返程日期(日期选择器)
  [PASS] 返程字段级联逻辑(仅往返显示)

  级联逻辑证据（脚本节选）:
    | const returnDateField = document.getElementById('return_date_field');
    | returnDateField.style.display = roundTrip ? 'block' : 'none';

[步骤 3] Agent 解析 JSON 并继续任务，输出订票摘要：
您选择的航段为：从上海出发，前往北京。出发日期为2026年8月1日，返程日期为
2026年8月7日。行程类型为往返，舱位为商务舱，携带行李数量为2件。正在为您检索航班...
```

### Limitations

- **Field naming not fully controllable (online only)**: different models/temps may vary `name`/id. System prompt asks for English names (`departure_city` / `departure_date` / `trip_type` / `return_date`); validation uses **robust keyword/attr matching** (agreed name first, then semantic/text). Occasional drift usually still passes. On `FAIL`, open `generated_form.html`. Offline schema is fully stable.
- **Cascade verification**: default is static JS parse + keywords—no real browser. For live cascade, use `--serve` or open the HTML.
- **Submit is simulated**: step 3 uses constructed JSON; real systems POST from form `submit` to a backend.
- Online quality depends on model; `temperature=0` for more stable reproduction.

---

## 中文

### 目的

验证 Agent 在面对**信息不完整**的用户请求时，不是逐条一问一答，而是**动态生成
一个自包含的 HTML 表单**来一次性澄清意图。表单内置**级联逻辑**（某些字段仅在特定
选择下才显示、某些下拉选项随另一字段动态变化），用户**一次提交**即可补全全部
信息；前端把表单汇总成 JSON 交回 Agent，Agent 解析后继续任务。

验收场景：用户输入"我想订一张去北京的机票"，Agent 生成的表单包含：
- 出发城市（文本输入）
- 出发日期（日期选择器）
- 旅行类型（单选：单程 / 往返）
- **返程日期（仅当选择"往返"时才显示）** ← 级联逻辑①：显示/隐藏
- 舱位（下拉：经济舱 / 公务舱 / 头等舱）
- **免费托运行李额度（可选项随"舱位"动态变化）** ← 级联逻辑②：动态选项

### 机制

`demo.py` 分三步验证，两种运行模式机制完全一致，只是"谁来写表单代码"不同：

- **在线（默认）**：把用户请求发给 OpenAI，system prompt 约束它输出一个自包含的
  HTML（内联 `<style>` + `<script>`，含级联显示逻辑和"提交汇总为 JSON"逻辑），
  需要 `OPENAI_API_KEY`。
- **离线（`--offline`）**：不调用 LLM，用内置机票 schema **确定性渲染**同样的级联
  表单，无需 API Key。离线渲染出的表单同样真实可用、可在浏览器打开，且含**两类**
  级联逻辑（显示/隐藏 + 下拉选项动态更新）。未设置 `OPENAI_API_KEY` 时自动回落到
  离线模式。

三步流程：

1. **生成表单**：在线让模型生成，或离线由内置 schema 渲染，保存为
   `generated_form.html`（路径可用 `--output` 覆盖）。
2. **结构化校验（不依赖浏览器）**：用 BeautifulSoup + 正则检查表单确实含要求的
  字段，且返程字段带"仅往返显示"的 JS toggle 逻辑，并打印级联逻辑的脚本证据。
3. **模拟提交**：构造一份用户提交的 JSON（往返场景），喂回 Agent；Agent 解析后
   输出订票摘要（在线交给模型，离线用确定性模板），验证"解析 JSON → 继续任务"闭环。

### 运行

```bash
pip install -r requirements.txt
cp env.example .env                 # 填入 OPENAI_API_KEY（未配置时设 OPENROUTER_API_KEY 自动改走 OpenRouter）

python demo.py                      # 在线：Agent 调 OpenAI 生成（需 API Key）
python demo.py --offline            # 离线：内置 schema 确定性渲染，无需 API Key
python demo.py --offline --serve    # 离线渲染后起本地服务，浏览器实时体验级联/提交
python demo.py --model gpt-5.6     # 可选：覆盖在线模型（--offline 下忽略）
python demo.py --request "我想订去东京的机票"   # 可选：自定义模糊请求
python demo.py --help               # 查看全部参数
```

命令行参数：

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `-r` / `--request TEXT` | 用户的模糊请求（意图） | `我想订一张去北京的机票` |
| `-o` / `--output PATH` | 生成的 HTML 输出路径（相对路径按脚本目录解析） | `generated_form.html` |
| `--model NAME` | 覆盖在线模型名（`--offline` 下忽略） | 环境变量 `MODEL`，缺省 `gpt-5.6-luna` |
| `--offline` | 离线模式：内置 schema 确定性渲染，无需 API Key | 关（未设 Key 时自动开启） |
| `--serve` | 生成后起本地 HTTP 服务并打开浏览器，真实体验级联/提交 | 关 |
| `--port N` | `--serve` 使用的端口 | `8000` |

跑通后：
- 生成的表单存为 `generated_form.html`，可**手动在浏览器打开**（或用 `--serve`
  自动打开），切换"单程/往返"即可看到返程日期字段的级联显示效果，切换舱位可看到
  行李额度下拉的动态更新，点"提交"会在页面底部打印汇总 JSON。
- 终端会打印字段校验结果、级联逻辑证据、以及 Agent 对提交 JSON 的解析摘要。

环境变量：
- `OPENAI_API_KEY`（在线模式必填；未设置时自动回落到离线模式）
- `OPENAI_BASE_URL`（可选，兼容 OpenAI 协议的第三方端点）
- `MODEL`（可选，默认 `gpt-5.6-luna`）

### 真实运行输出

**离线模式（`--offline`，确定性渲染，无需 API Key）**

```
[步骤 2] 结构化校验表单字段与级联逻辑：
  [PASS] 出发城市(文本输入)
  [PASS] 出发日期(日期选择器)
  [PASS] 旅行类型(单选:单程)
  [PASS] 旅行类型(单选:往返)
  [PASS] 返程日期(日期选择器)
  [PASS] 返程字段级联逻辑(仅往返显示)

[步骤 3] 解析 JSON 并继续任务，输出订票摘要：
已收到您的订票信息：上海 → 北京，出发日期 2026-08-01。
行程类型：往返，返程日期 2026-08-07。
舱位：公务舱，免费托运 2 件。
正在为您检索航班...
```

**在线模式（默认，模型 `gpt-5.6-luna`）**

```
[步骤 2] 结构化校验表单字段与级联逻辑：
  [PASS] 出发城市(文本输入) / [PASS] 出发日期(日期选择器)
  [PASS] 旅行类型(单选:单程/往返) / [PASS] 返程日期(日期选择器)
  [PASS] 返程字段级联逻辑(仅往返显示)

  级联逻辑证据（脚本节选）:
    | const returnDateField = document.getElementById('return_date_field');
    | returnDateField.style.display = roundTrip ? 'block' : 'none';

[步骤 3] Agent 解析 JSON 并继续任务，输出订票摘要：
您选择的航段为：从上海出发，前往北京。出发日期为2026年8月1日，返程日期为
2026年8月7日。行程类型为往返，舱位为商务舱，携带行李数量为2件。正在为您检索航班...
```

### 局限

- **字段命名不完全可控（仅在线模式）**：不同模型/温度下，生成的 `name`、id 写法
  可能不同。system prompt 已约定英文 `name` 标识（`departure_city` /
  `departure_date` / `trip_type` / `return_date`），校验也采用**鲁棒的关键词/属性
  匹配**（先按约定 name 找，找不到再退化到语义匹配 + 文本关键词），因此偶发命名
  漂移一般仍能通过。若某项 `FAIL`，可打开 `generated_form.html` 查看模型实际输出。
  离线模式由内置 schema 确定性渲染，命名/结构完全稳定，不受此限。
- **级联效果的两种验证**：默认不依赖真实浏览器，级联逻辑通过"静态解析 JS + 关键词
  匹配"来间接验证；要看真实级联点击效果，加 `--serve`（离线渲染的表单 + 本地服务）
  或手动打开生成的 HTML。
- **提交是模拟的**：步骤 3 用一份构造的 JSON 代替真实前端提交，用来验证 Agent
  的"解析 → 继续任务"环节；真实系统里这份 JSON 由表单 `submit` 回调 POST 回后端。
- 在线生成质量依赖模型；`temperature=0` 以尽量稳定复现。

---

## Notes / 说明

- Prefer `--offline` / `--serve` for cascade UX without a key. / 无 Key 用 `--offline`；体验级联加 `--serve`。
- Commands/code/paths/env vars are identical in both language sections. / 命令、代码、路径与环境变量在中英文两侧保持一致。
