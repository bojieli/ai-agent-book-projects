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
pip install -r requirements.txt
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

The full output, item-by-item comparisons, and conclusions from the actual run can be found in [`model_eval_results.md`](./model_eval_results.md) (produced on an RTX 4090; please refer to the actual results in that file, as this document will not repeat the specific values). The main conclusions can be summarized as:

- **Methodology is valid**: Continued pretraining + SFT can indeed inject new language ability into a model. Korean improved from "basically unusable" to "fluent and able to follow instructions," while English ability was largely retained (no significant catastrophic forgetting).
- **Data quality is the bottleneck**: Using only 5% of Wikipedia corpus, general language ability improved significantly, but specific cultural knowledge (e.g., kimchi) still often produced errors — indicating that for specific knowledge domains, **data coverage and quality are more critical than the training method itself**.

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
pip install -r requirements.txt
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

真实运行的完整输出、逐条对比与结论见 [`model_eval_results.md`](./model_eval_results.md)（在 RTX 4090 上产出，请以该文件中的实际结果为准，本文不再复述具体数值）。其主要结论可概括为：

- **方法论成立**：继续预训练 + SFT 确实能为模型注入新语言能力，韩语从“基本不可用”提升到“流畅、能遵循指令”，同时英语能力基本得到保留（无明显灾难性遗忘）。
- **数据质量是瓶颈**：仅用 5% 的维基百科语料，通用语言能力提升明显，但特定文化知识（如泡菜等）仍常出错——说明对具体知识域而言，**数据覆盖与质量比训练方法本身更关键**。

## 参考资料

- Unsloth 文档：https://docs.unsloth.ai
- 基础模型：[unsloth/mistral-7b-v0.3](https://huggingface.co/unsloth/mistral-7b-v0.3)
- 继续预训练语料：[wikimedia/wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia)（`20231101.ko`）
- 指令微调语料：[FreedomIntelligence/alpaca-gpt4-korean](https://huggingface.co/datasets/FreedomIntelligence/alpaca-gpt4-korean)
