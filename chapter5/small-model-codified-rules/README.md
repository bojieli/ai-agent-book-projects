# Experiment 5-3: Codified Rules for Small Models / 实验 5-3：小模型通过代码化知识提升执行规则的准确性

> Companion lab for *AI Agents in Depth*, Chapter 5 — τ-bench-style airline customer service: codified refund policy as CODE guard vs pure natural-language policy.  
> 《深入理解 AI Agent》第 5 章（实验 5-3）：τ-bench 航空客服对照——把退款规则从提示词搬进代码/工具。

← [Chapter 5 index / 返回第 5 章目录](../README.md)

---

## English

### One-line takeaway

Same small model, same tasks: only moving business rules from the prompt into **code/tools** raised **task success from 88% to 100%** and **policy violations from 1 to 0**—and tool-side code checks intercept wrong model beliefs in real time. Claim: **codifying business rules as guards lets a small model match large-model bare reliability on complex policy** (run a large-model baseline arm with `--big-model`; see below).

### Experiment design

A simplified airline customer-service env: simulated DB truth (flights / bookings / cabin / booking time / flight status) and one **codified refund policy** (`airline_env.is_refundable`) as the sole authority.

Refund policy (NL and code share the same source of truth):

- Basic economy (`basic_economy`) is **non-refundable** by default;
- Exception 1: full refund within **24 hours** of booking;
- Exception 2: full refund if the airline **cancels** or delays **≥ 3 hours** (major delay);
- Flexible / business cabin: full refund;
- When non-refundable: explain policy and **proactively offer alternatives** (rebook keeping the ticket, travel credit).

#### Arms

By default two arms (same small model; only difference is “codified rules or not”); `--big-model` adds a third **large-model bare baseline**:

| Arm | Model | Codified rules | Role |
|---|---|---|---|
| A `codified` | Small | ✅ triple guard | Treatment |
| B `control` | Small | ❌ pure NL | Control |
| C `control` | **Large** | ❌ pure NL | Large-model baseline (`--big-model`, optional) |

Expected relation **A ≈ C > B**: small model + codified guards (A) matches large bare (C), both clearly beat small bare (B).

#### Only difference between control and treatment (three-layer guards)

| | Control `control` | Treatment `codified` |
|---|---|---|
| ① System prompt (layer 1) | NL policy | Same NL policy |
| ② Tool description (layer 2 · checklist) | Minimal, no checklist params | Full policy listed; optional `expected_refundable` / `expected_reason` nudge model to **check before calling** |
| ③ Inside tool (layer 3 · gatekeeper) | Naive: cancel → **unconditional refund** | Codified check on **DB truth**: policy facts from DB, server clock, ignore model self-reports; illegal calls **rejected** |

Both share read-only `get_reservation` (truth; `hours_since_booking` from server clock so the model cannot mis-compute time). The clean isolation is “whether the third layer exists: in-tool codified validation.” Together they are the book’s “triple guarantee”: first two layers reduce mistakes; the third ensures mistakes do not become irreversible loss.

#### Eval tasks (8: 4 refundable / 4 non-refundable)

Normal and adversarial boundary cases: flexible fare, 24h boundary (5h / 26h), airline cancel, business cabin, user lies about flexible fare, minor delay (not major), airline schedule change (neither cancel nor ≥3h delay). See `tasks.py`.

#### Metrics (rule-based, deterministic, reproducible, zero extra LLM cost)

“State is truth”: after a run, check whether `refund_issued` happened and compare to codified policy truth:

- **Task success**: refund outcome matches policy truth;
- **Policy violations**: `over-refund (should deny but didn’t)` + `under-refund (should refund but didn’t)`;
- **Invalid tool calls**: rejected by code checks / unknown booking, etc. (error/rejected);
- **Rate of `expected_*` vs DB truth mismatch** (treatment only): quantifies “model self-belief can be wrong,” motivating server-side truth checks.

### Run

```bash
pip install -r requirements.txt
cp env.example .env   # set OPENAI_API_KEY (or env vars)
# Fallback: if OPENAI_API_KEY unset, OPENROUTER_API_KEY routes to OpenRouter
# (small model gpt-5.6-luna is gpt-5.x → prefer OpenRouter openai/gpt-5.6-luna; large baseline same)

# Offline self-test (no API key): show codified guard logic
python demo.py --selftest

# Default: all 8 cases, control vs treatment (small model both)
python demo.py

# Three-way: add large-model bare arm
python demo.py --big-model gpt-5.6-luna
```

#### CLI (`python demo.py --help` for full Chinese help)

| Flag | Description |
|---|---|
| `--mode {control,codified,both}` | Which arm(s); default `both` |
| `--task ID [ID ...]` | Cases whose `task_id` matches substring, e.g. `--task R009` |
| `--small-model NAME` | Small model (default `gpt-5.6-luna`, or `MODEL`) |
| `--big-model NAME` | Large baseline (optional; or `BIG_MODEL`) |
| `--quick` | First 4 cases only |
| `-v, --verbose` | Print each tool call |
| `--output PATH` | Write per-case results + summary JSON |
| `--selftest` | Offline codified-check demo (no API key) |

`--selftest` prints policy truth for all cases and contrasts naive tool (unconditional refund → violation when non-refundable) vs codified tool (always DB truth; block non-refundable)—fastest way to understand layer 3.

### Real results (`gpt-5.6-luna`, reasoning model temperature=1)

```
指标                  控制组                     实验组
--------------------------------------------------------------------
任务成功率               7/8 = 88%               8/8 = 100%
政策违规次数              1                       0
无效工具调用次数            0                       1        （= 1 次违规被代码拦截）

[实验组] expected_* 自报值 vs 数据库真值：
  5 次带 checklist 的取消调用中，1 次与真值不一致 —— 不一致比例 = 20%
```

> **Large-model arm (C)**: the table is the two-arm run shipped with the repo (same small model `gpt-5.6-luna`). Arm C is **run on demand**—`--big-model <your large model>` fills column C live to check **A (small+rules) ≈ C (large bare) > B (small bare)**. No pre-filled C numbers, so they match your model/time.

> **What is stable vs noisy**: core claim—success 88%→100%, violations 1→0, control’s only violation fixed on trap case `R009`—reproduces every run; secondary metrics (invalid calls 0–1, `expected_*` mismatch 0%–20%, whether R009 is self-identified at params vs rejected after cancel) vary with reasoning choices. Both paths still end non-refund correctly.

> **Model ↔ harness, two layers of value.** On weak `gpt-4o-mini`: control 6/8, treatment 8/8 (**+2**); on stronger `gpt-5.6-luna`: control 7/8, gap **+1**. Accuracy gains thin as models get stronger (like `code-for-logic` / `code-for-math`). Codified rules also give a **second value that does not vanish with stronger models: determinism and truth backstop**. Even strong models can over-refund on traps like `R009`; “always check DB, never trust model self-report” stably intercepts for 0 violations. Accuracy can be absorbed by better models; **auditability/safety backstops should not be thinned away blindly**.

Control’s only stable violation is trap case `R009` (model belief ≠ truth):

| case | Policy truth | Model belief | Control | Treatment |
|---|---|---|---|---|
| R009 (basic · airline schedule change, not either exception) | Non-refundable | Treats “airline retime = airline cause = refundable” (`expected_refundable=True`) | ❌ Over-refund | ✅ Code rejects (or self-identify at params) → explain + alternatives |

`gpt-5.6-luna` as a stronger small model already handles routine 24h cases (e.g. R003 at 5h) but can still be **over-generous** on “airline unilateral retime ≠ cancel / major delay”; server truth checks exist for that.

#### Intercept example (R009)

```
模型 checklist 自报：expected_refundable=True，expected_reason=airline_caused（认为"航司改签=航司原因=可退"）
数据库真值        ：refundable=False，原因=non_refundable_basic_economy
模型发起取消调用：{'reservation_id':'R009','expected_refundable':True,'expected_reason':'airline_caused'}
工具代码化校验返回：status=rejected, reason=policy_violation
  → "已按数据库真值校验：该预订不可退款（基础经济票，下单超过 24 小时，且无航司原因）。
     系统已拦截退款操作。请勿承诺退款，改为向乘客解释政策，并主动提议替代方案（如保留客票改签、申请旅行信用点）。"

模型最终回复用户（被拦截后自主转向）：
  "……根据退款政策，基础经济票仅在下单 24 小时内，或航班被取消、重大延误（≥3 小时）时可退款。
   目前不符合退款条件，因此无法为 R009 办理全额退款。你可以选择保留客票并申请改签到其他可用航班，
   或咨询是否能够申请旅行信用点……"
```

In **control**, the naive tool refunds—`gpt-5.6-luna` treated unilateral retime as a refund reason. NL-only complex policy is unreliable; **codify rules in tools** so wrong model judgment is still blocked and the dialogue pivots to explanation + alternatives.

### Two key observations

1. **“Params as checklist”**: in treatment, preparing `expected_*` is guided by the tool description; many boundary cases (R006 26h, R008 minor delay, R005 user lie) are **self-identified as non-refundable** before any cancel, and the agent explains + offers alternatives instead of refunding.
2. **Need for server-side truth**: self-belief is often good but still wrong on traps like R009—this run had **20% (1/5)** `expected_*` vs truth mismatch (other runs 0%–20%). Control trusts the model and turns that into over-refund. Offline: `python demo.py --selftest` injects inverted self-reports to show intercepts deterministically without a key.

### Files

- `airline_env.py`: simulated DB, codified `is_refundable`, naive vs codified tools.
- `tasks.py`: 8 eval tasks and policy truth.
- `agent.py`: OpenAI tool loop; system prompts and tool schemas for both arms (`run_agent` takes `model` for the large baseline).
- `demo.py`: arms, eval, rule scoring, N-arm table + mismatch rate + intercept samples; CLI and offline self-test.
- `requirements.txt` / `env.example`.

### Caveats

- Use `OPENAI_API_KEY` (default small model `gpt-5.6-luna`; `MODEL` / `--small-model`; large baseline `BIG_MODEL` / `--big-model`). Cost is low (~tens of calls per arm × 8 cases).
- No key: `python demo.py --selftest`.
- Reasoning models (`gpt-5.6-luna` and gpt-5/o series) reject `temperature=0`; code uses `temperature=1`, so secondary metrics can drift slightly while “treatment ≥ control and treatment 8/8 with 0 violations” stays stable.
- Server clock fixed at `2026-07-17 12:00` (`airline_env.SERVER_NOW`); all time logic uses it.

---

## 中文

### 一句话结论

同一个小模型、同一批任务，仅仅把"业务规则从提示词搬进代码/工具"，就把
**任务成功率从 88% 提升到 100%，政策违规从 1 次降到 0 次**——并能观察到工具内代码
校验实时拦截了模型的错误认知。核心主张：**把业务规则代码化为守卫，能让一个小模型在
复杂政策执行上追平大模型裸跑**（用 `--big-model` 加跑大模型基线臂即可现场验证，见下文）。

### 实验设计

精简航空客服环境：一个模拟"数据库真值"（航班/预订/舱位/下单时间/航班状态），一条
**代码化的退款政策**（`airline_env.is_refundable`）作为唯一权威判据。

退款政策（自然语言 + 代码同源）：
- 经济舱基础票（`basic_economy`）默认**不可退款**；
- 例外 1：下单 **24 小时内**可全额退款；
- 例外 2：航班被**航司取消**或**延误 ≥ 3 小时**（重大延误）可全额退款；
- 灵活票 / 商务舱可全额退款；
- 不可退款时应解释政策并**主动提议替代方案**（保留客票改签、旅行信用点）。

#### 对照臂

默认跑两臂（同一小模型，唯一差异是"是否代码化规则"）；加 `--big-model` 则再加一臂
**大模型裸跑基线**，凑成书中所述的三方对照：

| 臂 | 模型 | 代码化规则 | 角色 |
|---|---|---|---|
| A `codified` | 小模型 | ✅ 三重保障 | 实验组 |
| B `control` | 小模型 | ❌ 纯自然语言 | 控制组 |
| C `control` | **大模型** | ❌ 纯自然语言 | 大模型基线（`--big-model`，可选） |

预期关系 **A ≈ C > B**：小模型 + 代码化守卫（A）追平大模型裸跑（C），且都显著优于
小模型裸跑（B）。

#### 控制组 / 实验组的唯一差异（三层守卫对照）

| | 控制组 `control` | 实验组 `codified` |
|---|---|---|
| ① 系统提示（第一层守卫） | 自然语言政策 | 自然语言政策（相同） |
| ② 工具描述（第二层守卫·checklist） | 极简、无 checklist 参数 | 列出完整政策，并以可选 `expected_refundable` / `expected_reason` 参数引导模型**调用前逐条核对** |
| ③ 工具内部（第三层守卫·守门员） | 天真执行：被调用即取消并**无条件退款** | 基于**数据库真值**代码化校验：政策事实一律查库、时间取服务端时钟、不采信模型自报参数；违规调用直接**拒绝** |

两组共用只读工具 `get_reservation`（返回真值，`hours_since_booking` 由服务端时钟算好，
杜绝模型口算时间出错）。差异被干净地隔离为"是否有第三重保障：工具内代码化校验"。
三层守卫合起来即书中"三重保障"：前两层减少错误发生，第三层确保错误不会变成不可逆损失。

#### 评测任务（8 个，可退 4 / 不可退 4）

含正常任务与违规边界任务，覆盖：灵活票、24h 边界（5h / 26h）、航司取消、商务舱、
用户谎称灵活票、轻微延误（非重大延误）、航司改签时刻（既非取消也非 ≥3h 延误）。
见 `tasks.py`。

#### 指标与判据（规则判据，确定性、可复现、零额外成本）

"状态即真值"：一次运行结束后直接检查环境里 `refund_issued` 是否发生，与代码化政策
真值比对：
- **任务成功率**：退款结果是否符合政策真值；
- **政策违规次数**：`多退款（该拒不拒）` + `该退不退`，两个方向都算；
- **无效工具调用次数**：被代码校验拒绝 / 未知预订等返回 error/rejected 的调用；
- **`expected_*` 自报值 vs 数据库真值 不一致比例**（仅实验组）：量化"模型自我认知会
  出错"，从而验证服务端真值校验的必要性。

### 运行

```bash
pip install -r requirements.txt
cp env.example .env   # 填入 OPENAI_API_KEY（也可直接用环境变量）
# 通用兜底：未配置 OPENAI_API_KEY 时，设置 OPENROUTER_API_KEY 即自动改走 OpenRouter
#（小模型 gpt-5.6-luna 属 gpt-5.x，代码会自动优先走 OpenRouter：openai/gpt-5.6-luna；大模型基线同理）

# 离线自检（无需 API Key）：直接看代码化守卫的校验逻辑
python demo.py --selftest

# 默认：跑全部 8 个 case，控制组 vs 实验组（均用小模型）
python demo.py

# 三方对照：加跑大模型基线臂，验证"小模型+规则 ≈ 大模型裸跑"
python demo.py --big-model gpt-5.6-luna
```

#### 命令行参数（`python demo.py --help` 看完整中文帮助）

| 参数 | 说明 |
|---|---|
| `--mode {control,codified,both}` | 跑哪一组：不带/带 代码化规则，或两组都跑（默认 `both`） |
| `--task ID [ID ...]` | 只跑 `task_id` 匹配子串的 case，如 `--task R009` 直取核心拦截样例 |
| `--small-model NAME` | 小模型名（默认 `gpt-5.6-luna`，或用环境变量 `MODEL`） |
| `--big-model NAME` | 大模型基线名（可选；给定后加跑第三臂，或用环境变量 `BIG_MODEL`） |
| `--quick` | 只跑前 4 个 case（省钱快看） |
| `-v, --verbose` | 打印每步工具调用 |
| `--output PATH` | 把逐 case 结果与汇总指标写入 JSON |
| `--selftest` | 离线演示代码化校验逻辑（无需 API Key） |

`--selftest` 会对全部 case 打印政策真值，并对比"天真工具（无条件退款、不可退时即违规）"
与"代码化工具（一律以数据库真值裁决、不可退一律拦截）"，是理解第三层守卫最快的方式。

### 真实运行结果（`gpt-5.6-luna`，推理模型 temperature=1）

```
指标                  控制组                     实验组
--------------------------------------------------------------------
任务成功率               7/8 = 88%               8/8 = 100%
政策违规次数              1                       0
无效工具调用次数            0                       1        （= 1 次违规被代码拦截）

[实验组] expected_* 自报值 vs 数据库真值：
  5 次带 checklist 的取消调用中，1 次与真值不一致 —— 不一致比例 = 20%
```

> **关于大模型基线臂（C）**：上表是本仓库随附的真实两臂运行（同一小模型 `gpt-5.6-luna`）。
> 第三臂"大模型裸跑"是**按需自跑**的——加 `--big-model <你的大模型>` 即可现场得到 C 列
> 成功率填进对比表，验证 **A（小模型+规则）≈ C（大模型裸跑）> B（小模型裸跑）**。
> 这里不预填 C 的具体数字，以免与你实际使用的大模型/时刻不符。

> **哪些数字稳定、哪些会波动**：核心结论——「任务成功率 88%→100%、政策违规 1→0，
> 且控制组唯一的违规固定落在陷阱 case `R009`」——每次运行都稳定复现；而次级指标
> （实验组无效工具调用次数 0~1、`expected_*` 不一致比例 0%~20%、以及 R009 在实验组
> 究竟是"参数阶段就被模型自我识别为不可退"还是"发起取消后被代码守卫拦截"）取决于
> 推理模型每次的选择，会小幅波动，属正常现象——两条路径都稳定导向正确的不退款结果。

> **模型 ↔ 脚手架此消彼长，但这里的脚手架有「两层价值」。** 本实验在强弱两个模型上都实测过：
> 较弱模型 `gpt-4o-mini` 控制组 6/8、实验组 8/8，代码化规则把成功率拉开 **+2 题**；换成更强的 `gpt-5.6-luna`，
> 控制组自己就升到 7/8，差距收窄到 **+1 题**。可见**准确率**这层收益确实随模型变强而变薄——这与 `code-for-logic`、
> `code-for-math` 的规律一致。但代码化规则还提供了**不随模型变强而消失**的第二层价值：**确定性与真值兜底**。
> 即便强模型，仍会在 `R009` 这类政策陷阱上"该拒不拒"，而"一律查库校验、不采信模型自报"能稳定拦截、保持 0 违规。
> 换言之：靠模型能力能补的部分（准确率）会被更强的模型逐步抹平，靠脚手架才能保证的部分（确定性、可审计、安全兜底）
> 不会——**这正是判断"哪些脚手架可以随模型升级而变薄、哪些必须保留"的关键**。

控制组唯一的违规稳定发生在**模型认知与真值不符**的陷阱 case `R009`，形成清晰的因果链：

| case | 政策真值 | 模型认知 | 控制组结果 | 实验组结果 |
|---|---|---|---|---|
| R009（基础票·航司改签时刻，不属两条例外） | 不可退 | 误当"航司改签=航司原因=可退"（`expected_refundable=True`） | ❌ 多退款 | ✅ 代码校验拦截（或参数阶段自我识别），转为解释+提议替代 |

`gpt-5.6-luna` 作为较强的小模型，在 24h 边界（如 R003 下单 5h）等常规判断上已能自行答对，
但面对"航司单方面改签 ≠ 航司取消/重大延误"这类政策细节仍会**过度慷慨、该拒不拒**；服务端
真值校验（政策事实一律查库、不采信模型自报参数）正是为兜住这类认知错误而设。

#### 代码化校验拦截实例（R009）

```
模型 checklist 自报：expected_refundable=True，expected_reason=airline_caused（认为"航司改签=航司原因=可退"）
数据库真值        ：refundable=False，原因=non_refundable_basic_economy
模型发起取消调用：{'reservation_id':'R009','expected_refundable':True,'expected_reason':'airline_caused'}
工具代码化校验返回：status=rejected, reason=policy_violation
  → "已按数据库真值校验：该预订不可退款（基础经济票，下单超过 24 小时，且无航司原因）。
     系统已拦截退款操作。请勿承诺退款，改为向乘客解释政策，并主动提议替代方案（如保留客票改签、申请旅行信用点）。"

模型最终回复用户（被拦截后自主转向）：
  "……根据退款政策，基础经济票仅在下单 24 小时内，或航班被取消、重大延误（≥3 小时）时可退款。
   目前不符合退款条件，因此无法为 R009 办理全额退款。你可以选择保留客票并申请改签到其他可用航班，
   或咨询是否能够申请旅行信用点……"
```

同一个 case 在**控制组**里，天真工具直接执行了退款——`gpt-5.6-luna` 把"航司单方面改签"
当成了退款理由。可见：靠模型自然语言推理执行复杂政策并不可靠；把规则**代码化**到工具内，
即使模型判断错误也能被真值兜底拦截，并顺势转为向用户解释与提议替代方案。

### 观察到的两个关键现象（对应实验目标）

1. **"参数即 checklist"**：实验组里，模型在**准备 `expected_*` 参数**时就被工具描述的
   逐条政策引导，多数违规边界（R006 26h、R008 轻微延误、R005 用户谎称）在参数阶段就被
   模型**自主识别为不可退**，直接向用户解释并提议替代方案，根本没走到退款。
2. **服务端真值校验的必要性**：`gpt-5.6-luna` 的自我认知已相当准，但仍会在 R009 这类陷阱上出错——
   本次运行 `expected_*` 自报值与真值有 **20%（1/5）** 不一致（不同运行在 0%~20% 间波动）；若像控制组那样
   信任模型自报/自行判断，这个认知错误就会直接变成违规操作（R009 多退款）。想在无 Key 环境下确定性地
   复现"守卫拦截"，可跑 `python demo.py --selftest`（对每个 case 灌入与真值相反的自报值，演示一律被拦截）。

### 文件说明

- `airline_env.py`：模拟数据库、代码化退款政策 `is_refundable`、两组的工具实现（天真 / 代码化校验）。
- `tasks.py`：8 个评测任务及其政策真值。
- `agent.py`：OpenAI 工具调用循环，两组的系统提示与工具 schema（`run_agent` 支持 `model` 形参，供大模型基线臂复用控制组逻辑）。
- `demo.py`：组装对照臂、跑评测、规则判据评分、打印 N 臂指标对比表 + 不一致比例 + 拦截实例；含 CLI（`--mode/--task/--small-model/--big-model/--output/--selftest`）与离线自检。
- `requirements.txt` / `env.example`。

### 注意事项

- 只用 `OPENAI_API_KEY`（默认小模型 `gpt-5.6-luna`，可用 `MODEL` / `--small-model` 覆盖；
  大模型基线用 `BIG_MODEL` / `--big-model`）。成本极低（每臂 8 个 case，约几十次调用）。
- 想在无 Key 环境下理解代码化守卫，直接 `python demo.py --selftest`。
- 推理模型（`gpt-5.6-luna` 等 gpt-5/o 系列）不接受 `temperature=0`，代码会自动改用 `temperature=1`，
  故次级指标（无效工具调用数、`expected_*` 不一致比例）会小幅波动，个别 case 走的路径偶有出入属正常，
  但"实验组 ≥ 控制组、且实验组 8/8 无违规"的结论稳定成立。
- 服务端时钟固定为 `2026-07-17 12:00`（`airline_env.SERVER_NOW`），所有时间判断以它为准。

---

## Notes / 说明

- Prefer `--selftest` without a key; use `--big-model` for three-way comparison. / 无 Key 先 `--selftest`；三方对照用 `--big-model`。
- Commands/code/paths/env vars are identical in both language sections. / 命令、代码、路径与环境变量在中英文两侧保持一致。
