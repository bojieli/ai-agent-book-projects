# 第 8 章 · 模型后训练

> 预训练/Mid-training/SFT/RL 四阶段：长上下文课程与数据构造、SFT 协议固化、RL 环境与奖励、单轮到多轮和样本效率

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter8.md)

逐实验的实现、外部源码与直接证据边界见 [验收台账](EXPERIMENT_LEDGER.md)。

## 如何阅读实验

正文用多组 text skeleton 分开说明 SFT masking、GRPO/PPO rollout、工具 token 屏蔽、RLVP 与蒸馏；完整训练框架和 CUDA 适配留在项目中：

- **Starter**：从 [cot-distillation](cot-distillation/) 先跑 2 题采集/验证 smoke，再按 generate_data.py → train_student.py → evaluate_student.py 追踪；
- **Builder**：按 [RLVP](RLVP/)、[SimpleVLA-RL](SimpleVLA-RL/) 的入口追踪 rollout、验证器和奖励字段；
- **Maintainer**：最后检查数据隔离、checkpoint/环境 hash、显存配置、失败轨迹与留出集；不需要首轮读完 verl/。

正文不要求把实验代码当作可复制的 SDK 教程；读者只需先能定位“哪段实现了正文 skeleton、哪段负责证据”。

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 8-1, 8-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | 同一确定性寻宝环境下完成 10,000 局 Q-learning、100 局贪婪评估与官方 Moonshot `kimi-k3` 第一局实测；[双臂证据](../chapter1/learning-from-experience/validation/20260730_011704/evidence.json)保留 17/17 原始 API 回执且零 fallback |
| 8-3 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind/` | ✅ | [规范训练报告](MiniMind-pretrain/validation/runs/exp8-3-training-report-20260731-v1/report.md)绑定原始与 QK-Norm + Muon 两臂在预训练、SFT、DPO 后的 49 份历史输出、8 次匿名 ARK 盲评、源码/数据/环境复现契约与完整 hash；盲评总分 3.6250 对 2.0417（+1.5833，7 胜 1 平），历史 loss 日志缺失的边界明确保留，checkpoint 不随书分发也不作为验收门槛 |
| 8-4 | [MiniMind-pretrain](MiniMind-pretrain/) | ✅ | [规范训练报告](MiniMind-pretrain/validation/runs/exp8-4-training-report-20260731-v1/report.md)保留 8 配置 × 8 图片的 64 份历史输出及 8 次真实图像感知匿名 ARK 评审，固定原版/改进版源码、数据、CLIP 与评估图片哈希；评审中原版 SFT 最高（1.9062），同 SFT 基座的 QK-Norm+Muon 两阶段均未占优。历史 revision/checkpoint 缺失被明确限定，checkpoint 不随书分发也不作为验收门槛 |
| 8-5 | [continued-pretraining](continued-pretraining/) | ✅ | [规范训练报告](continued-pretraining/validation/runs/exp8-5-training-report-20260731-v1/report.md)绑定 RTX-4090 三阶段原始输出、15 份生成、5 次匿名 ARK 盲评、源码与当前复现 revision；韩语最终阶段 +1.7777，英语下降 0.8333，泡菜事实错误明确保留，checkpoint 不随书分发也不作为验收门槛 |
| 8-6 | [sesame](sesame/) · [orpheus](orpheus/) | ✅ | [有界本地 GPU 实验](speech-sft-experiment/)已完成两条真实语音 SFT 轨道：各 60 次 LoRA 更新、留出集损失、40 个基线/微调音频、自动代理指标、哈希与失败样例；不据此声称主观音质 |
| 8-7 | [MultilingualReasoning](MultilingualReasoning/) | 🚧 | 多语言思考 SFT 实现；需训练 checkpoint 与跨语言基准前后对照才算完成 |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | [正式保留运行](../chapter8/prompt-distillation/validation/exp8-8-kimi3-smollm2-20260730/)包含 160/160 训练与 80/80 留出 Kimi K3 教师回执、真实 CUDA 训练的 SmolLM2-135M-Instruct LoRA checkpoint，并通过 8/8 门禁；留出集教师 100%、基线 0%、训练后学生 95% |
| 8-9 | [cot-distillation](cot-distillation/) | ✅ | 24/24 Kimi K3 教师轨迹均已完成并经规则过滤，23 条进入 SFT；真实 CUDA checkpoint 与同题三臂对照已保留。学生 2/24 对基线 1/24 的提升不显著（p=1.0），作为负结果如实报告 |
| 8-10 | [AdaptThink 配套说明](AdaptThink/) · `AdaptThink-original/` | ✅ | [历史训练报告](AdaptThink/TRAINING_REPORT.md)记录公开 W&B 主运行 `wubbn5tj`：8×H100，step 300 三基准响应长度均显著下降，但 AIME mean@16 下降 0.42 pp；运行继续至 step 410 后崩溃，checkpoint 不随书分发，且未保留独立 checkpoint 评估回执 |
| 8-11 | `SFTvsRL/` | 📖 | `bojieli/SFTvsRL` 的 GeneralPoints-L/VL：同预算 SFT 与 PPO 的 ID/OOD 记忆—泛化对照 |
| 8-12 | [SpatialReasoning 配套说明](SpatialReasoning/) · `SFTvsRL/` | 📖 | 同一 `bojieli/SFTvsRL` checkout 的 V-IRL-L/VL 训练与跨城市/规则 OOD 评估，不是独立 SpatialReasoning 代码仓库 |
| 8-13 | [SimpleVLA-RL 配套说明](SimpleVLA-RL/) · `SimpleVLA-RL/SimpleVLA-RL/` | 📖 | `PRIME-RL/SimpleVLA-RL` 主仓与内嵌 `verl/` 已固定；OpenVLA-OFT、LIBERO/RoboTwin、checkpoint、Flash Attention、CUDA/driver 和 simulator assets 仍未形成经验证的完整依赖锁 |
| 8-14 | [retool 配套说明](retool/) · `verl/` · `SandboxFusion/` | 📖 | ReTool 配方来自 `bojieli/verl`，实时代码执行依赖 `bojieli/SandboxFusion`；不是一个名为 `retool` 的独立源码仓库 |
| 8-15 | [AWorld-train 配套说明](AWorld-train/) · `AWorld/` | 📖 | `bojieli/AWorld` 中的 GAIA MCP 沙盒与训练入口，`bojieli/verl` 为训练后端 |
| 8-16 | [RLVP 配套说明](RLVP/) · `RLVP/rlvp/` | 📖 | 完整训练/评估代码来自固定到 `1ad30bc…` 的 `19PINE-AI/rlvp`；当前 checkout 缺失，训练未运行 |
| 8-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | 从"过早结束" bad case 到 DPO 修复的完整链路：bad case → 偏好对 → 7B+LoRA 单卡训练 → 未完成任务集与已完成任务保留集验证；本地 RTX PRO 6000 已完成训练，固定候选比较中未完成任务集选对率 25.0% → 91.7%，保留集保持 100% |
| 8-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | 中文弯引号作用域 Bad Case：人工审计合成数据 + 显式 Skill 正反规则 → Qwen3-8B bf16 LoRA SFT → 9 种代码语言和 10 种文章体裁回归；[manifest](curly-quote-sft/validation/manifest.json)；RTX PRO 6000 真实训练已完成，1024/256/256（训练/留出/边界），适配后 exact 96.9%/97.7%，保护区保持 100% |
| 8-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | `old_string`/特殊字符串精确复制 Bad Case：未见随机字符串、相似字符串选择和工具 JSON 参数 → Qwen3-8B bf16 LoRA SFT；[manifest](exact-copy-sft/validation/manifest.json)；RTX PRO 6000 真实训练已完成，1024/256/256（训练/留出/边界），byte-exact 基座 37.5%→适配 78.9%，边界 80.1%；另有 Qwen3/Qwen2.5/Mistral tokenizer 审计 |
| — | `verl/` | 📖 | 为 LLM RLHF 设计的高效 RL 框架，支持 PPO/GRPO/DAPO 等 |
| — | [Intuitor](Intuitor/) | ✅ | 训练模型的直觉推理，快速做出合理判断而不依赖详细思考链 |
| — | `tinker-cookbook/` | 📖 | 收集各种模型训练的实用技巧与最佳实践 |

## 外部训练实验复现锚点

下表严格对应正文实验编号。SHA 来自 2026-07-30 当前工作区 checkout，或同日只读上游审计。8-3、8-4、8-5 有各自的 checkpoint-free 历史训练报告验收包；8-10 提供直接链接公开 W&B 的训练报告。固定 revision 属于未来复现说明，不冒充历史训练时的精确 checkout。其余标为未完成的条目仍只完成来源/路径/入口静态核验，**没有启动训练或外部评测**。

| 实验 | 权威上游 → 本地源码路径 | 固定提交 | 已核对入口 |
| :--: | --- | --- | --- |
| 8-3 | [`bojieli/minimind`](https://github.com/bojieli/minimind) → `chapter8/MiniMind-pretrain/minimind` | `8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795` | `trainer/train_pretrain_muon.py` → `trainer/train_full_sft_muon.py` → `trainer/train_dpo.py`；评估 `eval_model.py` |
| 8-4 | [`bojieli/minimind-v`](https://github.com/bojieli/minimind-v) → `chapter8/MiniMind-pretrain/minimind-v` | `ead791c530fa5f9a3549dbfe9e11ec732d18d2e5` | `trainer/train_pretrain_vlm_muon.py` → `trainer/train_sft_vlm_muon.py`；评估 `eval_vlm.py` |
| 8-10 | [`bojieli/AdaptThink`](https://github.com/bojieli/AdaptThink) → `chapter8/AdaptThink-original` | `0033ad172dd53ac64004b763477407014f21b838`（W&B 历史提交 `9e588202…` 的直接子提交；三个入口文件字节一致） | `bash scripts/preprocess_dataset.sh` → `bash scripts/run_adapt_think_1.5b_deepscaler_16k_delta0.05_btz128_lr2e-6.sh` → `bash scripts/run_eval_verl_hf.sh`；训练命名产生 `-fl-`，评估却硬编码 `-fl4096` 且少一层目录，复现时需手工修正路径 |
| 8-11 | [`bojieli/SFTvsRL`](https://github.com/bojieli/SFTvsRL) → `chapter8/SFTvsRL` | `fef0a4a3367260a0934be1e40b01e4021698e023` | GeneralPoints：`bash scripts/gp_training/language_train.sh` / `bash scripts/gp_training/vl_train.sh`；评估在 `scripts/gp_evaluation/*.sh` |
| 8-12 | 同一 [`bojieli/SFTvsRL`](https://github.com/bojieli/SFTvsRL) → `chapter8/SFTvsRL`；说明在 `chapter8/SpatialReasoning` | `fef0a4a3367260a0934be1e40b01e4021698e023` | V-IRL：`bash scripts/virl_training/vl_train.sh`；ID/规则 OOD/视觉 OOD 分别运行 `scripts/virl_evaluation/vl_{indist,rule_ood,visual_ood}_eval.sh` |
| 8-13 | [论文](https://arxiv.org/abs/2509.09674) · [`PRIME-RL/SimpleVLA-RL`](https://github.com/PRIME-RL/SimpleVLA-RL/tree/7c51662df27b586f9e8a1ab35fcf849f2b8852f9) → `chapter8/SimpleVLA-RL/SimpleVLA-RL` | 主仓及内嵌 `verl/`：`7c51662df27b586f9e8a1ab35fcf849f2b8852f9`；外部栈没有作者给出的兼容 SHA，详见[依赖契约](SimpleVLA-RL/README.md#dependency-contract-and-lock-state) | `bash examples/run_openvla_oft_rl_libero.sh`；RoboTwin2 为 `bash examples/run_openvla_oft_rl_twin2.sh`；两者的 `SFT_MODEL_PATH` 仍是占位符 |
| 8-14 | [`bojieli/verl`](https://github.com/bojieli/verl) → `chapter8/verl`；[`bojieli/SandboxFusion`](https://github.com/bojieli/SandboxFusion) → `chapter8/SandboxFusion` | veRL：`1593fc3a8cf894debdc3dece2a23ed739c282789`；SandboxFusion：`4a0d573ebd64c98234c190a9d1d49e4276199a0c` | 启动沙箱 `make run-online`；在 veRL 根目录运行 `bash recipe/retool/run_qwen2-32b_dapo.sh` |
| 8-15 | [`bojieli/AWorld`](https://github.com/bojieli/AWorld) → `chapter8/AWorld`；训练后端 `chapter8/verl` | AWorld：`a52d61d6d483e66b22ef16970eae5bbf4f4ab2ec`；veRL：`1593fc3a8cf894debdc3dece2a23ed739c282789` | `cd chapter8/AWorld/env && bash run-local.sh`；数据准备后在 `train/examples/train_gaia_with_aworld_verl` 运行 `bash run.sh` |
| 8-16 | [`19PINE-AI/rlvp`](https://github.com/19PINE-AI/rlvp) → `chapter8/RLVP/rlvp` | `1ad30bc7e338911fb733739393d92c420f4d8bee` | 规则/credit 测试 → `scripts/phase0_baseline.py` → `scripts/run_all.sh` → `scripts/eval_checkpoint.py`；完整训练需 CUDA |

从仓库根目录获取当前可固定的版本：

```bash
git clone https://github.com/bojieli/AdaptThink.git chapter8/AdaptThink-original && git -C chapter8/AdaptThink-original checkout --detach 0033ad172dd53ac64004b763477407014f21b838
git clone https://github.com/bojieli/SFTvsRL.git chapter8/SFTvsRL && git -C chapter8/SFTvsRL checkout --detach fef0a4a3367260a0934be1e40b01e4021698e023
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git chapter8/SimpleVLA-RL/SimpleVLA-RL && git -C chapter8/SimpleVLA-RL/SimpleVLA-RL checkout --detach 7c51662df27b586f9e8a1ab35fcf849f2b8852f9
git clone https://github.com/bojieli/verl.git chapter8/verl && git -C chapter8/verl checkout --detach 1593fc3a8cf894debdc3dece2a23ed739c282789
git clone https://github.com/bojieli/AWorld.git chapter8/AWorld && git -C chapter8/AWorld checkout --detach a52d61d6d483e66b22ef16970eae5bbf4f4ab2ec
```

以下四个源码目录当前缺失，但不可变版本已经固定。每组命令都显式 fetch、detached checkout，并核对 `rev-parse HEAD`。8-3 的 checkpoint-free 训练报告已按本书训练实验政策验收；对其他实验而言，源码就绪仍不等于实验完成：

```bash
git clone https://github.com/bojieli/minimind.git chapter8/MiniMind-pretrain/minimind
git -C chapter8/MiniMind-pretrain/minimind fetch origin 8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795
git -C chapter8/MiniMind-pretrain/minimind checkout --detach 8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795
git -C chapter8/MiniMind-pretrain/minimind rev-parse HEAD
test "$(git -C chapter8/MiniMind-pretrain/minimind rev-parse HEAD)" = "8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795"

git clone https://github.com/bojieli/minimind-v.git chapter8/MiniMind-pretrain/minimind-v
git -C chapter8/MiniMind-pretrain/minimind-v fetch origin ead791c530fa5f9a3549dbfe9e11ec732d18d2e5
git -C chapter8/MiniMind-pretrain/minimind-v checkout --detach ead791c530fa5f9a3549dbfe9e11ec732d18d2e5
git -C chapter8/MiniMind-pretrain/minimind-v rev-parse HEAD
test "$(git -C chapter8/MiniMind-pretrain/minimind-v rev-parse HEAD)" = "ead791c530fa5f9a3549dbfe9e11ec732d18d2e5"

git clone https://github.com/19PINE-AI/rlvp.git chapter8/RLVP/rlvp
git -C chapter8/RLVP/rlvp fetch origin 1ad30bc7e338911fb733739393d92c420f4d8bee
git -C chapter8/RLVP/rlvp checkout --detach 1ad30bc7e338911fb733739393d92c420f4d8bee
git -C chapter8/RLVP/rlvp rev-parse HEAD
test "$(git -C chapter8/RLVP/rlvp rev-parse HEAD)" = "1ad30bc7e338911fb733739393d92c420f4d8bee"

git clone https://github.com/bojieli/SandboxFusion.git chapter8/SandboxFusion
git -C chapter8/SandboxFusion fetch origin 4a0d573ebd64c98234c190a9d1d49e4276199a0c
git -C chapter8/SandboxFusion checkout --detach 4a0d573ebd64c98234c190a9d1d49e4276199a0c
git -C chapter8/SandboxFusion rev-parse HEAD
test "$(git -C chapter8/SandboxFusion rev-parse HEAD)" = "4a0d573ebd64c98234c190a9d1d49e4276199a0c"
```

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 已有实现，但训练或正文验收证据尚未完整 |
