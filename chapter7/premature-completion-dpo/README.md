# 实验 7-17：过早结束的 DPO 修复

本项目演示实验 7-17 的完整链路：从 Coding Agent 的"过早结束"生产 bad case 出发，经过失败原因分析与轨迹前缀回归任务，构造 DPO 偏好对，做 7B+LoRA 单卡训练，最后在边界集与保留集上验证修复效果。它使用第六章建立的评估题（端到端/轨迹前缀回归任务、失败原因分析），是全书唯一一个从生产 bad case 出发的训练实验。

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

# 评估：自由生成和“完成/继续验证”候选比较都跑一遍
python evaluate.py --decision-score
# 可选 LLM 裁判复核分类结果（留证据回执）：
python evaluate.py --judge --provider ark
```

## 数据

- `data/bad_cases.json`：24 条轨迹前缀 bad case（合成但写实），覆盖四类过早结束：未跑测试就宣称完成（6）、多目标只完成一部分（6）、声称完成但验收条件未满足（6）、遇错放弃宣称不可能（6，含删测试/删断言/skip 等 reward hacking 变体）。每条含 id、category、task、trajectory_prefix、premature_claim、missing_verification；默认离线构造 24 条偏好对。
- `data/eval_boundary.json`：留出的评估集，与训练数据不同的任务和参数（训练/评估隔离，由单元测试强制检查）。其中未完成任务集 12 条：正确行为是继续验证；已完成任务保留集 8 条：正确行为是正常宣称完成，用来检测过度矫正（模型被训得永远不敢收尾）。
- `data/hidden_tests.json`：GRPO 可选分支用的端到端任务与隐藏验收脚本。

## 真实训练需要什么

- 单卡 GPU：7B 模型 + LoRA（bf16、gradient checkpointing、batch 1 × 累积 2）约需 24GB 级显存（RTX 3090/4090 或同级）；更小模型可用 `--model` 覆盖。
- HuggingFace 模型下载（默认 Qwen/Qwen2.5-7B-Instruct，约 15GB）。
- 训练产物：`output/adapter/`（仅 LoRA adapter），训练回执 `validation/<run>/training_receipt.json`（配置、数据哈希、时间戳）。

## 评估指标口径

对未完成任务集和已完成任务保留集分别让模型给出"下一步动作"，用确定性分类器（关键词/模式）判定属于"宣称完成"还是"继续验证"。此外，`--decision-score` 会固定两个候选动作，比较模型更偏好哪一个，直接测量决策边界：

- **未完成任务集的过早结束率**：训练后应下降；
- **已完成任务保留集的正常收尾率**：训练后应保持；
- **过度矫正率** = 1 − 已完成任务保留集的正常收尾率，应维持在低位。

本地 RTX PRO 6000（约 98GB 显存）实测：基座在固定候选比较的未完成任务集上选对 3/12（25.0%），已完成任务保留集 8/8（100%）；LoRA DPO（Qwen2.5-7B-Instruct，4 epochs，学习率 3e-5）后分别为 11/12（91.7%）和 8/8（100%），平均差值由 −0.2083 提升到 0.3828，保留集平均差值为 4.6904 → 2.8525。自由生成是补充诊断：过早结束 1/12 → 0/12，但正常收尾 6/8 → 0/8，说明小数据 DPO 会让模型在开放式回答里过于谨慎；因此主要结论只采用格式固定、与训练提示一致的候选比较，不能把它外推成线上总体成功率提升。完整训练回执、评估报告和迭代记录见 `validation/experiment_7_17_gpu_20260807.md` 与 `validation/`。

## 可选 RL 分支

`train_grpo_optional.py` 是可选路径（正文以 DPO 为主线）：用 TRL GRPOTrainer，奖励函数 = 隐藏验收测试——模型宣称完成则在隔离临时目录还原工作区并运行隐藏检查脚本（宣称完成且通过 +1，宣称完成但不过 −1，未宣称但执行验证动作 +0.3）。脚本真实可运行但训练成本更高，需要 GPU。

```bash
python train_grpo_optional.py   # 可选分支，默认 Qwen/Qwen2.5-7B-Instruct
```

## 可信根与诚实口径

偏好对构造、隐藏测试与评估分类器都属于模型外部的验证代码：被训练的模型不能修改它们，训练/评估数据的隔离由 `test_pipeline.py` 强制检查。评估报告只记录真实跑出的结果；LoRA adapter 文件体积较大，不随本次提交上传，训练回执中保留了模型、数据哈希和配置，按 README 命令可以重新生成。我们尝试过加入“已完成任务控制对”，它改善了开放式收尾却让未完成任务集的固定候选选择崩到 0/12，因此没有纳入最终训练集。
