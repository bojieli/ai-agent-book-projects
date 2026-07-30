# 第 7 章 · 模型后训练

> 预训练/SFT/RL 三阶段：何时选 SFT、何时选 RL，工具调用内化、样本效率

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter7.md)

逐实验的实现、外部源码与直接证据边界见 [验收台账](EXPERIMENT_LEDGER.md)。

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 7-1, 7-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | 同一确定性寻宝环境下完成 10,000 局 Q-learning、100 局贪婪评估与官方 Moonshot `kimi-k3` 第一局实测；[双臂证据](../chapter1/learning-from-experience/validation/20260730_011704/evidence.json)保留 17/17 原始 API 回执且零 fallback |
| 7-3 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind/` | 📖 | 配套说明 + 固定到 `8bdc5d9…` 的外部 `bojieli/minimind`；当前 checkout 缺失，训练未运行 |
| 7-4 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind-v/` | 📖 | 配套说明 + 固定到 `ead791c…` 的外部 `bojieli/minimind-v`；当前 checkout 缺失，训练未运行 |
| 7-5 | [continued-pretraining](continued-pretraining/) | ✅ | 在特定领域数据上持续预训练，提升目标领域表现 |
| 7-6 | [sesame](sesame/) · [orpheus](orpheus/) | 🚧 | 两条真实语音 SFT 轨道：副语言标记建模与跨句音色一致；需训练后 adapter、音频和人工/自动对照证据才算完成 |
| 7-7 | [MultilingualReasoning](MultilingualReasoning/) | 🚧 | 多语言思考 SFT 实现；需训练 checkpoint 与跨语言基准前后对照才算完成 |
| 7-8 | [prompt-distillation](../chapter8/prompt-distillation/) | 🚧 | 教师提示/响应生成、学生训练与质量-成本对照的跨章实现；仅生成示例或提示机制不构成完成 |
| 7-9 | [cot-distillation](cot-distillation/) | 🚧 | 已保存并规则过滤真实 Kimi K3 CoT；现已补齐无 mock 的学生 SFT、同题三臂对照、配对显著性与反思/回溯/验算验收代码，但当前主机尚无 CUDA checkpoint，不能宣称蒸馏提升 |
| 7-10 | [AdaptThink 配套说明](AdaptThink/) · `AdaptThink-original/` | 📖 | `bojieli/AdaptThink` 外部训练代码；让模型按难度选择 Thinking/NoThinking |
| 7-11 | `SFTvsRL/` | 📖 | `bojieli/SFTvsRL` 的 GeneralPoints-L/VL：同预算 SFT 与 PPO 的 ID/OOD 记忆—泛化对照 |
| 7-12 | [SpatialReasoning 配套说明](SpatialReasoning/) · `SFTvsRL/` | 📖 | 同一 `bojieli/SFTvsRL` checkout 的 V-IRL-L/VL 训练与跨城市/规则 OOD 评估，不是独立 SpatialReasoning 代码仓库 |
| 7-13 | [SimpleVLA-RL 配套说明](SimpleVLA-RL/) · `SimpleVLA-RL/SimpleVLA-RL/` | 📖 | `PRIME-RL/SimpleVLA-RL` 主仓与内嵌 `verl/` 已固定；OpenVLA-OFT、LIBERO/RoboTwin、checkpoint、Flash Attention、CUDA/driver 和 simulator assets 仍未形成经验证的完整依赖锁 |
| 7-14 | [RLVP 配套说明](RLVP/) · `RLVP/rlvp/` | 📖 | 完整训练/评估代码来自固定到 `1ad30bc…` 的 `19PINE-AI/rlvp`；当前 checkout 缺失，训练未运行 |
| 7-15 | [retool 配套说明](retool/) · `verl/` · `SandboxFusion/` | 📖 | ReTool 配方来自 `bojieli/verl`，实时代码执行依赖 `bojieli/SandboxFusion`；不是一个名为 `retool` 的独立源码仓库 |
| 7-16 | [AWorld-train 配套说明](AWorld-train/) · `AWorld/` | 📖 | `bojieli/AWorld` 中的 GAIA MCP 沙盒与训练入口，`bojieli/verl` 为训练后端 |
| — | `verl/` | 📖 | 为 LLM RLHF 设计的高效 RL 框架，支持 PPO/GRPO/DAPO 等 |
| — | [Intuitor](Intuitor/) | ✅ | 训练模型的直觉推理，快速做出合理判断而不依赖详细思考链 |
| — | `tinker-cookbook/` | 📖 | 收集各种模型训练的实用技巧与最佳实践 |

## 外部训练实验复现锚点

下表严格对应正文实验编号。SHA 来自 2026-07-30 当前工作区 checkout，或同日只读上游审计；这里只完成来源/路径/入口静态核验，**没有启动任何训练或外部评测**。

| 实验 | 权威上游 → 本地源码路径 | 固定提交 | 已核对入口 |
| :--: | --- | --- | --- |
| 7-3 | [`bojieli/minimind`](https://github.com/bojieli/minimind) → `chapter7/MiniMind-pretrain/minimind` | `8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795` | `trainer/train_pretrain_muon.py` → `trainer/train_full_sft_muon.py` → `trainer/train_dpo.py`；评估 `eval_model.py` |
| 7-4 | [`bojieli/minimind-v`](https://github.com/bojieli/minimind-v) → `chapter7/MiniMind-pretrain/minimind-v` | `ead791c530fa5f9a3549dbfe9e11ec732d18d2e5` | `trainer/train_pretrain_vlm_muon.py` → `trainer/train_sft_vlm_muon.py`；评估 `eval_vlm.py` |
| 7-10 | [`bojieli/AdaptThink`](https://github.com/bojieli/AdaptThink) → `chapter7/AdaptThink-original` | `0033ad172dd53ac64004b763477407014f21b838` | `bash scripts/preprocess_dataset.sh` → `bash scripts/run_adapt_think_1.5b_deepscaler_16k_delta0.05_btz128_lr2e-6.sh` → `bash scripts/run_eval_verl_hf.sh` |
| 7-11 | [`bojieli/SFTvsRL`](https://github.com/bojieli/SFTvsRL) → `chapter7/SFTvsRL` | `fef0a4a3367260a0934be1e40b01e4021698e023` | GeneralPoints：`bash scripts/gp_training/language_train.sh` / `bash scripts/gp_training/vl_train.sh`；评估在 `scripts/gp_evaluation/*.sh` |
| 7-12 | 同一 [`bojieli/SFTvsRL`](https://github.com/bojieli/SFTvsRL) → `chapter7/SFTvsRL`；说明在 `chapter7/SpatialReasoning` | `fef0a4a3367260a0934be1e40b01e4021698e023` | V-IRL：`bash scripts/virl_training/vl_train.sh`；ID/规则 OOD/视觉 OOD 分别运行 `scripts/virl_evaluation/vl_{indist,rule_ood,visual_ood}_eval.sh` |
| 7-13 | [论文](https://arxiv.org/abs/2509.09674) · [`PRIME-RL/SimpleVLA-RL`](https://github.com/PRIME-RL/SimpleVLA-RL/tree/7c51662df27b586f9e8a1ab35fcf849f2b8852f9) → `chapter7/SimpleVLA-RL/SimpleVLA-RL` | 主仓及内嵌 `verl/`：`7c51662df27b586f9e8a1ab35fcf849f2b8852f9`；外部栈没有作者给出的兼容 SHA，详见[依赖契约](SimpleVLA-RL/README.md#dependency-contract-and-lock-state) | `bash examples/run_openvla_oft_rl_libero.sh`；RoboTwin2 为 `bash examples/run_openvla_oft_rl_twin2.sh`；两者的 `SFT_MODEL_PATH` 仍是占位符 |
| 7-14 | [`19PINE-AI/rlvp`](https://github.com/19PINE-AI/rlvp) → `chapter7/RLVP/rlvp` | `1ad30bc7e338911fb733739393d92c420f4d8bee` | 规则/credit 测试 → `scripts/phase0_baseline.py` → `scripts/run_all.sh` → `scripts/eval_checkpoint.py`；完整训练需 CUDA |
| 7-15 | [`bojieli/verl`](https://github.com/bojieli/verl) → `chapter7/verl`；[`bojieli/SandboxFusion`](https://github.com/bojieli/SandboxFusion) → `chapter7/SandboxFusion` | veRL：`1593fc3a8cf894debdc3dece2a23ed739c282789`；SandboxFusion：`4a0d573ebd64c98234c190a9d1d49e4276199a0c` | 启动沙箱 `make run-online`；在 veRL 根目录运行 `bash recipe/retool/run_qwen2-32b_dapo.sh` |
| 7-16 | [`bojieli/AWorld`](https://github.com/bojieli/AWorld) → `chapter7/AWorld`；训练后端 `chapter7/verl` | AWorld：`a52d61d6d483e66b22ef16970eae5bbf4f4ab2ec`；veRL：`1593fc3a8cf894debdc3dece2a23ed739c282789` | `cd chapter7/AWorld/env && bash run-local.sh`；数据准备后在 `train/examples/train_gaia_with_aworld_verl` 运行 `bash run.sh` |

从仓库根目录获取当前可固定的版本：

```bash
git clone https://github.com/bojieli/AdaptThink.git chapter7/AdaptThink-original && git -C chapter7/AdaptThink-original checkout --detach 0033ad172dd53ac64004b763477407014f21b838
git clone https://github.com/bojieli/SFTvsRL.git chapter7/SFTvsRL && git -C chapter7/SFTvsRL checkout --detach fef0a4a3367260a0934be1e40b01e4021698e023
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git chapter7/SimpleVLA-RL/SimpleVLA-RL && git -C chapter7/SimpleVLA-RL/SimpleVLA-RL checkout --detach 7c51662df27b586f9e8a1ab35fcf849f2b8852f9
git clone https://github.com/bojieli/verl.git chapter7/verl && git -C chapter7/verl checkout --detach 1593fc3a8cf894debdc3dece2a23ed739c282789
git clone https://github.com/bojieli/AWorld.git chapter7/AWorld && git -C chapter7/AWorld checkout --detach a52d61d6d483e66b22ef16970eae5bbf4f4ab2ec
```

以下四个源码目录当前缺失，但不可变版本已经固定。每组命令都显式 fetch、detached checkout，并核对 `rev-parse HEAD`；源码就绪仍不等于实验完成：

```bash
git clone https://github.com/bojieli/minimind.git chapter7/MiniMind-pretrain/minimind
git -C chapter7/MiniMind-pretrain/minimind fetch origin 8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795
git -C chapter7/MiniMind-pretrain/minimind checkout --detach 8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795
git -C chapter7/MiniMind-pretrain/minimind rev-parse HEAD
test "$(git -C chapter7/MiniMind-pretrain/minimind rev-parse HEAD)" = "8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795"

git clone https://github.com/bojieli/minimind-v.git chapter7/MiniMind-pretrain/minimind-v
git -C chapter7/MiniMind-pretrain/minimind-v fetch origin ead791c530fa5f9a3549dbfe9e11ec732d18d2e5
git -C chapter7/MiniMind-pretrain/minimind-v checkout --detach ead791c530fa5f9a3549dbfe9e11ec732d18d2e5
git -C chapter7/MiniMind-pretrain/minimind-v rev-parse HEAD
test "$(git -C chapter7/MiniMind-pretrain/minimind-v rev-parse HEAD)" = "ead791c530fa5f9a3549dbfe9e11ec732d18d2e5"

git clone https://github.com/19PINE-AI/rlvp.git chapter7/RLVP/rlvp
git -C chapter7/RLVP/rlvp fetch origin 1ad30bc7e338911fb733739393d92c420f4d8bee
git -C chapter7/RLVP/rlvp checkout --detach 1ad30bc7e338911fb733739393d92c420f4d8bee
git -C chapter7/RLVP/rlvp rev-parse HEAD
test "$(git -C chapter7/RLVP/rlvp rev-parse HEAD)" = "1ad30bc7e338911fb733739393d92c420f4d8bee"

git clone https://github.com/bojieli/SandboxFusion.git chapter7/SandboxFusion
git -C chapter7/SandboxFusion fetch origin 4a0d573ebd64c98234c190a9d1d49e4276199a0c
git -C chapter7/SandboxFusion checkout --detach 4a0d573ebd64c98234c190a9d1d49e4276199a0c
git -C chapter7/SandboxFusion rev-parse HEAD
test "$(git -C chapter7/SandboxFusion rev-parse HEAD)" = "4a0d573ebd64c98234c190a9d1d49e4276199a0c"
```

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 已有实现，但训练或正文验收证据尚未完整 |
