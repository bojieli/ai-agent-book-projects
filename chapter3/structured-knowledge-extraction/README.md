# Experiment 3-13: Extracting Latent Knowledge from Structured Data / 实验 3-13：从结构化数据中提取隐性知识

> Companion material for *AI Agents in Depth*, Chapter 3 — judicial case analysis pipeline: bottom-up factor discovery → structured extraction → archetype clustering → conversational advisory Agent.  
> 配套《深入理解 AI Agent》第 3 章——以司法判例分析为例：因子发现 → 结构化抽取 → 案件原型聚类 → 对话式建议 Agent。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### What this experiment is

This lab shows how an Agent can treat a knowledge base not as a “static warehouse you only retrieve from,” but as data to **read, understand, and turn into structured decision logic**—then answer questions using that logic.

Using three charge types (theft / intentional injury / fraud) as examples, it walks a four-stage pipeline:

```
Case texts ──① bottom-up factor discovery──▶ modular schema (core + per-charge extensions)
                                                    │
                                        ② structured extraction (factors via discovered schema)
                                                    │
                                        ③ per-charge clustering ──▶ case archetypes + hierarchical factor importance
                                                    │
        New facts ──④ conversational Agent (match nearest archetype, ask by importance, advise) ◀──┘
```

Unlike “rigid predefined schema + black-box regression,” the two key ideas here are: **factors are not preset—the LLM induces them freely from data**; **sentencing experience is not fit by regression, but by clustering into interpretable case archetypes**.

### Four-stage pipeline

**① Bottom-up factor discovery (`discovery.py`)**  
No fields are predefined. Case texts are batched to the LLM so it can **freely list** factors that may affect the judgment; a second LLM pass **merges, deduplicates, and normalizes** raw factors into a modular schema: `core` (cross-charge factors: surrender, compensation, guilty plea, prior record, …) + `extensions` (charge-specific: theft → amount/home invasion/gang; intentional injury → injury level/weapon/premeditation; fraud → amount/victim count). Output: `data/schema.json` (cached).

**② Structured extraction (`extractor.py`)**  
Using the discovered schema, extract “core + that charge’s extensions” per case (LLM structured output, `response_format=json_object`). Factors not mentioned in the text return `null`. Results cache to `data/extracted.jsonl`; after one full pass, re-runs are nearly free.

**③ Clustering into case archetypes + hierarchical factor importance (`archetypes.py`)**  
Factors become numeric vectors: charge / categorical factors (e.g. injury level) as one-hot (not 1/2/3, to avoid implying order); amounts / counts use `ln` scaling; binary facts as 0/1. **Within each charge**, KMeans clusters (k chosen by silhouette score) produce “case archetypes”—e.g. intentional injury may cluster into “minor injury,” “light injury,” “premeditated armed serious injury,” etc. Two levels of importance:

- **Global factor importance**: how well each factor separates all archetypes (between-cluster variance share) → global ranking  
- **Within-archetype defining factors**: factors most distinctive for each archetype vs global, plus typical sentence distribution (median / range)

Readable output: `data/archetypes.json` (with normalization params and centroids).

**④ Conversational sentencing-advice Agent (`advisor_agent.py`)**  
Uses “archetypes + hierarchical factor importance” as decision logic: extract known factors from the user’s free-form description → ask for still-missing **globally important** factors → **match the nearest case archetype** (filter by charge, then distance on known dims only) → LLM writes an interpretable suggestion grounded in that archetype’s stats (typical sentence range, defining factors), with a legal disclaimer. All sentence numbers come from archetype statistics; the LLM only explains them.

### Run

```bash
pip install -r requirements.txt
cp env.example .env        # set OPENAI_API_KEY (default model gpt-5.6-luna)
python generate_data.py    # optional: regenerate synthetic cases (repo ships data/cases.jsonl)
python demo.py             # full pipeline: discovery → extract → cluster → conversational advice
```

First run calls the LLM for factor discovery (~7 calls) and per-case extraction (~66 calls), writing `data/schema.json` and `data/extracted.jsonl`; later runs hit cache and are nearly free.

### Real run output (excerpt)

```
阶段 1 自下而上发现的 schema：
  核心通用因子: prior_record 前科 / self_surrender 自首 / compensation 赔偿 /
               guilty_plea 认罪认罚 / victim_reconciliation 谅解 ...
  扩展·盗窃罪:  amount_stolen 盗窃金额 / gang_involvement 团伙 / use_of_weapon 持械
  扩展·故意伤害罪: injury_level 伤害等级[轻微伤/轻伤二级/重伤二级] / premeditation 预谋 ...
  扩展·诈骗罪:  amount_defrauded 诈骗金额 / victim_count 受害人数 / group_crime 团伙

阶段 3 各罪名内聚类（k 由轮廓系数自动选）→ 共 12 个案件原型；全局因子重要性排序：
  1. 罪名  2. 伤害等级=重伤  3. 诈骗金额  4. 盗窃金额  5. 团伙作案  6. 是否预谋 ...
  ▸ 原型#0 [故意伤害罪] 中位 2 月：伤害等级=轻微伤(z=+2.5)
  ▸ 原型#1 [故意伤害罪] 中位 42 月：伤害等级=重伤二级(z=+3.9)、预谋(z=+1.8) —— "持械预谋重伤"型
  ▸ 原型#5 [盗窃罪]     中位 51 月：盗窃金额高、前科/累犯 100% ...

阶段 4 对话：识别到盗窃案缺金额 → 按重要性追问金额/认罪/谅解 → 补全后匹配到 原型#6
         （典型刑期中位 40 月、区间 24~50 月），并引用该原型的关键因子给出建议。
```

### Data notes

`data/cases.jsonl` is a **bundled small synthetic sample** (66 cases, 3 charges), produced by `generate_data.py` with a known sentencing formula plus noise: each line has natural-language `fact`, structured ground truth `gold`, and sentence `label_months`. The point is that **factors are written into the narrative at generation time, then “read back” from text at discovery**—discovery does not depend on the generation field list, so patterns come from the data itself.

The **intended real dataset is CAIL2018** (Chinese criminal judgments, millions of rows). Volume makes shipping it impractical; to switch, replace `generate_data.py` with a reader for CAIL `data_*.json` (lines with `fact`, `meta.accusation`, `meta.term_of_imprisonment`) into the same `cases.jsonl` shape—discovery / extract / cluster / dialogue code need not change.

### Files

| File | Role |
|------|------|
| `generate_data.py` | Synthetic multi-charge small case set |
| `discovery.py` | Stage ①: bottom-up factor discovery → modular schema |
| `extractor.py` | Stage ②: structured extraction with discovered schema (cached) |
| `archetypes.py` | Stage ③: per-charge clustering + hierarchical factor importance |
| `advisor_agent.py` | Stage ④: conversational advice Agent (nearest archetype) |
| `demo.py` | End-to-end demo entry |
| `config.py` | OpenAI client and model config |

### Limitations and disclaimer

- **Teaching only**—demonstrates the paradigm “extract latent knowledge from structured data.”
- Data is synthetic, factor set simplified; clustering cannot capture full complexity of real sentencing.
- **No output constitutes legal advice.** Real sentencing depends on statutes, judicial interpretations, local policy, and many case-specific facts—consult a qualified lawyer; do not rely on this project for legal decisions.

---

## 中文

### 本实验是什么

演示如何让 Agent 不把知识库当成“只能检索的静态仓库”，而是**先把数据读懂、从数据本身归纳出结构化的决策逻辑，再基于这套逻辑回答问题**。

以三类罪名（盗窃罪 / 故意伤害罪 / 诈骗罪）的判例为例，完整走通四段流水线：

```
判例文本 ──①自下而上因子发现──▶ 模块化 schema（核心+各罪名扩展）
                                        │
                            ②结构化抽取（用发现的 schema 抽因子）
                                        │
                            ③各罪名内聚类 ──▶ 案件原型 + 层次因子重要性
                                        │
        新案情 ──④对话 Agent（匹配最近原型、按重要性追问、给出建议）◀──┘
```

与“预定义僵化 schema + 回归黑箱”的做法相反，本实验的两个关键创新是：
**因子不预设、由 LLM 从数据里自由归纳**；**判决经验不靠回归拟合刑期、而靠聚类出可解释的案件原型**。

### 四段流水线

**① 自下而上因子发现（`discovery.py`）**  
不预先定义任何字段。把判例文本分批喂给 LLM，让它**自由列出**每一批案例中所有可能影响判决的因素；再用一次 LLM 调用把各批发现的原始因子**归并、去重、规范化**成一个模块化 schema：`core`（适用所有罪名的通用因子：自首、赔偿、认罪认罚、前科累犯……）+ `extensions`（各罪名特有扩展因子：盗窃→涉案金额/入户/团伙，故意伤害→伤害等级/持械/预谋，诈骗→金额/受害人数）。产出 `data/schema.json`（带缓存）。

**② 结构化抽取（`extractor.py`）**  
用发现出来的 schema，从每条判例抽取「核心 + 该罪名扩展」因子（LLM 结构化输出，`response_format=json_object`）。文本未提及的因子返回 `null`。抽取结果缓存到 `data/extracted.jsonl`，一次性抽取后重跑几乎免费。

**③ 聚类成案件原型 + 层次因子重要性（`archetypes.py`）**  
把因子翻译成数值向量：罪名 / 分类因子（如伤害等级）用 one-hot 开关位（不用 1/2/3，避免暗示大小关系）；金额 / 人数取 `ln` 压缩量纲；是非情节取 0/1。**在每个罪名内部**用 KMeans 聚类（k 由轮廓系数自动挑选），得到若干「案件原型」——例如故意伤害罪会自动聚出“轻微伤”、“轻伤”、“持械预谋致重伤”等典型模式。再算两级重要性：

- **全局因子重要性**：每个因子在所有原型之间的区分度（簇间方差占比）→ 全局排序；
- **原型内定义性因子**：每个原型相对全局最突出的因子 + 该原型典型刑期分布（中位 / 区间）。

产出可读、自洽的 `data/archetypes.json`（含标准化参数与簇心）。

**④ 对话式量刑建议 Agent（`advisor_agent.py`）**  
把「案件原型 + 层次因子重要性」当决策逻辑：从用户口语描述抽取已知因子 → 对照**全局因子重要性**追问仍缺失的关键因子 → 把案件**匹配到最近的案件原型**（先按罪名圈定候选，再只在已知维度上比距离）→ 让 LLM 基于该原型的统计数据（典型刑期区间、定义性因子）给出一段有判例支持、可解释的建议（附法律免责声明）。所有刑期数字均来自原型统计，LLM 只负责讲清楚。

### 运行

```bash
pip install -r requirements.txt
cp env.example .env        # 填入 OPENAI_API_KEY（默认模型 gpt-5.6-luna）
python generate_data.py    # 可选：重新生成合成判例数据集（已自带 data/cases.jsonl）
python demo.py             # 跑通 因子发现 → 抽取 → 聚类 → 对话建议 全流程
```

首次运行会调用 LLM 做因子发现（约 7 次）与逐条抽取（约 66 次），结果分别写入 `data/schema.json`、`data/extracted.jsonl`；再次运行直接命中缓存，几乎免费。

### 真实运行输出（节选）

```
阶段 1 自下而上发现的 schema：
  核心通用因子: prior_record 前科 / self_surrender 自首 / compensation 赔偿 /
               guilty_plea 认罪认罚 / victim_reconciliation 谅解 ...
  扩展·盗窃罪:  amount_stolen 盗窃金额 / gang_involvement 团伙 / use_of_weapon 持械
  扩展·故意伤害罪: injury_level 伤害等级[轻微伤/轻伤二级/重伤二级] / premeditation 预谋 ...
  扩展·诈骗罪:  amount_defrauded 诈骗金额 / victim_count 受害人数 / group_crime 团伙

阶段 3 各罪名内聚类（k 由轮廓系数自动选）→ 共 12 个案件原型；全局因子重要性排序：
  1. 罪名  2. 伤害等级=重伤  3. 诈骗金额  4. 盗窃金额  5. 团伙作案  6. 是否预谋 ...
  ▸ 原型#0 [故意伤害罪] 中位 2 月：伤害等级=轻微伤(z=+2.5)
  ▸ 原型#1 [故意伤害罪] 中位 42 月：伤害等级=重伤二级(z=+3.9)、预谋(z=+1.8) —— "持械预谋重伤"型
  ▸ 原型#5 [盗窃罪]     中位 51 月：盗窃金额高、前科/累犯 100% ...

阶段 4 对话：识别到盗窃案缺金额 → 按重要性追问金额/认罪/谅解 → 补全后匹配到 原型#6
         （典型刑期中位 40 月、区间 24~50 月），并引用该原型的关键因子给出建议。
```

### 数据说明

`data/cases.jsonl` 是**自带的小样本合成数据**（66 条，覆盖 3 类罪名），由 `generate_data.py` 用已知量刑公式加噪声生成：每条含自然语言 `fact`、结构化真值 `gold`、刑期 `label_months`。关键点是**因子在生成时被“写进”案情文本，发现阶段再从文本里把它们“读”回来**——因子发现完全不依赖生成时的字段列表，因此学到的模式来自数据本身。

**真实目标数据集是 CAIL2018**（中文刑事判决，数百万条）。因体量太大不便随仓库分发才用合成小样本；换成真实数据只需把 `generate_data.py` 换成读取 CAIL 的 `data_*.json`（每行含 `fact`、`meta.accusation`、`meta.term_of_imprisonment`），产出同结构的 `cases.jsonl` 即可，发现 / 抽取 / 聚类 / 对话四段代码无需改动。

### 文件

| 文件 | 作用 |
|------|------|
| `generate_data.py` | 合成多罪名小样本判例数据集 |
| `discovery.py` | 阶段 ①：自下而上因子发现 → 模块化 schema |
| `extractor.py` | 阶段 ②：用发现的 schema 做结构化抽取（带缓存） |
| `archetypes.py` | 阶段 ③：各罪名内聚类成案件原型 + 层次因子重要性 |
| `advisor_agent.py` | 阶段 ④：对话式量刑建议 Agent（匹配最近原型） |
| `demo.py` | 全流程演示入口 |
| `config.py` | OpenAI 客户端与模型配置 |

### 局限与免责声明

- 本项目**仅用于教学**，演示“从结构化数据中提取隐性知识”这一技术范式。
- 数据为合成、因子集经简化，聚类也无法刻画真实司法量刑的复杂性与非线性。
- **本项目的任何输出都不构成法律意见。** 真实案件量刑受法律条文、司法解释、地域政策与大量具体情节影响，请务必咨询专业律师，切勿据此做任何法律决策。

---

## Notes / 说明

### OpenRouter 通用回退 / Universal OpenRouter fallback

This experiment supports a **universal OpenRouter fallback** for its chat LLM.

- If the primary provider key (e.g. `MOONSHOT_API_KEY` / `KIMI_API_KEY` / `OPENAI_API_KEY` / `DOUBAO_API_KEY` …) is present, behavior is unchanged.
- Else if `OPENROUTER_API_KEY` is set, the chat LLM is automatically routed through OpenRouter (`https://openrouter.ai/api/v1`). Model names are mapped automatically: `gpt-*`/`o1-*` → `openai/…`, `claude-*` → `anthropic/claude-opus-4.8`, `kimi-*` → `moonshotai/kimi-k2.6`, ids already containing `/` are kept as-is, and other provider-native ids (e.g. `doubao-*`) fall back to `openai/gpt-5.6-luna`. Set `OPENROUTER_MODEL` to force a specific OpenRouter model id.
- Else a clear error lists the accepted keys.

Add `OPENROUTER_API_KEY=...` to your `.env` (see `env.example`) to enable it.
