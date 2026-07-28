## English

# Experiment 10-8: Voice Werewolf Agent System

Companion to Chapter 10 of "Understanding AI Agents" – Experiment 10-8: Voice Werewolf Agent System.

## Objective

Use a multi-agent Werewolf system to demonstrate a form of multi-agent collaboration that best embodies **non-shared context**—**Information Asymmetry**: different roles can only see the information they are supposed to see. The system consists of three parts:

1. **Multi-Agent**: Each player = an independent LLM Agent (Chat Completions, default `gpt-5.6-luna`), each maintaining **strictly isolated private contexts**, reasoning only based on the information they see.
2. **Information Access Control**: The **Judge** decides which information is delivered into which player Agent's context—wolves know their teammates, the Seer knows the investigation result, public speeches go to everyone. Each delivery is logged for auditing, and after the game ends, the audit table is printed and isolation is **automatically verified**.
3. **Judge Orchestration**: The Judge is a **code-driven** (non-LLM) deterministic orchestrator that manages the day/night cycle and determines the winner.

> **Voice is an optional enhancement, not required to run.** The default "text mode" is sufficient to run a complete, reproducible game and verify information isolation; add `--voice` to use OpenAI `tts-1` to synthesize public speeches into audio.

> **Offline mode (`--offline` / `--mock`): No API Key required, zero cost, fully reproducible.**
> In this mode, each player Agent uses a set of **rule-based strategies** instead of an LLM to make speech/vote/skill decisions. The key point is: the offline strategy also **only reads its own private context** (`memory`), never accessing other Agents' information—therefore, the core teaching point of information access control still holds in offline mode and can still pass audit verification.
> To see the full picture of "Judge orchestration + information isolation" at zero cost, use `python demo.py --offline`.

To control costs, this demo defaults to a **7-player game** (all played by AI, ensuring reproducibility and verifiability):
**2 Werewolves + 1 Seer + 1 Witch + 3 Villagers**; you can also customize with `--players` / `--wolves`.

## Role and Information Access Matrix

| Information Category | Who Can See (enters whose context) | Description |
|---|---|---|
| Own identity | Only oneself | Each person only knows their own role |
| **Werewolf teammate identities** | **Only all werewolves** | Werewolves know each other; good guys don't know anyone's identity |
| **Werewolf night consensus** | **Only all werewolves** | Tonight's kill target decision, only enters werewolf context |
| **Seer investigation result** | **Only the Seer** | Investigates one person's alignment each night, result is exclusive |
| **Witch night info / potion use** | **Only the Witch** | Who was killed tonight, whether to use healing/poison potion, exclusive |
| Death announcement (at dawn) | Everyone | Public information |
| Daytime speeches | Everyone | Public information, enters all player contexts |
| Voting and banishment result | Everyone | Public information, the banished player's identity is revealed |

The "God's perspective" true identity table is only printed for human observation, **not entered into any Agent context**.

## Judge Orchestration (Day/Night Cycle)

```text
Phase 0 Assign identities: privately send each person their identity; only broadcast "teammate identities" to werewolves
Each round:
  Night: Werewolves collectively choose a kill target (werewolf consensus only enters werewolf context)
         → Seer investigates one person (result only enters Seer context)
         → Witch decides whether to use healing potion to save / poison potion to kill (only enters Witch context)
         → Settle tonight's deaths
  Check win condition; if not decided, proceed to daytime
  Daytime: Announce deaths (public)
           → Public speeches in seat order (enters everyone's context)
           → All players vote to banish, announce the banished player's identity (public)
  Check win condition
Win condition: All werewolves eliminated → Good guys win; Werewolf count ≥ Good guy count → Werewolves win (simplified slaughter rule)
```

## Running

```bash
pip install -r requirements.txt
cp env.example .env        # Fill in OPENAI_API_KEY; or directly export OPENAI_API_KEY=sk-...

# Offline mode: No API Key required, rule-based decisions, zero cost, reproducible, best to run first to see the full picture
python demo.py --offline

# Online mode (LLM decisions, requires OPENAI_API_KEY)
python demo.py             # Text mode, run a complete game (default, recommended)
python demo.py --seed 7    # Change the identity distribution (reproducible)
python demo.py --voice     # Additionally use OpenAI tts-1 to synthesize public speeches into audio/ directory
python demo.py --voice --play   # Synthesize and play (macOS afplay)
python demo.py --model gpt-5.6-luna   # Override model

# General parameters (available for both offline/online)
python demo.py --offline --players 9 --wolves 3   # Customize player count and werewolf count
python demo.py --offline --max-rounds 8           # Adjust round limit
python demo.py --offline --log game.log           # Save the complete game log to a file

python demo.py --help      # View all parameters (Chinese descriptions)
```

Running will print sequentially: each phase's process (with information isolation annotations showing "who can see what") → final winner →
**Information Visibility Audit Table** → **Information Isolation Automatic Verification** (showing the private contexts of werewolf/villager/seer sides, proving each sees only their own).

## File Description

```text
voice-werewolf/
├── demo.py              # Entry point: run a complete game + print audit table + automatically verify information isolation
├── werewolf/
│   ├── roles.py         # Roles, alignments, strategy prompts for each role
│   ├── agent.py         # PlayerAgent: one Agent per player + private context + LLM/offline rule-based decision
│   ├── game.py          # Judge: Judge orchestration + information delivery primitives (with audit logging)
│   ├── audit.py         # Information visibility audit log
│   └── tts.py           # Optional voice synthesis (OpenAI tts-1)
├── requirements.txt
├── env.example
└── audio/               # Voice files synthesized when using --voice
```

The information isolation implementation is in `game.py`'s three delivery primitives: `broadcast` (enters everyone's context),
`private_send` (enters only one person's context), `wolves_send` (enters only werewolves' context); each primitive synchronously writes to the corresponding Agent's `memory` and logs in the audit "whose context it entered". Each Agent only reads its own `memory` when thinking, physically unable to see others' private information.

## Real Run Example (`python demo.py`, seed=42, gpt-5.6-luna)

Night (private actions, all with visibility annotations):

```text
【Round 1 · Night】Close your eyes, it's night.
  [Visible only to Judge + Werewolves] Werewolf P1 proposes to kill → P3
  [Visible only to Judge + Werewolves] Werewolf P6 proposes to kill → P3
  → Werewolf consensus: kill P3 (this consensus only enters werewolf context)
  [Visible only to Judge + Seer P4] Seer investigates P1 → Werewolf
  [Visible only to Judge + Witch P2] Witch learns tonight's victim: P3
  [Visible only to Judge + Witch] Witch uses healing potion to save P3
```

Daytime: Seer P4 immediately reveals and reports the investigation (Round 1 daytime, public speech enters everyone's context):

```text
  P4 (speech): I am the Seer, last night I investigated P1 and found them to be a Werewolf. The peaceful night does not affect the investigation result. Today, please prioritize voting for P1; if P1 counter-claims, ask them to explain their specific investigation information and logic.
  —— Voting Phase ——
  → Voting result: P1 is banished, their true identity is 【Werewolf】. Vote count: P1=5 votes, P4=2 votes
```

Round 2 night, the Seer investigates P6 and finds them to be a Werewolf, the Witch uses poison to kill P6. The good guys win after banishing/poisoning both werewolves (survivors: P2 Witch, P3 Villager, P5 Villager, P7 Villager).

Information Isolation Automatic Verification (excerpt):

```text
[Check 1] 『Werewolf teammate identities』only enters werewolf context: Passed ✓
   - Any non-werewolf context contains teammate identities? False (should be False)
[Check 2] 『Seer investigation result』only enters Seer(P4) context: Passed ✓
   - Any other player context contains investigation result? False (should be False)
[Check 3] Visible set of werewolf-exclusive information in audit log == werewolf set ['P1', 'P6']: Passed ✓
[Check 4] Visible set of all 『public-*』information in audit log == all players: Passed ✓
Information isolation total check: All passed ✓✓✓
```

Comparison shows: Werewolf P1's context contains "Players in the werewolf faction are: P1, P6" and "Werewolves decide to kill P3", while Villager P3's context contains **no other player's identity**, and Seer P4's context **uniquely** contains "Round 1 you investigated P1, result is 【Werewolf】". This is direct evidence of information access control in effect.

## Limitations

- **Online mode LLM decisions** default to the cheap flagship `gpt-5.6-luna` (`OPENAI_API_KEY`). **General fallback**: If `OPENAI_API_KEY` is not set but `OPENROUTER_API_KEY` is set, it automatically switches to OpenRouter and maps the model name to its namespace (`gpt-5.6-luna` → `openai/gpt-5.6-luna`); note that the `gpt-5.6` series requires organization verification for direct OpenAI connection, setting only `OPENROUTER_API_KEY` will force using OpenRouter. Note: the optional voice synthesis (`--voice`, OpenAI tts-1) still only supports `OPENAI_API_KEY`, OpenRouter has no TTS endpoint.
  To run the full process at zero cost without any API Key, use `--offline` (rule-based decisions); the offline strategy is relatively simple, speech/reasoning is less vivid than LLM, only used to demonstrate the orchestration and information isolation mechanism, not representing real game-playing ability.
- For reproducibility and cost control, this demo **is entirely played by AI**, defaulting to text mode; the book's "real human voice connection" and real-time conversation are simplified here to: Judge orchestrates speeches in seat order, AI uses text for reasoning and voting, voice is only an optional one-way TTS output (`--voice`), without real human ASR voice input and real-time interruption.
- The win condition uses the "simplified slaughter rule" (Werewolf count ≥ Good guy count → Werewolves win), without implementing advanced mechanics like Hunter, Sheriff, self-destruct, etc.; the Witch's healing potion defaults to allowing self-rescue, all can be extended as needed.
- Each game result is random, length depends on AI reasoning (usually 2-4 rounds to determine the winner); use `--seed` to reproduce or switch game scenarios. AI's deception/reasoning quality is limited by model capability.

---

## 中文

# 实验 10-8：语音狼人杀 Agent 系统

配套《深入理解 AI Agent》第 10 章「实验 10-8：语音狼人杀 Agent 系统」。

## 目的

用一个多 Agent 狼人杀系统，演示多 Agent 协作里最能体现「上下文不共享」的一种
形态——**信息权限控制（Information Asymmetry）**：不同角色天生只能看到自己该看
的信息。系统包含三部分：

1. **多 Agent**：每个玩家 = 一个独立的 LLM Agent（Chat Completions，默认
   `gpt-5.6-luna`），各自维护**严格隔离的私有上下文**，只能依据自己看到的信息推理。
2. **信息权限控制**：由**法官**决定每条信息投递进哪些玩家 Agent 的上下文——狼人
   才知道队友、预言家才知道查验结果、公开发言进所有人。每次投递都登记审计，游戏
   结束后打印审计表并**自动校验**隔离是否正确。
3. **法官编排**：法官是**代码驱动**（非 LLM）的确定性编排器，编排昼夜循环并结算胜负。

> **语音是可选增强，不是跑通的必需。** 默认「文本模式」即可完整、可复现地跑完
> 一局并验证信息隔离；加 `--voice` 才会用 OpenAI `tts-1` 把公开发言合成语音。

> **离线模式（`--offline` / `--mock`）：无需任何 API Key、零成本、完全可复现。**
> 此时每个玩家 Agent 用一套**规则策略**代替 LLM 做发言/投票/用技能的决策。关键在于：
> 离线策略同样**只读自己的私有上下文**（`memory`），绝不访问其他 Agent 的信息——
> 因此信息权限控制这一核心教学点在离线模式下依然成立、依然能通过审计校验。
> 想零成本先看清楚「法官编排 + 信息隔离」的全貌，用 `python demo.py --offline` 即可。

本 demo 为控成本默认采用 **7 人局**（全部由 AI 扮演，保证可复现可验证）：
**2 狼人 + 1 预言家 + 1 女巫 + 3 村民**；也可用 `--players` / `--wolves` 自定义。

## 角色与信息权限矩阵

| 信息类别 | 谁能看到（进入谁的上下文） | 说明 |
|---|---|---|
| 自己的身份 | 仅本人 | 每人只知道自己是什么角色 |
| **狼人队友身份** | **仅全体狼人** | 狼人互相知道队友，好人不知道任何人的身份 |
| **狼人夜间共识** | **仅全体狼人** | 今晚决定刀谁，只进狼人上下文 |
| **预言家查验结果** | **仅预言家本人** | 每晚查验一人的阵营，结果独享 |
| **女巫夜间信息 / 用药** | **仅女巫本人** | 今晚谁被刀、是否用解药/毒药，独享 |
| 死讯（天亮公布） | 所有人 | 公开信息 |
| 白天发言 | 所有人 | 公开信息，进入所有玩家上下文 |
| 投票与放逐结果 | 所有人 | 公开信息，放逐时公布出局者身份 |

「上帝视角」的真实身份表只打印给人类观察，**不进入任何 Agent 上下文**。

## 法官编排（昼夜循环）

```
阶段0 分配身份：私发每人身份；仅向狼人群发「队友身份」
每回合：
  夜晚：狼人共同选择击杀目标（狼人共识只进狼人上下文）
        → 预言家查验一人（结果只进预言家上下文）
        → 女巫决定是否解药救人 / 毒药毒人（只进女巫上下文）
        → 结算今晚死亡
  判定胜负；未分胜负则进入白天
  白天：公布死讯（公开）
        → 按座位顺序依次公开发言（进所有人上下文）
        → 全员投票放逐，公布出局者身份（公开）
  判定胜负
胜负规则：狼人全部出局 → 好人胜；狼人数 ≥ 好人数 → 狼人胜（屠边简化）
```

## 运行

```bash
pip install -r requirements.txt
cp env.example .env        # 填入 OPENAI_API_KEY；或直接 export OPENAI_API_KEY=sk-...

# 离线模式：无需 API Key，规则决策，零成本、可复现，最适合先跑通看全貌
python demo.py --offline

# 在线模式（LLM 决策，需 OPENAI_API_KEY）
python demo.py             # 文本模式跑完整一局（默认，推荐）
python demo.py --seed 7    # 换一局身份分布（可复现）
python demo.py --voice     # 额外用 OpenAI tts-1 把公开发言合成语音到 audio/
python demo.py --voice --play   # 合成并播放（macOS afplay）
python demo.py --model gpt-5.6-luna   # 覆盖模型

# 通用参数（离线/在线均可）
python demo.py --offline --players 9 --wolves 3   # 自定义人数与狼人数
python demo.py --offline --max-rounds 8           # 调整回合上限
python demo.py --offline --log game.log           # 把完整对局日志另存到文件

python demo.py --help      # 查看全部参数（中文说明）
```

运行会依次打印：每个阶段的流程（带「谁能看到什么」的信息隔离标注）→ 最终胜负 →
**信息可见性审计表** → **信息隔离自动校验**（对照展示狼人/村民/预言家三方各自的
私有上下文，证明各看各的）。

## 文件说明

```
voice-werewolf/
├── demo.py              # 入口：跑完整一局 + 打印审计表 + 自动校验信息隔离
├── werewolf/
│   ├── roles.py         # 角色、阵营、各角色策略提示词
│   ├── agent.py         # PlayerAgent：每玩家一个 Agent + 私有上下文 + LLM/离线规则决策
│   ├── game.py          # Judge：法官编排 + 信息投递原语（含审计登记）
│   ├── audit.py         # 信息可见性审计日志
│   └── tts.py           # 可选语音合成（OpenAI tts-1）
├── requirements.txt
├── env.example
└── audio/               # --voice 时合成的语音文件
```

信息隔离的落点在 `game.py` 的三个投递原语：`broadcast`（进所有人）、
`private_send`（只进一人）、`wolves_send`（只进狼人）；每个原语都同步写入对应
Agent 的 `memory` 并在审计里登记「进了谁的上下文」。Agent 每次思考只读自己的
`memory`，物理上不可能看到别人的私密信息。

## 真实运行样例（`python demo.py`，seed=42，gpt-5.6-luna）

夜晚（私密行动，均带可见范围标注）：

```
【第 1 回合 · 夜晚】天黑请闭眼。
  [仅法官+狼人可见] 狼人 P1 提议击杀 → P3
  [仅法官+狼人可见] 狼人 P6 提议击杀 → P3
  → 狼人共识：击杀 P3（此共识只进狼人上下文）
  [仅法官+预言家 P4 可见] 预言家查验 P1 → 狼人
  [仅法官+女巫 P2 可见] 女巫得知今晚被刀者：P3
  [仅法官+女巫可见] 女巫使用解药救 P3
```

白天预言家 P4 直接跳出报查杀（第 1 回合白天，公开发言进所有人上下文）：

```
  P4（发言）：我是预言家，昨晚查验P1是狼人。平安夜不影响验人结果，今天请大家优先投P1；若P1悍跳，请他解释具体验人信息和逻辑。
  —— 投票阶段 ——
  → 投票结果：P1 被放逐出局，其真实身份是【狼人】。计票：P1=5票，P4=2票
```

第 2 回合夜晚，预言家再验出 P6 是狼人、女巫用毒药毒杀 P6，好人阵营在放逐/毒杀
两只狼人后获胜（存活：P2 女巫、P3 村民、P5 村民、P7 村民）。

信息隔离自动校验（节选）：

```
[校验1] 『狼人队友身份』只进狼人上下文：通过 ✓
   - 存在非狼人上下文含队友身份？False（应为 False）
[校验2] 『预言家查验结果』只进预言家(P4)上下文：通过 ✓
   - 存在其他玩家上下文含查验结果？False（应为 False）
[校验3] 审计日志中狼人专属信息的可见集合 == 狼人集合 ['P1', 'P6']：通过 ✓
[校验4] 审计日志中所有『公开-*』信息可见集合 == 全体玩家：通过 ✓
信息隔离总校验：全部通过 ✓✓✓
```

对照可见：狼人 P1 的上下文里有「狼人阵营的玩家是：P1、P6」和「狼人决定击杀 P3」，
而村民 P3 的上下文里**没有任何他人身份**、预言家 P4 的上下文里**独有**「第 1 回合
你查验了 P1，结果为【狼人】」。这就是信息权限控制生效的直接证据。

## 局限

- **在线模式 LLM 决策**默认用便宜旗舰 `gpt-5.6-luna`（`OPENAI_API_KEY`）。**通用回退**：
  若未设置 `OPENAI_API_KEY` 但设了 `OPENROUTER_API_KEY`，则自动改走 OpenRouter，并把
  模型名映射到其命名空间（`gpt-5.6-luna` → `openai/gpt-5.6-luna`）；提示 `gpt-5.6` 系列
  直连 OpenAI 需组织验证，只填 `OPENROUTER_API_KEY` 即可强制走 OpenRouter。
  注意：可选的语音合成（`--voice`，OpenAI tts-1）仍只支持 `OPENAI_API_KEY`，OpenRouter 无 TTS 端点。
  想零成本、无 Key 跑通全流程，请用 `--offline`（规则决策）；离线策略较为简单，
  发言/推理不如 LLM 生动，仅用于演示编排与信息隔离机制，不代表真实博弈水平。
- 为可复现与控成本，本 demo **全部由 AI 扮演**、默认文本模式；书中「真人语音连线」
  与实时对话在此简化为：法官按座位顺序编排发言、AI 用文本推理投票，语音仅作可选
  的单向 TTS 输出（`--voice`），未做真人 ASR 语音输入与实时打断。
- 胜负采用「屠边简化」规则（狼人数 ≥ 好人数即狼人胜），未实现猎人、警长、
  自爆等进阶机制；女巫解药默认允许自救，均可按需扩展。
- 每局结果随机，长度取决于 AI 的推理（通常 2~4 回合分出胜负）；用 `--seed` 复现
  或切换局面。AI 的伪装/推理质量受模型能力限制。
