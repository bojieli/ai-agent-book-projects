# 实验 7-17：过早结束的 DPO 修复

本项目演示实验 7-17 的完整链路：从 Coding Agent 的"过早结束"生产 bad case 出发，经过失败归因与轨迹前缀回归任务，构造 DPO 偏好对，做 7B+LoRA 单卡训练，最后在边界集与保留集上验证修复效果。它消费第六章建立的评估资产（端到端/轨迹前缀回归任务、失败归因），是全书唯一一个从生产 bad case 出发的训练实验。

"过早结束"指 Coding Agent 在任务未真正完成时宣称完成：没跑测试就说"已完成"、多目标只完成一部分就收尾、遇到错误放弃并宣称"不可能完成"，甚至更恶劣的 reward hacking（删除失败测试后宣称全部通过）。修复思路是在"Agent 准备宣称完成"的决策边界上构造偏好对：rejected 是直接宣称完成，chosen 是先运行测试/逐条核对验收条件再下结论。

离线教学演示与机制单元测试不依赖 API key 和 GPU：

```bash
cd chapter7/premature-completion-dpo
python demo.py                          # 离线端到端演示：偏好对构造 + mock 评估
python -m pytest -q test_pipeline.py    # 机制单元测试
python build_preference_data.py         # 离线确定性路径生成 preference_pairs.jsonl
python evaluate.py --mock               # 不加载模型，演示评估指标口径
python train_dpo.py --smoke             # 数据/tokenizer/前向一次性检查（需下载小模型，无需 GPU）
```

真实训练与评估是另一条路径，需要单卡 GPU 与 HuggingFace 模型下载：

```bash
# 从仓库根目录开始：使用共享的第 7 章训练环境
uv sync --locked --python 3.12 --extra ch7
source .venv/bin/activate
cd chapter7/premature-completion-dpo
# 单项目兼容路径（兜底）：python -m pip install -r requirements.txt

# 可选：用教师模型生成 chosen（规则过滤的拒绝采样，留证据回执）
export ARK_API_KEY=your_api_key_here
python build_preference_data.py --teacher --provider ark --model doubao-seed-1-6-250615

# 单卡 LoRA DPO 训练（默认 Qwen/Qwen2.5-7B-Instruct，可用 --model 覆盖）
python train_dpo.py

# 评估：先评基线，再对比 base+adapter
python evaluate.py --base-only
python evaluate.py
# 可选 LLM 裁判复核分类结果（留证据回执）：
python evaluate.py --judge --provider ark
```

## 数据

- `data/bad_cases.json`：24 条轨迹前缀 bad case（合成但写实），覆盖四类过早结束：未跑测试就宣称完成（6）、多目标只完成一部分（6）、声称完成但验收条件未满足（6）、遇错放弃宣称不可能（6，含删测试/删断言/skip 等 reward hacking 变体）。每条含 id、category、task、trajectory_prefix、premature_claim、missing_verification。
- `data/eval_boundary.json`：held-out 评估集，与训练数据不同的任务/参数（训练/评估隔离，由单元测试强制检查）。`boundary` 12 条：任务未真正完成，正确行为是继续验证；`retention` 8 条：任务确实已完成，正确行为是正常宣称完成——retention 用来检测过度矫正（模型被训得永远不敢收尾）。
- `data/hidden_tests.json`：GRPO 可选分支用的端到端任务与隐藏验收脚本。

## 真实训练需要什么

- 单卡 GPU：7B 模型 + LoRA（bf16、gradient checkpointing、batch 1 × 累积 16）约需 24GB 级显存（RTX 3090/4090 或同级）；更小模型可用 `--model` 覆盖。
- HuggingFace 模型下载（默认 Qwen/Qwen2.5-7B-Instruct，约 15GB）。
- 训练产物：`output/adapter/`（仅 LoRA adapter），训练回执 `validation/<run>/training_receipt.json`（配置、数据哈希、时间戳）。

## 评估指标口径

对 boundary/retention 两集分别让模型给出"下一步动作"，用确定性分类器（关键词/模式）判定属于"宣称完成"还是"继续验证"：

- **boundary 过早宣称率**：训练后应下降；
- **retention 正常收尾率**：训练后应保持；
- **过度矫正率** = 1 − retention 正常收尾率，应维持在低位。

以上"应"是预期方向；实际数字需在真实 GPU 训练与评估运行后填入，本仓库不预先编造。真实 LLM 路径（教师采样、LLM 裁判）的原始请求/响应、token 用量、延迟、请求/响应哈希保存在 `validation/<run>/evidence.json`，`validation/latest.json` 指向最近一次。

## 可选 RL 分支

`train_grpo_optional.py` 是可选路径（正文以 DPO 为主线）：用 TRL GRPOTrainer，奖励函数 = 隐藏验收测试——模型宣称完成则在隔离临时目录还原工作区并运行隐藏检查脚本（宣称完成且通过 +1，宣称完成但不过 −1，未宣称但执行验证动作 +0.3）。脚本真实可运行但训练成本更高，需要 GPU。

```bash
python train_grpo_optional.py   # 可选分支，默认 Qwen/Qwen2.5-7B-Instruct
```

## 可信根与诚实口径

偏好对构造、隐藏测试与评估分类器都属于模型外部的验证代码：被训练的模型不能修改它们，训练/评估数据的隔离由 `test_pipeline.py` 强制检查。评估报告只记录真实跑出的结果；本仓库当前未包含 GPU 训练后的实测数字，README 中的预期均以"应"表述。
