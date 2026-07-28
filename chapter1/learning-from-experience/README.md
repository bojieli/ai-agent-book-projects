# Learning from Experience: RL vs LLM In-Context Learning / 从经验中学习：RL 与 LLM 上下文学习对比

> Compares tabular Q-learning with LLM in-context learning on a treasure-hunt game with hidden mechanics (Shunyu Yao, “The Second Half”).  
> 代码位于第 1 章项目树；对应书中 **实验 7-1 ★（Q-learning 在寻宝游戏中的表现）** 与 **实验 7-2 ★★（传统 RL 与 LLM Agent 的对比研究）**。

← [Chapter 1 index / 返回第 1 章目录](../README.md) · 📖 [Read Chapter 7 / 读第 7 章正文](../../book/chapter7.md)（[EN](../../book-en/chapter7.md)）

---

## English

### Overview

This experiment compares traditional Reinforcement Learning (Q-learning) with LLM-based in-context learning, replicating the key insights from Shunyu Yao's blog post ["The Second Half"](https://ysymyth.github.io/The-Second-Half/).

It demonstrates how LLMs can generalize through reasoning while traditional RL methods require extensive training to learn game mechanics. We use a text-based treasure hunt game with hidden mechanics that agents must discover through experience.

### Key Insights Being Tested

1. **Sample Efficiency**: LLMs can learn from far fewer examples than traditional RL
2. **Generalization**: LLMs use reasoning to understand patterns, while RL memorizes state-action mappings
3. **Prior Knowledge**: Language pre-training provides powerful priors for reasoning about new tasks
4. **Hidden Mechanics Discovery**: LLMs can form hypotheses and test them, while RL requires exhaustive exploration

### What You'll See

When running the LLM experiment, you'll see the **complete decision-making process**:

```
============================================================
LLM DECISION PROCESS
============================================================
📊 Experiences in memory: 15
🎮 Current room: hallway
🎯 Available actions: 8

💡 Recent successful patterns learned:
   • take red key → +5.0 reward
   • try crafting → +10.0 reward

🤔 LLM is thinking...

📝 LLM Reasoning:
----------------------------------------
  Based on my past experiences, I've learned that:
  1. The red key opens the locked door to the guard room
  2. Crafting rusty sword + magic crystal creates a silver sword
  3. The silver sword can defeat the strong guard
  
  Since I have the silver sword and I'm in the hallway...
----------------------------------------

✅ Chosen action: go north
```

This transparency shows exactly how the LLM learns and reasons, unlike the black-box nature of Q-learning.

### The Game

A text-based treasure hunt game where agents must:

- Navigate through multiple rooms
- Collect items and keys
- Defeat guards using appropriate weapons
- Discover hidden mechanics through experience

#### Hidden Mechanics (Not Revealed to Agents)

1. **Color-coded locks**: Specific colored keys open matching doors
2. **Weapon effectiveness**: Different weapons work against different enemies
3. **Crafting system**: Certain items combine to create better items
4. **Potion effects**: Temporary abilities from consuming potions

### Quick Start

#### Installation

```bash
# Navigate to the project directory
cd chapter1/learning-from-experience

# Install dependencies
pip install -r requirements.txt
```

- Q-learning runs fully offline with **no API key**.
- The LLM path needs a Moonshot/Kimi API key (or OpenRouter fallback).

#### Setting up Kimi K3 API

To run the LLM experiments, you need a Kimi (Moonshot) API key:

1. Get your API key from [Moonshot AI](https://platform.moonshot.cn/)
2. Set the environment variable:

```bash
export MOONSHOT_API_KEY="your-api-key-here"
```

Or create a `.env` file:

```bash
echo "MOONSHOT_API_KEY=your-api-key-here" > .env
```

**Universal OpenRouter fallback**: if `MOONSHOT_API_KEY` is unset but `OPENROUTER_API_KEY` is set, the LLM path routes through OpenRouter. Because Kimi models are not stably available on OpenRouter, the fallback uses `OPENROUTER_MODEL` (default `openai/gpt-5.6-luna`):

```bash
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
python quick_demo.py   # runs via OpenRouter when MOONSHOT_API_KEY is missing
```

### Running the Experiment

#### Quick Demo (See LLM Learning in Action)

```bash
python quick_demo.py
```

This shows a detailed view of how the LLM learns through reasoning, displaying:

- Complete thought process for each decision
- How experiences accumulate and influence future decisions
- The dramatic difference in learning speed vs traditional RL

#### Command-Line Interface (`experiment.py`)

`experiment.py` provides a full CLI (Chinese help text). List all flags:

```bash
python experiment.py --help
```

Main parameters:

| Parameter | Description | Default |
| --- | --- | --- |
| `--mode {both,qlearning,rl,llm}` | Which agent(s): `qlearning`/`rl` = Q-learning only (offline), `llm` = LLM Agent only, `both` = comparison | `both` |
| `--rl-episodes` | Q-learning training episodes (Experiment 7-1 uses 10000) | `10000` |
| `--llm-episodes` | LLM Agent training episodes | `20` |
| `--eval-episodes` | Greedy evaluation episodes after Q-learning | `100` |
| `--checkpoint-interval` | Learning-curve sample interval (every N episodes) | `1000` |
| `--model` | LLM model name (or `MOONSHOT_MODEL` env) | `kimi-k3` |
| `--output` | Results output directory | `results` |
| `--seed` | Random seed for reproducible Q-learning curves | unset |
| `--learning-rate` / `--discount` / `--epsilon-decay` / `--epsilon-min` | Q-learning hyperparameters | `0.2 / 0.99 / 0.9995 / 0.1` |
| `--stochastic` | Use stochastic environment | deterministic |
| `--skip-llm` | Legacy alias for `--mode qlearning` | — |

#### Q-Learning Only (Experiment 7-1, offline, no API)

```bash
python experiment.py --mode qlearning --rl-episodes 10000 --seed 42
```

Training finishes in under ~3 seconds and prints a **learning curve table** showing how the agent goes from ~0% win rate to mastery over nearly 10k episodes (see Results below).

#### Full Comparison (RL vs LLM, Experiment 7-2)

```bash
python experiment.py --mode both --model kimi-k3
```

This will:

1. Train a Q-learning agent for 10000 episodes (~3 seconds) and print its learning curve
2. Train an LLM agent for 20 episodes with detailed reasoning display
3. Evaluate both agents
4. Generate comparison plots
5. Save results to the `results/` directory

**Note**: LLM training shows the full reasoning process for the first 3 episodes and the last episode. Each LLM episode takes ~1–2 minutes (real API calls), matching the cost trade-off discussed in Experiment 7-2.

#### LLM Only

```bash
python experiment.py --mode llm --llm-episodes 20
```

#### Interactive Game Play

Test the game manually:

```python
from game_environment import TreasureHuntGame

game = TreasureHuntGame()
print(game.get_state_description())
print("Available actions:", game.get_available_actions())

# Try an action
feedback, reward, done = game.execute_action("take rusty sword")
print(f"Feedback: {feedback}")
print(f"Reward: {reward}")
```

### Experiment Results

#### Metrics Compared

1. **Sample Efficiency** — Episodes needed to achieve good performance; learning speed
2. **Performance** — Victory rate in evaluation; average rewards and episode lengths
3. **Computational Cost** — Training time; memory (Q-table size vs. experience storage); API calls for LLM

#### Visualizations

The experiment creates comparison plots showing:

- Learning curves over time
- Victory rate progression
- Sample efficiency comparison
- Key insights summary

#### Expected Results

##### Q-Learning learning curve (measured locally, `--mode qlearning --rl-episodes 10000 --seed 42`)

Measured curve (deterministic env; victory rate as a sliding window over the last 1000 episodes; full training ~3s):

| Episodes | Victory rate | Q-table states | epsilon |
| ---: | ---: | ---: | ---: |
| 1000 | 0.1% | 124 | 0.606 |
| 2000 | 0.0% | 129 | 0.368 |
| 3000 | 0.0% | 130 | 0.223 |
| 5000 | 0.0% | 132 | 0.100 |
| 7000 | 0.0% | 138 | 0.100 |
| 8000 | 0.0% | 140 | 0.100 |
| 9000 | 9.3% | 143 | 0.100 |
| 10000 | **99.8%** | 143 | 0.100 |

After training, greedy evaluation (`--eval-episodes 100`) reaches **100%** win rate, averaging 15 steps to clear. This is the core of Experiment 7-1: nearly zero wins for the first ~8000 episodes while exploring blindly; value signals need nearly 10k trials to propagate. (With free exploration variance, unseeded runs shift the inflection slightly but keep the same shape.)

##### RL vs LLM (Experiment 7-2 conclusions)

- **Q-Learning**: Needs ~10000 episodes for stable clears; treats “door / key / sword” as meaningless symbols and only explores statistically.
- **LLM In-Context**: Carries pretrained priors; often clears in the first episode within tens of steps by reasoning about game concepts.
- **Sample Efficiency**: LLM is 2–3 orders of magnitude more sample-efficient; but per-episode inference is slow (~1–2 min API), while Q-learning finishes 10000 episodes in ~3s—trade-off depends on interaction cost (see book Experiment 7-2).

### Project Structure

```
learning-from-experience/
├── game_environment.py    # Text-based game with hidden mechanics
├── rl_agent.py            # Q-learning implementation
├── llm_agent.py           # LLM with in-context learning
├── experiment.py          # Main experiment runner
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── results/               # Experiment outputs (created on run)
    └── [timestamp]/
        ├── rl_agent.pkl           # Trained Q-learning agent
        ├── llm_experiences.json   # LLM's collected experiences
        ├── experiment_results.json # Numerical results
        └── comparison_plots.png   # Visualization
```

### Technical Details

#### Q-Learning Agent

- **Algorithm**: Tabular Q-learning with ε-greedy exploration
- **State Representation**: Hashed combination of room, inventory, and game state
- **Learning Rate**: 0.2 (configurable via `--learning-rate`)
- **Discount Factor**: 0.99 (configurable via `--discount`)
- **Exploration**: ε starts at 1.0, decays by `--epsilon-decay` (0.9995) to `--epsilon-min` (0.1)

#### LLM Agent (Kimi K3)

- **Model**: `kimi-k3` (override with `--model` or `MOONSHOT_MODEL`)
- **Reasoning model**: Kimi K3 emits a chain-of-thought (`message.reasoning_content`) before its final answer (`message.content`), so the code uses a generous `max_tokens=2048` to make sure the `ACTION:` line is not truncated by the reasoning budget.
- **Learning Method**: In-context learning with experience memory (up to 50 experiences)
- **Context Management**: Stores successful and failed experiences
- **Reasoning**: Prompts LLM to reason about past experiences before acting
- **Temperature**: requested 0.7, but reasoning models (Kimi K3, GPT-5) only accept `temperature=1`, so the code auto-forces `1` for those (see `_reasoning_safe_temperature`)

### Extending the Experiment

#### Ideas for Further Research

1. **Different Games**: Try other hidden-mechanic games
2. **Hybrid Approaches**: Combine RL with LLM guidance
3. **Transfer Learning**: Test how well agents transfer to similar games
4. **Ablation Studies**: Remove reasoning prompts to isolate their impact
5. **Other LLMs**: Compare different language models

#### Modifying the Game

Edit `game_environment.py` to:

- Add new rooms and items
- Create more complex hidden mechanics
- Adjust difficulty and rewards
- Add new types of puzzles

### Educational Value

1. **The Power of Priors**: How language pre-training provides useful knowledge
2. **Reasoning vs. Memorization**: Different approaches to learning
3. **Sample Efficiency**: Why it matters for real-world applications
4. **The Second Half Thesis**: Moving from “can we solve it?” to “how efficiently?”

### References

- [The Second Half](https://ysymyth.github.io/The-Second-Half/) by Shunyu Yao
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- Original Q-learning paper: Watkins & Dayan (1992)

---

## 中文

### 概述

本实验对比传统强化学习（Q-learning）与基于 LLM 的上下文学习（in-context learning），复现 Shunyu Yao 博客 [“The Second Half”](https://ysymyth.github.io/The-Second-Half/) 中的核心洞见。

目标：展示 LLM 如何通过**推理**泛化，而传统 RL 往往需要大量试错才能学到游戏机制。我们使用带有**隐藏机制**的文本寻宝游戏，智能体只能通过经验去发现规则。

代码在 `chapter1/learning-from-experience/`，对应书中**实验 7-1** 与 **实验 7-2**（正文见第 7 章）。

### 要验证的关键洞察

1. **样本效率**：LLM 用远少于传统 RL 的样例即可学习  
2. **泛化**：LLM 用推理理解模式；RL 记忆状态-动作映射  
3. **先验知识**：语言预训练为新任务推理提供强大先验  
4. **隐藏机制发现**：LLM 可形成假设并检验；RL 往往需要穷尽式探索  

### 你会看到什么

运行 LLM 实验时，会看到**完整决策过程**：

```
============================================================
LLM DECISION PROCESS
============================================================
📊 Experiences in memory: 15
🎮 Current room: hallway
🎯 Available actions: 8

💡 Recent successful patterns learned:
   • take red key → +5.0 reward
   • try crafting → +10.0 reward

🤔 LLM is thinking...

📝 LLM Reasoning:
----------------------------------------
  Based on my past experiences, I've learned that:
  1. The red key opens the locked door to the guard room
  2. Crafting rusty sword + magic crystal creates a silver sword
  3. The silver sword can defeat the strong guard
  
  Since I have the silver sword and I'm in the hallway...
----------------------------------------

✅ Chosen action: go north
```

这种透明度展示了 LLM 如何学习与推理，有别于 Q-learning 的黑盒性质。

### 游戏说明

文本寻宝游戏，智能体需要：

- 在多个房间间导航  
- 收集物品与钥匙  
- 使用合适武器击败守卫  
- 通过经验发现隐藏机制  

#### 隐藏机制（不对智能体公开）

1. **颜色锁**：特定颜色钥匙开对应门  
2. **武器有效性**：不同武器对不同敌人有效  
3. **合成系统**：特定物品可合成更强物品  
4. **药水效果**：消耗药水获得临时能力  

### 快速开始

#### 安装

```bash
# Navigate to the project directory
cd chapter1/learning-from-experience

# Install dependencies
pip install -r requirements.txt
```

- Q-learning 完全离线，**无需任何 API Key**。  
- LLM 部分需要 Moonshot/Kimi API Key（或 OpenRouter 兜底）。  

#### 配置 Kimi K3 API

运行 LLM 实验需要 Kimi（Moonshot）API Key：

1. 从 [Moonshot AI](https://platform.moonshot.cn/) 获取 Key  
2. 设置环境变量：

```bash
export MOONSHOT_API_KEY="your-api-key-here"
```

或创建 `.env`：

```bash
echo "MOONSHOT_API_KEY=your-api-key-here" > .env
```

**通用兜底（OpenRouter）**：若未设置 `MOONSHOT_API_KEY` 但设置了 `OPENROUTER_API_KEY`，LLM 部分会自动改走 OpenRouter。由于 Kimi 模型在 OpenRouter 上不稳定可用，兜底时会使用 `OPENROUTER_MODEL`（默认 `openai/gpt-5.6-luna`）：

```bash
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
python quick_demo.py   # MOONSHOT_API_KEY 缺失时自动经 OpenRouter 运行
```

### 运行实验

#### 快速演示（观察 LLM 如何学习）

```bash
python quick_demo.py
```

会展示：

- 每一步的完整思考过程  
- 经验如何累积并影响后续决策  
- 与传统 RL 在学习速度上的巨大差异  

#### 命令行接口（`experiment.py`）

`experiment.py` 提供带中文帮助的完整 CLI：

```bash
python experiment.py --help
```

主要参数：

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--mode {both,qlearning,rl,llm}` | 运行哪种智能体：`qlearning`/`rl` 只跑 Q-learning（离线）、`llm` 只跑 LLM Agent、`both` 两者对比 | `both` |
| `--rl-episodes` | Q-learning 训练局数（实验 7-1 用 10000） | `10000` |
| `--llm-episodes` | LLM Agent 训练局数 | `20` |
| `--eval-episodes` | Q-learning 训练后贪婪评估局数 | `100` |
| `--checkpoint-interval` | 学习曲线采样间隔（每 N 局记录一次胜率/Q 表规模） | `1000` |
| `--model` | LLM 模型名（也可用 `MOONSHOT_MODEL` 环境变量） | `kimi-k3` |
| `--output` | 结果输出目录 | `results` |
| `--seed` | 随机种子，用于复现 Q-learning 学习曲线 | 不固定 |
| `--learning-rate` / `--discount` / `--epsilon-decay` / `--epsilon-min` | Q-learning 超参数 | `0.2 / 0.99 / 0.9995 / 0.1` |
| `--stochastic` | 使用随机环境 | 确定性 |
| `--skip-llm` | 兼容旧用法，等价于 `--mode qlearning` | — |

#### 仅 Q-Learning（实验 7-1，离线，无需 API）

```bash
python experiment.py --mode qlearning --rl-episodes 10000 --seed 42
```

训练不到 3 秒即可完成，并打印**学习曲线表格**，直观展现智能体如何在近万局试错中从 0% 胜率逐步学会通关（见下文“实验结果”）。

#### 完整对比（RL vs LLM，实验 7-2）

```bash
python experiment.py --mode both --model kimi-k3
```

流程：

1. 训练 Q-learning 10000 局（约 3 秒）并打印学习曲线  
2. 训练 LLM Agent 20 局，并展示详细推理  
3. 评估双方  
4. 生成对比图  
5. 结果写入 `results/`  

**说明**：LLM 训练会对前 3 局与最后一局展示完整推理。每局 LLM 约 1–2 分钟（真实 API 调用），对应书中实验 7-2 讨论的成本权衡。

#### 仅 LLM

```bash
python experiment.py --mode llm --llm-episodes 20
```

#### 交互式试玩

```python
from game_environment import TreasureHuntGame

game = TreasureHuntGame()
print(game.get_state_description())
print("Available actions:", game.get_available_actions())

# Try an action
feedback, reward, done = game.execute_action("take rusty sword")
print(f"Feedback: {feedback}")
print(f"Reward: {reward}")
```

### 实验结果

#### 对比指标

1. **样本效率** — 达到良好表现所需局数、学习速度  
2. **性能** — 评估胜率、平均回报与回合长度  
3. **计算成本** — 训练时间；内存（Q 表规模 vs. 经验存储）；LLM 的 API 调用  

#### 可视化

实验会生成对比图，包括：

- 随时间的学习曲线  
- 胜率演进  
- 样本效率对比  
- 关键洞察摘要  

#### 预期结果

##### Q-learning 学习曲线（本地实测，`--mode qlearning --rl-episodes 10000 --seed 42`）

实测学习曲线（确定性环境，胜率按最近 1000 局滑动窗口统计，整段训练约 3 秒）：

| Episodes | Victory rate | Q-table states | epsilon |
| ---: | ---: | ---: | ---: |
| 1000 | 0.1% | 124 | 0.606 |
| 2000 | 0.0% | 129 | 0.368 |
| 3000 | 0.0% | 130 | 0.223 |
| 5000 | 0.0% | 132 | 0.100 |
| 7000 | 0.0% | 138 | 0.100 |
| 8000 | 0.0% | 140 | 0.100 |
| 9000 | 9.3% | 143 | 0.100 |
| 10000 | **99.8%** | 143 | 0.100 |

训练后贪婪评估（`--eval-episodes 100`）胜率为 **100%**，平均 15 步通关。这正是实验 7-1 的核心现象：前 8000 局几乎 0% 胜率、只在盲目探索，价值信号需要近万局试错才传播到位。（因随机探索有方差，未固定 `--seed` 时各次运行的拐点会略有不同，但整体形态一致。）

##### RL vs LLM（实验 7-2 的对比结论）

- **Q-Learning**：需要近 10000 局才达到稳定通关；把“门/钥匙/剑”当作无意义符号，只能靠统计式暴力探索。  
- **LLM In-Context**：携带预训练先验，往往第一局就能在十几步内通关；靠推理理解游戏概念结构。  
- **样本效率**：LLM 高出 2–3 个数量级；但单局推理慢（API 调用 ~1–2 分钟），Q-learning 跑 10000 局只需约 3 秒——权衡取决于交互成本，详见书中实验 7-2。  

### 项目结构

```
learning-from-experience/
├── game_environment.py    # Text-based game with hidden mechanics
├── rl_agent.py            # Q-learning implementation
├── llm_agent.py           # LLM with in-context learning
├── experiment.py          # Main experiment runner
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── results/               # Experiment outputs (created on run)
    └── [timestamp]/
        ├── rl_agent.pkl           # Trained Q-learning agent
        ├── llm_experiences.json   # LLM's collected experiences
        ├── experiment_results.json # Numerical results
        └── comparison_plots.png   # Visualization
```

### 技术细节

#### Q-Learning Agent

- **算法**：表格 Q-learning + ε-贪婪探索  
- **状态表示**：房间、背包与游戏状态的哈希组合  
- **学习率**：0.2（`--learning-rate`）  
- **折扣因子**：0.99（`--discount`）  
- **探索**：ε 从 1.0 起，按 `--epsilon-decay`（0.9995）衰减到 `--epsilon-min`（0.1）  

#### LLM Agent（Kimi K3）

- **模型**：`kimi-k3`（可用 `--model` 或 `MOONSHOT_MODEL` 覆盖）  
- **推理模型**：Kimi K3 会在最终答案（`message.content`）前输出思维链（`message.reasoning_content`），因此代码使用较大的 `max_tokens=2048`，避免 `ACTION:` 行被思考预算截断。  
- **学习方式**：上下文学习 + 经验记忆（最多 50 条）  
- **上下文管理**：存储成功与失败经验  
- **推理**：行动前提示模型基于过往经验推理  
- **Temperature**：请求 0.7，但推理模型（Kimi K3、GPT-5）只接受 `temperature=1`，代码会自动强制为 `1`（见 `_reasoning_safe_temperature`）  

### 扩展实验

#### 进一步研究思路

1. **不同游戏**：尝试其他隐藏机制游戏  
2. **混合方法**：RL 与 LLM 引导结合  
3. **迁移学习**：测试向相似游戏的迁移  
4. **消融研究**：去掉推理提示以隔离其影响  
5. **其他 LLM**：对比不同语言模型  

#### 修改游戏

编辑 `game_environment.py` 可：

- 增加房间与物品  
- 设计更复杂的隐藏机制  
- 调整难度与奖励  
- 加入新类型谜题  

### 教学价值

1. **先验的力量**：语言预训练如何提供有用知识  
2. **推理 vs. 记忆**：不同学习路径  
3. **样本效率**：为何对现实任务重要  
4. **“The Second Half” 论点**：从“能否解决”转向“多高效”  

### 参考文献

- [The Second Half](https://ysymyth.github.io/The-Second-Half/) — Shunyu Yao  
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)  
- Q-learning 原文：Watkins & Dayan (1992)  

---

## Notes / 说明

- Project type: **✅ standalone runnable** (Q-learning offline; LLM needs API key).  
  项目类型：**✅ 可独立运行**（Q-learning 离线；LLM 需 API Key）。  
- For educational purposes; inspired by academic work on AI and RL.  
  教学用途，灵感来自 AI 与强化学习相关研究。  
- Feel free to add mechanics, other RL algorithms (DQN, PPO, …), providers, or richer metrics.  
  欢迎增加隐藏机制、其他 RL 算法、提供商或更完善的评估指标。  
