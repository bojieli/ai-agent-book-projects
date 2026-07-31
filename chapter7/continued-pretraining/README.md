## English

# Continued Pretraining: Teaching a Model a New Language (Korean Mistral)

> This directory corresponds to Chapter 7, **Experiment 7-5 ★★: Continued Pretraining for Learning a New Language** of *Deep Understanding of AI Agents*.

## Project Overview

Using **Mistral 7B v0.3** as the base model (primarily pretrained on English, with virtually no understanding of Korean), we inject Korean language capability through **continued pretraining on Korean Wikipedia**, followed by **SFT on Korean instruction data**. The final model can both understand Korean and follow instructions in Korean.

The core idea this experiment aims to demonstrate: **To make a model memorize a large amount of new domain knowledge (here, a new language), rely on continued pretraining, not SFT.** The model already possesses general language modeling ability from the pretraining phase; continued pretraining merely adapts it to a new data distribution, at a cost far lower than training from scratch.

The entire process consists of two stages:

1. **Continued Pretraining**: Unsupervised "predict the next token" training on Korean Wikipedia, allowing the model to learn Korean vocabulary and syntax.
2. **Instruction Fine-Tuning (SFT)**: Training on Korean Alpaca instruction data to teach the model to "follow instructions in Korean."

A key engineering challenge is **mitigating Catastrophic Forgetting**: learning a new language should not cause the model to forget its original English ability. The common approach discussed in the book uses mixed data (approximately 80% target language + 20% original language) to balance this; this implementation adopts a parameter-efficient scheme using **LoRA + training `embed_tokens`/`lm_head`** — only updating the adapters and word embeddings while keeping the base weights unchanged, thereby preserving English as much as possible while injecting Korean. Evaluation results (see below) show that English ability is largely retained.

## Directory Structure

```
continued-pretraining/
├── README.md                 # This document
├── continued-pretrain.py     # Main training script: continued pretraining + SFT, produces two LoRA models
├── evaluate_model.py         # Single model evaluation: generates samples on Korean/English tasks
├── compare_models.py         # Three-stage comparison: base → continued pretraining → instruction fine-tuning side-by-side generation
├── model_eval_results.md     # Full evaluation output and conclusions from actual run (RTX 4090)
├── validation/               # Canonical report audit, blind-judge receipts, manifest, and validator
├── README_EVALUATION.md      # Detailed usage instructions for evaluation scripts
└── requirements.txt          # Dependency list
```

Running the training script produces two local directories (saving only LoRA adapters, not the full model):

- `lora_model_pretrained/`: Model after continued pretraining, before SFT
- `lora_model/`: Model after final instruction fine-tuning

## System Requirements & Dependencies

- **GPU**: Requires a CUDA-capable NVIDIA GPU. By default, Mistral-7B is loaded in 4-bit quantization, allowing training on consumer-grade GPUs with approximately 24GB VRAM (e.g., RTX 4090). The results in `model_eval_results.md` were produced on an RTX 4090.
- **Framework**: [Unsloth](https://github.com/unslothai/unsloth) (efficient LoRA training), PyTorch, Transformers, Datasets, bitsandbytes.
- **Optional**: wandb (experiment tracking; script defaults to `report_to="wandb"`).

```bash
# From the repository root: use the shared Chapter 7 environment plus Unsloth
uv sync --locked --python 3.12 --extra ch7 --extra unsloth

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch7,unsloth]"

cd chapter7/continued-pretraining

# Single-project compatibility path, still supported for exact legacy parity
# (including the original Unsloth Git install used by this project):
# python -m pip install -r requirements.txt
```

> Note: Unsloth depends on a GPU with a compatible CUDA/PyTorch version and cannot be used for training or inference in a pure CPU environment. The `--help` for each script uses lazy imports, so parameter descriptions can be viewed on machines without a GPU.

## Quick Start

### 1. Training (Continued Pretraining + SFT)

Run both stages with default hyperparameters in one command (using a 5% subset of Korean Wikipedia for continued pretraining, followed by SFT on Korean Alpaca):

```bash
python continued-pretrain.py
```

The script will sequentially: load the base model → print a baseline test → perform continued pretraining on Korean Wikipedia → save `lora_model_pretrained/` → perform SFT on Korean instructions → save `lora_model/`.

Common parameters (defaults match the script's original hardcoded values; changes will deviate from the original experiment):

```bash
python continued-pretrain.py \
    --base_model unsloth/mistral-7b-v0.3 \
    --wiki_config 20231101.ko \
    --wiki_train_size 0.05 \
    --alpaca_dataset FreedomIntelligence/alpaca-gpt4-korean \
    --lora_rank 128 \
    --max_seq_len 2048 \
    --pretrain_epochs 1 \
    --sft_epochs 2 \
    --pretrained_save_dir lora_model_pretrained \
    --final_save_dir lora_model
```

- For a quick smoke test, use `--pretrain_max_steps 20 --sft_max_steps 20` to run only a few steps.
- To switch to a different language: replace `--wiki_config` with the corresponding Wikipedia snapshot (e.g., `20231101.ja` for Japanese) and `--alpaca_dataset` with the corresponding instruction dataset.
- See `python continued-pretrain.py --help` for the full list of parameters.

### 2. Evaluating a Single Model

```bash
# Evaluate the final fine-tuned model (default loads lora_model/)
python evaluate_model.py

# Evaluate the model after continued pretraining, before SFT
python evaluate_model.py --pretrained

# Generate longer outputs using sampling
python evaluate_model.py --max_new_tokens 300 --use_sampling --temperature 0.7
```

See [`README_EVALUATION.md`](./README_EVALUATION.md) for more usage details.

### 3. Three-Stage Side-by-Side Comparison

Load the **base model / continued pretraining model / instruction fine-tuning model** simultaneously and generate side-by-side outputs on the same set of Korean and English prompts, visually demonstrating the improvement in Korean ability and the retention of English ability:

```bash
python compare_models.py
```

```bash
# Specify model directories and generation parameters
python compare_models.py \
    --pretrained_path lora_model_pretrained \
    --finetuned_path lora_model \
    --max_new_tokens 150 \
    --temperature 0.3
```

## Experimental Results

The full terminal output from the historical RTX 4090 run is retained in [`model_eval_results.md`](./model_eval_results.md). The canonical evidence package is [`validation/runs/exp7-5-training-report-20260731-v1/`](validation/runs/exp7-5-training-report-20260731-v1/), and [`validation/latest.json`](validation/latest.json) binds its manifest.

The audit extracted all **5 prompts × 3 stages = 15 outputs** and sent five deterministic stage-blind comparison tasks to the independent ARK `doubao-seed-1-6-250615` judge. All five raw request/responses, unique response IDs, usage, and latency are retained. The 0–5 mean scores were:

| Stage | Korean | English |
| --- | ---: | ---: |
| Base Mistral | 1.6667 | 5.0000 |
| After Korean continued pretraining | 1.3333 | 3.1667 |
| After Korean instruction SFT | 3.4444 | 4.1667 |

The final stage improved the Korean mean by **+1.7777** over baseline. Its English mean fell by **0.8333**, within the audit's declared 1.0-point retention tolerance. Continued pretraining alone did not improve this small retained prompt set; the final SFT stage produced the observed Korean gain. The kimchi answer remained materially false: it described boiling vegetables and soaking them in a soy-sauce-based sauce. That limitation is an accepted negative result, not hidden by the aggregate score.

The historical run did not retain adapter hashes, exact resolved upstream commits, or its generation seed. For future reproduction, the audit freezes immutable current revisions for the base model and both datasets in [`reproduction_contract.json`](validation/runs/exp7-5-training-report-20260731-v1/reproduction_contract.json). Those pins are explicitly **not claimed to be the historical revisions**.

Training checkpoints/adapters are intentionally local and are not distributed with the book. They are not acceptance artifacts; the accepted artifact is the reproducible, evidence-backed report. Validate it without a GPU or provider call:

```bash
python chapter7/continued-pretraining/validation/validate_evidence.py
python -m pytest chapter7/continued-pretraining/validation/test_report_audit.py -q
```

To create a new independent audit from the retained report, set `ARK_API_KEY` and use a new run ID:

```bash
python chapter7/continued-pretraining/validation/run_report_audit.py \
  --run-id exp7-5-training-report-YYYYMMDD-vN
```

The evidence-backed conclusions are:

- **The full two-stage path improved Korean in this retained comparison**: the final SFT stage scored substantially above the baseline, while the continued-pretrained intermediate stage did not.
- **English remained usable but measurably regressed**: the final stage stayed within the declared tolerance; the intermediate stage regressed much more.
- **Fluency is not factual reliability**: the fluent final kimchi answer contains serious preparation and ingredient errors.

## References

- Unsloth documentation: https://docs.unsloth.ai
- Base model: [unsloth/mistral-7b-v0.3](https://huggingface.co/unsloth/mistral-7b-v0.3)
- Continued pretraining corpus: [wikimedia/wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia) (`20231101.ko`)
- Instruction fine-tuning corpus: [FreedomIntelligence/alpaca-gpt4-korean](https://huggingface.co/datasets/FreedomIntelligence/alpaca-gpt4-korean)

---

## 中文

# 继续预训练：让模型学会一门新语言（韩语 Mistral）

> 本目录对应《深入理解 AI Agent》第 7 章 **实验 7-5 ★★：继续预训练学习新语言**。

## 项目简介

以 **Mistral 7B v0.3** 为基础模型（主要用英语预训练，对韩语几乎没有理解能力），通过**韩语维基百科继续预训练**注入韩语能力，再用**韩语指令数据做 SFT**，最终得到一个既能理解韩语、又能用韩语遵循指令的模型。

本实验想说明的核心观点：**要让模型记住大量新领域知识（这里是一门新语言），靠的是继续预训练，而不是 SFT。** 模型在预训练阶段已经具备通用的语言建模能力，继续预训练只是让它适应新的数据分布，成本远低于从头训练。

整个流程分两个阶段：

1. **继续预训练（Continued Pretraining）**：在韩语维基百科上做无监督的“预测下一个词”训练，让模型学会韩语的词汇与句法。
2. **指令微调（SFT）**：在韩语 Alpaca 指令数据上训练，让模型学会“用韩语遵循指令”。

一个关键工程点是**缓解灾难性遗忘（Catastrophic Forgetting）**：学了新语言不能把原来的英语能力忘掉。书中讨论的通用做法是用混合数据（约 80% 目标语言 + 20% 原语言）来平衡；本实现则采用 **LoRA + 训练 `embed_tokens`/`lm_head`** 的参数高效方案——只更新适配器与词嵌入，基础权重保持不变，从而在注入韩语的同时尽量保留英语。评测结果（见下文）显示英语能力基本得到保留。

## 目录结构

```
continued-pretraining/
├── README.md                 # 本文档
├── continued-pretrain.py     # 训练主脚本：继续预训练 + SFT，产出两个 LoRA 模型
├── evaluate_model.py         # 单模型评测：在韩英任务上生成样例
├── compare_models.py         # 三阶段对比：基础 → 继续预训练 → 指令微调 并排生成
├── model_eval_results.md     # 真实运行的完整评测输出与结论（RTX 4090）
├── validation/               # 规范报告审计、盲评回执、manifest 与验证器
├── README_EVALUATION.md      # 评测脚本的详细用法说明
└── requirements.txt          # 依赖清单
```

训练脚本运行后会产出两个本地目录（仅保存 LoRA 适配器，不含完整模型）：

- `lora_model_pretrained/`：继续预训练之后、SFT 之前的模型
- `lora_model/`：最终指令微调之后的模型

## 系统要求与依赖

- **GPU**：需要支持 CUDA 的 NVIDIA GPU。默认以 4bit 量化加载 Mistral-7B，可在约 24GB 显存的消费级显卡（如 RTX 4090）上完成训练，`model_eval_results.md` 中的结果即在 RTX 4090 上产出。
- **框架**：[Unsloth](https://github.com/unslothai/unsloth)（高效 LoRA 训练）、PyTorch、Transformers、Datasets、bitsandbytes。
- **可选**：wandb（实验跟踪，脚本默认 `report_to="wandb"`）。

```bash
# 在仓库根目录使用统一的第 7 章环境，并显式加入 Unsloth
uv sync --locked --python 3.12 --extra ch7 --extra unsloth

# 切换目录前先激活环境：
# macOS/Linux：
source .venv/bin/activate
# Windows PowerShell：.\.venv\Scripts\Activate.ps1
# Windows cmd：.venv\Scripts\activate.bat

# 未安装 uv 时可用 pip 兜底：
# python -m pip install -e ".[ch7,unsloth]"

cd chapter7/continued-pretraining

# 迁移期间仍支持单项目兼容路径，用于完全复现旧版依赖
#（包括本项目原有的 Unsloth Git 安装方式）：
# python -m pip install -r requirements.txt
```

> 注意：Unsloth 依赖 GPU 与匹配的 CUDA/PyTorch 版本，无法在纯 CPU 环境下训练或推理。各脚本的 `--help` 已做延迟导入，可在没有 GPU 的机器上直接查看参数说明。

## 快速开始

### 1. 训练（继续预训练 + SFT）

用默认超参数一键完成两个阶段（韩语维基百科 5% 子集做继续预训练，随后用韩语 Alpaca 做 SFT）：

```bash
python continued-pretrain.py
```

脚本会依次：加载基础模型 → 打印基线测试 → 韩语维基继续预训练 → 保存 `lora_model_pretrained/` → 韩语指令 SFT → 保存 `lora_model/`。

常用参数（默认值与脚本原始硬编码一致，改动才会偏离原实验）：

```bash
python continued-pretrain.py \
    --base_model unsloth/mistral-7b-v0.3 \
    --wiki_config 20231101.ko \
    --wiki_train_size 0.05 \
    --alpaca_dataset FreedomIntelligence/alpaca-gpt4-korean \
    --lora_rank 128 \
    --max_seq_len 2048 \
    --pretrain_epochs 1 \
    --sft_epochs 2 \
    --pretrained_save_dir lora_model_pretrained \
    --final_save_dir lora_model
```

- 想快速冒烟测试，可用 `--pretrain_max_steps 20 --sft_max_steps 20` 只跑很少的步数。
- 想换一门语言：把 `--wiki_config` 换成对应维基快照（如 `20231101.ja` 日语）、`--alpaca_dataset` 换成对应语言的指令集即可。
- 完整参数见 `python continued-pretrain.py --help`。

### 2. 评测单个模型

```bash
# 评测最终微调模型（默认加载 lora_model/）
python evaluate_model.py

# 评测继续预训练后、SFT 前的模型
python evaluate_model.py --pretrained

# 生成更长、使用采样
python evaluate_model.py --max_new_tokens 300 --use_sampling --temperature 0.7
```

更多用法详见 [`README_EVALUATION.md`](./README_EVALUATION.md)。

### 3. 三阶段并排对比

同时加载**基础模型 / 继续预训练模型 / 指令微调模型**，在同一组中韩英提示上并排生成，直观展示韩语能力的提升与英语能力的保留：

```bash
python compare_models.py
```

```bash
# 指定模型目录与生成参数
python compare_models.py \
    --pretrained_path lora_model_pretrained \
    --finetuned_path lora_model \
    --max_new_tokens 150 \
    --temperature 0.3
```

## 实验结果

历史 RTX 4090 运行的完整终端输出保存在 [`model_eval_results.md`](./model_eval_results.md)。规范证据包位于 [`validation/runs/exp7-5-training-report-20260731-v1/`](validation/runs/exp7-5-training-report-20260731-v1/)，[`validation/latest.json`](validation/latest.json) 绑定其 manifest。

审计从原始报告提取了 **5 个提示 × 3 个阶段 = 15 个输出**，并向独立 ARK `doubao-seed-1-6-250615` 裁判提交了五次确定性乱序、阶段匿名的对比。五份原始请求/响应、唯一 response ID、usage 与延迟均已保留。0–5 分均值如下：

| 阶段 | 韩语 | 英语 |
| --- | ---: | ---: |
| 基础 Mistral | 1.6667 | 5.0000 |
| 韩语继续预训练后 | 1.3333 | 3.1667 |
| 韩语指令 SFT 后 | 3.4444 | 4.1667 |

最终阶段相对基线的韩语均值提升 **+1.7777**；英语均值下降 **0.8333**，仍在预先声明的 1.0 分保留容差内。仅继续预训练的中间阶段在这组小规模保留提示上没有提升，观察到的韩语增益来自完整两阶段流程后的最终 SFT 模型。最终模型的泡菜回答仍有严重事实错误：它错误地描述了煮蔬菜和以酱油为基础的浸泡汁。这个负结果被明确保留，而没有被总分掩盖。

历史运行没有保留 adapter hash、当时解析到的上游 commit 或生成随机种子。为了将来复现，[`reproduction_contract.json`](validation/runs/exp7-5-training-report-20260731-v1/reproduction_contract.json) 固定了基础模型和两个数据集的当前不可变 revision；这些 revision 明确**不声称是历史运行所用版本**。

训练 checkpoint/adapter 按本书策略仅保存在本地，不随书分发，也不是验收产物；验收产物是可复现、证据充分的训练报告。无需 GPU 或 API 调用即可验证：

```bash
python chapter7/continued-pretraining/validation/validate_evidence.py
python -m pytest chapter7/continued-pretraining/validation/test_report_audit.py -q
```

如需从保留报告创建新的独立审计，设置 `ARK_API_KEY` 并使用新的 run ID：

```bash
python chapter7/continued-pretraining/validation/run_report_audit.py \
  --run-id exp7-5-training-report-YYYYMMDD-vN
```

有证据支持的结论如下：

- **完整两阶段流程在本次保留对比中提升了韩语**：最终 SFT 阶段显著高于基线，但继续预训练的中间阶段没有提升。
- **英语仍可用，但出现可测量的退化**：最终阶段仍在声明容差内；中间阶段退化更明显。
- **流畅不等于事实可靠**：最终泡菜回答虽然更流畅，却包含严重的制作方法与配料错误。

## 参考资料

- Unsloth 文档：https://docs.unsloth.ai
- 基础模型：[unsloth/mistral-7b-v0.3](https://huggingface.co/unsloth/mistral-7b-v0.3)
- 继续预训练语料：[wikimedia/wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia)（`20231101.ko`）
- 指令微调语料：[FreedomIntelligence/alpaca-gpt4-korean](https://huggingface.co/datasets/FreedomIntelligence/alpaca-gpt4-korean)
