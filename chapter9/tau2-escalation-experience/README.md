# 实验 9-2：从 τ²-bench 失败轨迹提炼转人工与工具使用规则

本实验对应第九章「将经验写成指令」。它检验一个具体问题：**当策略里关于
「何时转人工」只有两句原则性描述时，能否从 Agent 自己的失败轨迹中提炼出
可操作的规则，并让同一个模型在未见过的任务上表现更好。**

## 为什么用 τ²-bench

第七章已经完整解剖过 τ²-bench 的 telecom 领域，读者对它的任务结构、双控
环境和分层判分已经熟悉。本实验直接复用同一套环境，把第七章的「怎么评」
接到第九章的「评完之后怎么改」。

## 数据划分

`telecom_small`（20 条）与 `telecom`（114 条）在上游仓库中**互不相交**，
因此天然构成提炼集与迁移集，划分不是本实验事后挑的。

- **提炼集**：`telecom_small`，20 条。只用来收集失败轨迹、提炼规则。
- **迁移集**：`telecom`，114 条。三个策略臂在这里对照，规则提炼过程从未见过这些任务。

## 模型

| 角色 | 模型 | 说明 |
|---|---|---|
| 被测 Agent | `doubao-seed-1-6-flash-250615` | 故意选弱模型，留出改进空间 |
| 用户模拟器 | `doubao-seed-1-6-250615` | 三臂固定不变，避免混淆 |
| 规则提炼 | `doubao-seed-1-6-250615` | 由模型提炼，不由人手写 |

均通过火山方舟（ARK）的 OpenAI 兼容端点调用。

## 三个对照臂

| 臂 | 策略 | 说明 |
|---|---|---|
| A | 原始 `main_policy.md` | 转人工只有两句原则描述 |
| B | 原始 + v1 规则 | 提炼器只看到失败摘要与报错文本 |
| C | 原始 + v2 规则 | 提炼器额外看到 Agent 与用户各自的工具清单 |

B 与 C 的差别只在**给提炼器看什么**，提炼模型、提示词模板、失败轨迹完全相同。

## 复现

```bash
# 1. 安装 τ²-bench（不随本仓库分发）
git clone https://github.com/sierra-research/tau2-bench.git chapter7/tau2-bench
cd chapter7/tau2-bench && uv venv --python 3.12 && uv pip install -e .

# 2. 跑提炼集基线，收集失败轨迹
export VOLCENGINE_API_KEY=$ARK_API_KEY
.venv/bin/tau2 run --domain telecom --task-set-name telecom_small \
  --agent-llm volcengine/doubao-seed-1-6-flash-250615 \
  --user-llm volcengine/doubao-seed-1-6-250615 \
  --num-trials 1 --max-concurrency 10 --save-to base-train-v1

# 3. 提炼规则（两个版本）
cd ../../chapter9/tau2-escalation-experience
python3 derive_rules.py --run ../../chapter7/tau2-bench/data/simulations/base-train-v1.json \
  --out-dir validation/runs/exp9-2-tau2-escalation-v1
python3 derive_rules.py --run ../../chapter7/tau2-bench/data/simulations/base-train-v1.json \
  --tool-inventory tool_inventory.txt \
  --out-dir validation/runs/exp9-2-tau2-escalation-v2

# 4. 三臂对照（自动切换策略文件，结束后恢复）
./run_arms.sh

# 5. 汇总
python3 analyze.py
```

## 目录

- `derive_rules.py` — 从失败轨迹提炼规则，保存完整请求与回复回执
- `run_arms.sh` — 三臂运行，切换 `main_policy.md` 并记录 sha256，结束后恢复
- `analyze.py` — 通过率、转人工率、误调用用户侧工具次数、空参调用次数
- `policies/baseline_main_policy.md` — 原始策略副本
- `validation/runs/*/` — 提炼回执、生成的规则、进化后的完整策略
