# Experiment 7-10 reproduction anchor

This directory is the book-owned explanation. Executable training code is the external [`bojieli/AdaptThink`](https://github.com/bojieli/AdaptThink) checkout at `chapter7/AdaptThink-original`, verified in the current workspace at commit `0033ad172dd53ac64004b763477407014f21b838`.

## Canonical training report / 规范训练报告

The canonical Experiment 7-10 result is the checkpoint-free [training report](TRAINING_REPORT.md). It is backed by public W&B run [`wubbn5tj`](https://wandb.ai/bojieli-pine-ai/adapt_think_verl/runs/wubbn5tj); baseline run [`dblyx7cm`](https://wandb.ai/bojieli-pine-ai/adapt_think_verl/runs/dblyx7cm) exactly matches its step-0 validation metrics.

本实验的规范结果是无 checkpoint 的[历史训练报告](TRAINING_REPORT.md)。公开 W&B 主运行是 [`wubbn5tj`](https://wandb.ai/bojieli-pine-ai/adapt_think_verl/runs/wubbn5tj)，基线运行 [`dblyx7cm`](https://wandb.ai/bojieli-pine-ai/adapt_think_verl/runs/dblyx7cm) 的验证指标与主运行 step 0 完全一致。

| Dataset | Accuracy, step 0 → 300 | Response length, step 0 → 300 | Step-300 NoThinking |
| --- | ---: | ---: | ---: |
| MATH500 | 0.8100 → 0.8180 (+0.80 pp) | 4911.46 → 1576.62 (-67.90%) | 83.80% |
| GSM8K | 0.796816 → 0.818802 (+2.20 pp) | 1025.24 → 477.33 (-53.44%) | 84.15% |
| AIME2024 mean@16 | 0.314583 → 0.310417 (-0.42 pp) | 12119.51 → 6402.23 (-47.17%) | 56.25% |

W&B records 8 × NVIDIA H100 80GB GPUs (CUDA 12.6), a configured schedule of 10 epochs / 3,140 steps, and save/test intervals of 10 steps. Step 300 occurred at 28.37 hours. The run continued to step 410 (411 history rows; 36.92 hours) and then has state `crashed`, so neither the full schedule nor a clean completion is claimed. A step-300 checkpoint timing event is logged, but the checkpoint is not distributed with the book.

These aggregate metrics show large response-length reductions on all three datasets and a lower NoThinking rate on AIME. They do **not** show uniform accuracy improvement—AIME regressed slightly—or prove “perfect” per-example difficulty awareness. No public separate `adapt_think_verl-eval` run was found, and no retained receipt proves that the selected checkpoint was evaluated with `run_eval_verl_hf.sh` or that MMLU was rerun.

以上结果明确取代下文历史说明中的 `1 epoch / 314 steps`、H800、宽泛取整区间、准确率普遍提升和“完美难度感知”等表述；下文仅保留作方法与历史解读背景。

```bash
git clone https://github.com/bojieli/AdaptThink.git chapter7/AdaptThink-original
git -C chapter7/AdaptThink-original checkout --detach 0033ad172dd53ac64004b763477407014f21b838
cd chapter7/AdaptThink-original
bash scripts/preprocess_dataset.sh
bash scripts/run_adapt_think_1.5b_deepscaler_16k_delta0.05_btz128_lr2e-6.sh
bash scripts/run_eval_verl_hf.sh
```

These commands identify the future workflow; the documentation audit did not rerun them. The W&B-recorded source commit `9e588202ff56fe93cdbe49f5594cf895f7d6b7c2` is the parent of the future pin above, and the three entrypoints are byte-identical at both revisions. Manual path correction is nevertheless required: the training script interpolates an undefined `adapt_think_max_response_length` into its experiment name (yielding `-fl-`), while the evaluation script expects `-fl4096` and omits the training script's `adapt_think_verl/` directory level.

## English

# AdaptThink: Teaching Reasoning Models When to Think

> **Historical, noncanonical walkthrough.** This long-form explanation is retained for method context. Where its rounded trends, comparisons, or cost estimates conflict with the canonical section above, the training report and exact step-300 table control.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Core Principles](#core-principles)
  - [Research Motivation](#research-motivation)
  - [Method Design](#method-design)
- [Experiment Setup](#experiment-setup)
  - [Model and Data](#model-and-data)
  - [Training Configuration](#training-configuration)
- [Experimental Results Analysis](#experimental-results-analysis)
  - [Overall Performance](#overall-performance)
  - [Training Process Analysis](#training-process-analysis)
  - [Adaptive Behavior Across Difficulties](#adaptive-behavior-across-difficulties)
  - [Efficiency vs. Accuracy Trade-off](#efficiency-vs-accuracy-trade-off)
- [Operation Guide](#operation-guide)
- [Key Findings](#key-findings)
- [Reference Resources](#reference-resources)

---

## Project Overview

**AdaptThink** is an innovative reinforcement learning algorithm designed to teach Large Reasoning Models (LRMs) to **adaptively choose their reasoning mode** based on problem difficulty.

### Background Problem

Current reasoning models (e.g., OpenAI o1, DeepSeek-R1) engage in prolonged "thinking" when processing problems. While this deep reasoning improves performance on complex tasks, it also introduces significant issues:

- **High inference cost**: Long thinking chains lead to substantially increased token consumption
- **High latency**: Even simple problems require lengthy thinking processes
- **Inefficiency**: Many simple problems do not require complex reasoning

### Core Innovation

AdaptThink enables models to intelligently switch between two modes:

- **Thinking mode**: Generates detailed thinking chains (`<think>...</think>`) to solve complex problems
- **NoThinking mode**: Skips the thinking process and directly generates answers for simple problems

In the retained step-300 result, this mechanism **substantially reduces mean response length**, with mixed accuracy changes across datasets.

---

## Core Principles

### Research Motivation

The paper first identifies a key phenomenon through experimentation:

> **For relatively simple problems (below high school competition level), the NoThinking mode performs comparably to or even better than the Thinking mode, while significantly reducing token usage. The advantage of Thinking only becomes apparent when problems are sufficiently difficult.**

This finding motivates the core research question:

**Can we enable models to autonomously learn to select the optimal reasoning mode based on problem difficulty?**

### Method Design

AdaptThink achieves adaptive reasoning through two core components:

#### 1. Constrained Optimization

$$\max_{\theta} \mathbb{E}_{x \sim \mathcal{D}, y \sim \pi_\theta(y|x)} [r(x,y)] \quad \text{s.t.} \quad \mathbb{E}_{x \sim \mathcal{D}, y \sim \pi_\theta(y|x)} [r(x,y)] \geq \mathbb{E}_{x \sim \mathcal{D}, y \sim \pi_{\text{ref}}(y|x)} [r(x,y)] - \delta$$

Where:
- $r(x,y)$ is the reward function (based on answer accuracy)
- $\pi_{\text{ref}}$ is the reference model (original reasoning model)
- $\delta$ is the allowable performance degradation (set to 0.05 in this experiment)

**Core idea**: Maximize reward while ensuring overall performance does not fall below the reference model (allowing a slight degradation $\delta$). The separate sampling strategy below exposes the model to both Thinking and NoThinking responses; the constrained objective shown here does not itself include a KL-divergence or token-cost term.

#### 2. Importance Sampling Strategy

During training, to balance Thinking and NoThinking samples:

- **Cold start phase**: The model tends to use Thinking (its pre-training behavior)
- **Sampling strategy**: Importance sampling is introduced to ensure both Thinking and NoThinking samples are present during training
- **Exploration vs. exploitation**: The model continuously explores both modes throughout training

Implementation: For each problem, both Thinking and NoThinking responses are sampled, and sampling weights are dynamically adjusted based on their performance.

#### 3. NoThinking Implementation

Implemented by adding an empty think tag to the input prompt:

```
User: [Problem]
Assistant: <think></think>[Direct Answer]
```

This concise implementation leverages the model's pre-trained knowledge, allowing it to understand the semantics of "skipping thinking."

---

## Experiment Setup

### Model and Data

#### Base Model
- **DeepSeek-R1-Distill-Qwen-1.5B** (this experiment)
- DeepSeek-R1-Distill-Qwen-7B (comparison experiment in the paper)

#### Training Dataset
- **DeepScaler**: 40,000 math problems covering multiple difficulty levels from elementary school to high school competitions

#### Evaluation Datasets
- **GSM8K**: Elementary school math problems
- **MATH500**: Competition-level math problems (Levels 1-5)
- **AIME2024**: American high school math competition (hardest)

### Training Configuration

| Parameter | Value |
|-----------|-------|
| Context length | 16K tokens |
| Batch size | 128 |
| Learning rate | 2e-6 |
| Configured schedule | 10 epochs (3,140 planned steps); run crashed after step 410 |
| δ (performance tolerance) | 0.05 |
| Hardware configuration | 8 × NVIDIA H100 80GB, CUDA 12.6 |
| Logged duration | Step 300 at 28.37 h; through step 410 at 36.92 h |
| Retained report point | Step 300; checkpoint not distributed |

#### Reference Model Pre-sampling

Pre-sampling of the reference model is required before training to evaluate instance-level accuracy:
- 16 responses sampled per training problem
- Accuracy calculated per problem as a difficulty metric
- Used for importance sampling weight calculation

---

## Experimental Results Analysis

### Overall Performance

Based on WandB monitoring data from this experiment (1.5B model, δ=0.05): https://wandb.ai/bojieli-pine-ai/adapt_think_verl/

#### Core Metrics Comparison

| Dataset | Accuracy, step 0 → 300 | Response Length, step 0 → 300 | NoThinking at step 300 |
|---------|--------------------------|--------------------------------|------------------------|
| GSM8K | **0.796816 → 0.818802** (+2.20 pp) | 1025.24 → 477.33 (-53.44%) | **84.15%** |
| MATH500 | **0.8100 → 0.8180** (+0.80 pp) | 4911.46 → 1576.62 (-67.90%) | **83.80%** |
| AIME2024 mean@16 | **0.314583 → 0.310417** (-0.42 pp) | 12119.51 → 6402.23 (-47.17%) | **56.25%** |

**Key Results**:
- **Accuracy is mixed**: MATH500 gained 0.80 pp and GSM8K gained 2.20 pp, while AIME mean@16 lost 0.42 pp
- **Significant efficiency gains**: response-length means fell 67.90% on MATH500, 53.44% on GSM8K, and 47.17% on AIME
- **Dataset-level routing signal**: AIME's 56.25% NoThinking rate is lower than MATH500/GSM8K, consistent with difficulty-sensitive routing but not proof of perfect per-example awareness

### Training Process Analysis

#### 1. Evolution of Response Length

From the WandB chart `response_length/mean` and response lengths for each dataset, a clear three-phase pattern emerges:

```
Initial Phase (Step 0-50):
  - Overall average response length: ~5,500 tokens
  - MATH500: ~5,000 tokens (almost all Thinking)
  - GSM8K: ~1,600 tokens (almost all Thinking)
  - AIME: ~12,000 tokens (long thinking chains for complex problems)
  - Model continues pre-training behavior, thinking on all problems

Transition Phase (Step 50-150):
  - Overall drops sharply to ~4,000 tokens
  - is_nothinking ratio begins to rise (from 0 → 0.5+)
  - NoThinking accuracy emerges rapidly (MATH500: 0 → 0.8)
  - Critical period for the model to learn to distinguish problem difficulty

Stable Phase (Step 150-300):
  - Overall stabilizes at ~3,000-3,500 tokens
  - MATH500: drops to ~1,800 tokens (80% NoThinking)
  - GSM8K: drops to ~500 tokens (85% NoThinking)
  - AIME: drops to ~9,000 tokens (55% NoThinking)
  - NoThinking routing is established; accuracy does not improve uniformly across datasets
```

**Key Observation**: The retained aggregate data are consistent with difficulty-sensitive routing, but cannot establish a perfect per-example match to difficulty.

#### 2. Evolution of Accuracy and Emergence of NoThinking Capability

**GSM8K (Simple Math)**:
- **selected-point score/mean**: 0.796816 → **0.818802** (+2.20 pp)
- **nothinking_acc**: Rapidly rises from 0 to **0.88-0.90** around Step 150
- **selected-point is_nothinking**: **84.15%**
- **Key Finding**: The step-300 aggregate uses NoThinking on 84.15% of GSM8K examples

**MATH500 (Medium Math)**:
- **selected-point score/mean**: 0.8100 → **0.8180** (+0.80 pp)
- **thinking_acc**: Stable between 0.5-0.65 (difficult problems selected by the model)
- **nothinking_acc**: Emerges rapidly around Step 150, jumping from 0 to **0.8-0.85** (simple problems selected by the model)
- **selected-point is_nothinking**: **83.80%**
- **Key Finding**: The step-300 aggregate uses NoThinking on 83.80% of MATH500 examples

**AIME2024 (Hard Math)**:
- **selected-point score/mean@16**: 0.314583 → **0.310417** (-0.42 pp)
- **thinking_acc**: Fluctuates significantly between 0.3-0.7
- **nothinking_acc**: Gradually improves from 0.3 to 0.4-0.6
- **selected-point is_nothinking/mean@16**: **56.25%**, lower than the other two datasets
- **Key Finding**: AIME uses Thinking more often at the selected point, while its accuracy slightly regresses

#### 2.1 Emergence Phenomenon of NoThinking Capability

From the chart `nothinking_acc/mean`, a surprising phenomenon is clearly observable:

```
Step 0-150:   nothinking_acc ≈ 0 or undefined (almost no NoThinking samples)
Step 150:     Sharp inflection point
Step 150-300: nothinking_acc ≈ 0.8-0.85 (MATH500), 0.88-0.90 (GSM8K)
```

This **sudden emergence** suggests:
- The model is not simply learning "when to skip thinking"
- It is genuinely learning the ability to "solve simple problems without thinking"
- This represents a high-level meta-learning capability

#### 3. Emergence of Adaptive Behavior

From the `is_nothinking/mean` metric, clear stratification of adaptive behavior across datasets is visible:

```
GSM8K:            84.15% NoThinking  ← Simple problems (elementary math)
MATH500:          83.80% NoThinking  ← Medium difficulty (high school math)
AIME2024:         56.25% NoThinking  ← Difficult problems (competition level)
```

**Timeline of Adaptive Pattern Evolution** (using MATH500 as an example):

```
Step 0-100:   is_nothinking ≈ 0-0.1 (almost never uses NoThinking)
Step 100-150: is_nothinking rises rapidly 0.1 → 0.6
Step 150:     Critical inflection point, is_nothinking jumps to 0.8
Step 150-300: is_nothinking stabilizes at 0.78-0.82
```

This aggregate stratification is consistent with **difficulty-sensitive reasoning-mode selection**. Without per-example outputs, it does not prove that routing is correct for each problem or that a causal capability suddenly emerged at Step 150.

#### 4. Historical Curve Observations

The following are descriptive observations from the historical `adapt_think` curves. They do not override the final W&B state `crashed` or establish causal training phases:

**Reward Evolution**:
- **thinking_reward/mean**: Gradually rises from negative values to near 0 or positive
- **reward/mean**: Trends upward over the selected reporting window
- **nothinking_reward**: Fluctuates more but generally trends upward

**Token Probability**:
- **first_eot_token_probs/mean**: Rises from ~0.2 to **0.6-0.8**
  - This records greater probability on the first end-of-thinking token
  - It does not by itself prove calibrated confidence or correct per-example routing

**Thinking Chain Length Optimization** (adapt_think/thinking_response_length):
- Drops from ~9,000 tokens to **~4,500-5,000 tokens**
- Thinking-mode responses become shorter in aggregate
- **Observed combination**: less Thinking use on some datasets and shorter Thinking responses

**Overall Response Length Trend** (response_length):
- **mean**: 5,500 → 3,000 (-45%)
- **min**: Stable at 50-150 (shortest responses)
- **max**: Remains at 16,000-17,000 (limited by the response cap)
- **clip_ratio**: decreases from about 0.1 to **0.02**

### Adaptive Behavior Across Difficulties

#### MATH500 Difficulty Analysis (from the paper)

| Difficulty Level | NoThinking Ratio | Accuracy Change |
|-----------------|-----------------|-----------------|
| Level 1 | 95% | +3% |
| Level 2 | 88% | +2% |
| Level 3 | 72% | +1% |
| Level 4 | 45% | No change |
| Level 5 | 28% | No change |

**Observations**:
1. **Paper-reported monotonic pattern**: The NoThinking ratio decreases as difficulty increases; this is not proof of perfect awareness
2. **Efficiency-quality balance**: NoThinking is used boldly for simple problems, while Thinking is retained cautiously for difficult ones
3. **Performance maintained**: Good accuracy levels are preserved across all problem types

### Efficiency vs. Accuracy Trade-off

#### Impact of the δ Parameter

The paper compares the effects of different δ values:

| δ Value | NoThinking Ratio | Response Length Reduction | Accuracy Change |
|---------|-----------------|--------------------------|-----------------|
| 0 | Lowest | Small | Slight improvement |
| 0.01 | Medium | ~40% | Slight improvement |
| 0.02 | High | ~50% | No change |
| **0.05** | **~80%** | **~53%** | **+2.4%** |
| 0.075 | Higher | ~60% | Possible decrease |
| 0.1 | Highest | Largest | Slight decrease |

**Historical paper-level rationale for δ=0.05**: The table above is comparison context, not the exact retained step-300 result. In the canonical run, all three response-length means fell, but accuracy was mixed and AIME regressed by 0.42 pp.

---

## Operation Guide

### Environment Setup

```bash
# Create environment
conda create -n adapt_think python=3.13
conda activate adapt_think

# Install dependencies
cd chapter7/AdaptThink-original
pip install -r requirements.txt
pip install flash-attn --no-build-isolation
```

### Data Preparation

#### 1. Pre-sampling Reference Responses

```bash
# Start vLLM server
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B \
  --served_model_name DeepSeek-R1-Distill-Qwen-1.5B \
  --tensor_parallel_size 4

# Sample 16 responses
python src/presampling_ref_responses.py \
  --K 16 \
  --dataset_path ./data/train/deepscaler.json \
  --model_name DeepSeek-R1-Distill-Qwen-1.5B \
  --max_tokens 16384

# Post-process to get instance-level accuracy
python src/postprocess_ref_results.py \
  --input_path ./data/train/ref_presampling/DeepSeek-R1-Distill-Qwen-1.5B_deepscaler_n0_K16_len16384.json \
  --output_path ./data/train/ref_results/DeepSeek-R1-Distill-Qwen-1.5B_deepscaler_K16_len16384.json
```

**Note**: Pre-processed results are already provided in `./data/train/ref_results` and can be used directly.

#### 2. Preprocess Dataset

```bash
bash scripts/preprocess_dataset.sh
```

### Training

```bash
# 1.5B model, single node
bash scripts/run_adapt_think_1.5b_deepscaler_16k_delta0.05_btz128_lr2e-6.sh
```

**Training Monitoring**:
- VeRL automatically logs training metrics to WandB
- Test set is automatically evaluated every `trainer.test_freq` steps
- Key monitoring metrics:
  - `val-aux/gsm8k/score/mean`: GSM8K accuracy
  - `val-aux/math/score/mean`: MATH500 accuracy
  - `response_length/mean`: Average response length
  - `adapt_think/is_nothinking/mean`: NoThinking ratio
  - `adapt_think/thinking_response_length/mean`: Chain-of-thought length

### Evaluation

The commands below are the advertised upstream workflow, not a receipt of a successful selected-checkpoint evaluation. Correct the `-fl-` versus `-fl4096` experiment-name mismatch and the missing `adapt_think_verl/` directory level before using it.

```bash
# Convert checkpoint to HF format
bash scripts/convert_to_hf.sh

# Run evaluation
bash scripts/run_eval_verl_hf.sh

# Or directly evaluate a published HF model
bash scripts/run_eval_hf.sh
```

---

## Key Findings

### 1. Effectiveness of NoThinking

**Key Finding**: At step 300, NoThinking is used more often on GSM8K and MATH500 than on AIME2024.

**Observations**:
- Conditional aggregate accuracy remains high for the subsets routed to NoThinking
- NoThinking responses are shorter than Thinking responses on all three datasets
- Without retained per-example outputs, the report cannot determine whether every routing choice was correct

### 2. Emergence of Adaptive Behavior

The step-300 aggregates show a routing gradient across datasets without explicit difficulty labels:

```
Simple problems (GSM8K):     "Simple arithmetic"       → NoThinking (85%)
Medium problems (MATH500):   "High school math"       → NoThinking (80%)
Difficult problems (AIME):   "Competition-level problems"     → Mixed use (55%)
```

### 3. Efficiency Gain with Mixed Accuracy

At the selected point, AdaptThink reduces mean response length on all three retained datasets, while accuracy changes are mixed:

- **Significant efficiency gains**:
  - GSM8K: Response length reduced by **53.44%** (1025.24 → 477.33)
  - MATH500: Response length reduced by **67.90%** (4911.46 → 1576.62)
  - AIME: Response length reduced by **47.17%** (12119.51 → 6402.23)

- **Mixed performance**:
  - MATH500: Accuracy changed **0.8100 → 0.8180** (+0.80 pp)
  - GSM8K: Accuracy changed **0.796816 → 0.818802** (+2.20 pp)
  - AIME mean@16: Accuracy changed **0.314583 → 0.310417** (-0.42 pp)

- **Reasons**:
  - Targeted use of reasoning resources, quick decisions on simple problems
  - Thinking itself becomes more concise (from 9K → 5K tokens)
  - Avoids error accumulation from overthinking

### 4. Training Stability and Key Inflection Point

The historical W&B curves show a sharp aggregate routing change around step 150. The run later crashed after step 410, so this is not described as a cleanly completed or universally stable campaign.

**Step 150 - Descriptive routing inflection**:
- Validation **is_nothinking** rises sharply
- Validation **nothinking_acc** rises from near 0 to about 0.8-0.9
- Mean response length begins to decrease rapidly
- **first_eot_token_probs** increases

The training configuration forces balanced Thinking/NoThinking sampling during optimization. The validation curves are observational and do not prove a phase transition or prevent dataset-level performance regressions; AIME accuracy is slightly lower at step 300.

---

## Comparison with Existing Methods

| Method | Core Idea | Response Length Reduction | Accuracy Change | Adaptivity |
|--------|-----------|--------------------------|-----------------|------------|
| **Baseline Model** | Think on all problems | 0% | - | ❌ |
| **Length Reward** | Add length penalty in RL | ~30% | No change/decrease | ❌ |
| **DPO (Short Preference)** | Alignment preferring short responses | ~35% | No change | ❌ |
| **Model Merging** | Fusion of reasoning/non-reasoning models | ~25% | No change | Partial |
| **AdaptThink** | Adaptive mode selection | **45-69%** | **+2-10%** | ✅ |

**Specific data for this experiment (1.5B, δ=0.05)**:
- GSM8K: Response length ↓53.44%, accuracy +2.20 pp, 84.15% NoThinking
- MATH500: Response length ↓67.90%, accuracy +0.80 pp, 83.80% NoThinking
- AIME mean@16: Response length ↓47.17%, accuracy -0.42 pp, 56.25% NoThinking

**Unique Advantages of AdaptThink**:
- **Paper-level comparison only**: the retained run does not independently establish that AdaptThink is the only method improving both dimensions
- **Aggregate adaptivity signal**: NoThinking use is lower on AIME than on MATH500/GSM8K
- ✅ **Dual optimization**: Reduces Thinking usage + optimizes Thinking itself
- **Observed routing transition**: aggregate NoThinking metrics change sharply around the middle of the retained run
- ✅ **No additional model needed**: A single model can achieve mixed reasoning

---

## Experimental Environment and Cost

### Hardware Requirements

**Training**:
- Retained 1.5B W&B run: 8 × NVIDIA H100 80GB; step 300 at 28.37 hours and step 410 at 36.92 hours
- 7B resource statements in the original walkthrough are paper context and were not recorded by this run

**Inference**:
- Can use a single GPU (depending on model size)
- vLLM for accelerated inference

### Computational Cost Estimate

Using the 1.5B model as an example:
- **Observed training allocation**: 8×H100; 28.37 wall-clock hours to the selected point and 36.92 hours through the final logged step
- **Inference cost savings**:
  - GSM8K: 53.44% lower mean response length at step 300
  - MATH500: 67.90% lower mean response length at step 300
  - AIME2024: 47.17% lower mean response length at step 300
- **Boundary**: token reductions do not by themselves prove proportional latency speedups or a specific ROI

---

## Limitations and Future Directions

### Current Limitations

1. **Domain limitation**: Primarily validated on math tasks; other domains require further testing
2. **δ tuning**: Different tasks may require different δ values
3. **Cold start**: Requires pre-sampling of a reference model, adding preparation cost
4. **Interpretability**: How the model judges difficulty remains a black box

### Future Directions

1. **Multi-level reasoning**: Not just a binary Thinking/NoThinking choice, but multiple levels like "shallow thinking" and "deep thinking"
2. **Online adaptation**: Dynamically adjust reasoning depth based on real-time feedback
3. **Cross-domain generalization**: Validate on more tasks like code, reasoning, creative writing
4. **User control**: Allow users to specify reasoning depth preferences

---

## Reference Resources

### Paper and Code

- **Paper**: [AdaptThink: LLM Can Learn When to Think](https://arxiv.org/abs/2505.13417)
- **Code**: [GitHub - THU-KEG/AdaptThink](https://github.com/THU-KEG/AdaptThink)
- **Model**: [HuggingFace Collection](https://huggingface.co/collections/THU-KEG/adaptthink-682a1059aa9f5102c4fa0470)

### Related Work

- **DeepSeek-R1**: Base reasoning model
- **VeRL**: RL training framework
- **vLLM**: Efficient inference engine

---

## Citation

If you find this work helpful, please cite:

```bibtex
@article{zhang2025adapt_think,
  title = {AdaptThink: LLM Can Learn When to Think},
  author = {Jiajie Zhang and Nianyi Lin and Lei Hou and Ling Feng and Juanzi Li},
  journal = {arXiv preprint arXiv:2505.13417},
  url = {https://arxiv.org/abs/2505.13417},
  year = {2025}
}
```

---

## Acknowledgements

This experiment is based on the AdaptThink project by the THU-KEG team at Tsinghua University. We thank the team for open-sourcing the code and models.

**Experiment Log**: This walkthrough is historical context. The canonical W&B-backed step-300 values, provenance, and negative findings are in the training report linked at the top.

---

## 中文

# AdaptThink: 让推理模型学会何时思考

> **历史非规范说明。** 本长篇说明保留作方法背景；其中取整趋势、横向比较和成本估算不属于实验 7-10 的规范结果。若与文首内容冲突，以训练报告及精确 step-300 表格为准。

## 📋 目录

- [项目简介](#项目简介)
- [核心原理](#核心原理)
  - [研究动机](#研究动机)
  - [方法设计](#方法设计)
- [实验设置](#实验设置)
  - [模型与数据](#模型与数据)
  - [训练配置](#训练配置)
- [实验结果分析](#实验结果分析)
  - [整体性能表现](#整体性能表现)
  - [训练过程分析](#训练过程分析)
  - [不同难度的自适应行为](#不同难度的自适应行为)
  - [效率与准确率的权衡](#效率与准确率的权衡)
- [操作指南](#操作指南)
- [关键发现](#关键发现)
- [参考资源](#参考资源)

---

## 项目简介

**AdaptThink** 是一种创新的强化学习算法，旨在教会大型推理模型（Large Reasoning Models, LRMs）根据问题难度**自适应选择推理模式**。

### 背景问题

当前的推理模型（如 OpenAI o1、DeepSeek-R1）在处理问题时会进行长时间的"思考"（Thinking），这种深度推理虽然提升了复杂任务的表现，但也带来了显著问题：

- **高推理成本**：长思考链导致 token 消耗大幅增加
- **高延迟**：即使简单问题也需要冗长的思考过程
- **效率低下**：许多简单问题并不需要复杂推理

### 核心创新

AdaptThink 让模型学会在两种模式间智能切换：

- **Thinking 模式**：生成详细的思考链（`<think>...</think>`）来解决复杂问题
- **NoThinking 模式**：跳过思考过程，直接生成答案来处理简单问题

在保留的 step-300 结果中，这一机制**大幅降低平均响应长度**，但不同数据集的准确率变化有正有负。

---

## 核心原理

### 研究动机

论文首先通过实验发现了一个关键现象：

> **对于相对简单的问题（高中竞赛级别以下），NoThinking 模式的性能与 Thinking 模式相当甚至更优，同时显著减少了 token 使用量。只有当问题足够困难时，Thinking 的优势才会显现。**

这一发现启发了核心研究问题：

**能否让模型自主学习根据问题难度选择最优的推理模式？**

### 方法设计

AdaptThink 通过两个核心组件实现自适应推理：

#### 1. 约束优化目标（Constrained Optimization）

$$\max_{\theta} \mathbb{E}_{x \sim \mathcal{D}, y \sim \pi_\theta(y|x)} [r(x,y)] \quad \text{s.t.} \quad \mathbb{E}_{x \sim \mathcal{D}, y \sim \pi_\theta(y|x)} [r(x,y)] \geq \mathbb{E}_{x \sim \mathcal{D}, y \sim \pi_{\text{ref}}(y|x)} [r(x,y)] - \delta$$

其中：
- $r(x,y)$ 是奖励函数（基于答案准确性）
- $\pi_{\text{ref}}$ 是参考模型（原始推理模型）
- $\delta$ 是允许的性能降幅（本实验设为 0.05）

**核心思想**：在保证整体性能不低于参考模型（允许轻微降幅 $\delta$）的前提下，最大化奖励。下述独立采样策略让训练同时看到 Thinking 与 NoThinking 响应；这里展示的约束目标本身不含 KL 散度项或 token 成本项。

#### 2. 重要性采样策略（Importance Sampling）

在训练过程中，为了平衡 Thinking 和 NoThinking 样本：

- **冷启动阶段**：模型倾向于使用 Thinking（因为这是其预训练行为）
- **采样策略**：引入重要性采样，确保训练过程中既有 Thinking 也有 NoThinking 样本
- **探索与利用**：让模型在整个训练过程中持续探索两种模式

具体实现：对每个问题，同时采样 Thinking 和 NoThinking 响应，并根据其性能动态调整采样权重。

#### 3. NoThinking 实现

通过在输入提示中添加空的 think 标签来实现：

```
User: [问题]
Assistant: <think></think>[直接答案]
```

这种简洁的实现方式利用了模型的预训练知识，让模型理解"跳过思考"的语义。

---

## 实验设置

### 模型与数据

#### 基座模型
- **DeepSeek-R1-Distill-Qwen-1.5B**（本次实验）
- DeepSeek-R1-Distill-Qwen-7B（论文中的对比实验）

#### 训练数据集
- **DeepScaler**：40,000 个数学问题，涵盖从小学到高中竞赛的多个难度级别

#### 评估数据集
- **GSM8K**：小学数学问题
- **MATH500**：竞赛级数学问题（分为 Level 1-5）
- **AIME2024**：美国高中数学竞赛（最难）

### 训练配置

| 参数 | 值 |
|------|------|
| 上下文长度 | 16K tokens |
| 批次大小 | 128 |
| 学习率 | 2e-6 |
| 配置计划 | 10 epochs（计划 3,140 steps）；运行在 step 410 后崩溃 |
| δ（性能容忍度） | 0.05 |
| 硬件配置 | 8 × NVIDIA H100 80GB，CUDA 12.6 |
| 记录时长 | Step 300 为 28.37 小时；至 step 410 为 36.92 小时 |
| 报告选点 | Step 300；checkpoint 不随书分发 |

#### 参考模型预采样

训练前需要对参考模型进行预采样以评估实例级准确率：
- 每个训练问题采样 16 个响应
- 计算每个问题的准确率作为难度指标
- 用于重要性采样的权重计算

---

## 实验结果分析

### 整体性能表现

根据本次实验（1.5B 模型，δ=0.05）的 WandB 监控数据：https://wandb.ai/bojieli-pine-ai/adapt_think_verl/

#### 核心指标对比

| 数据集 | 准确率，step 0 → 300 | 响应长度，step 0 → 300 | Step-300 NoThinking |
|--------|-------------------------|---------------------------|---------------------|
| GSM8K | **0.796816 → 0.818802**（+2.20 pp） | 1025.24 → 477.33（-53.44%） | **84.15%** |
| MATH500 | **0.8100 → 0.8180**（+0.80 pp） | 4911.46 → 1576.62（-67.90%） | **83.80%** |
| AIME2024 mean@16 | **0.314583 → 0.310417**（-0.42 pp） | 12119.51 → 6402.23（-47.17%） | **56.25%** |

**关键成果**：
- **准确率结果有正有负**：MATH500 提升 0.80 pp，GSM8K 提升 2.20 pp，AIME mean@16 下降 0.42 pp
- **效率显著提升**：MATH500、GSM8K、AIME 的平均响应长度分别下降 67.90%、53.44%、47.17%
- **数据集层面的路由信号**：AIME 的 NoThinking 比例为 56.25%，低于 MATH500/GSM8K；这与难度敏感路由一致，但不能证明逐题“完美感知”

### 训练过程分析

#### 1. 响应长度的演变

从 WandB 图表 `response_length/mean` 和各数据集的响应长度可以观察到清晰的三阶段模式：

```
初始阶段 (Step 0-50):
  - 整体平均响应长度：~5,500 tokens
  - MATH500: ~5,000 tokens (几乎全部 Thinking)
  - GSM8K: ~1,600 tokens (几乎全部 Thinking)
  - AIME: ~12,000 tokens (复杂问题的长思考链)
  - 模型延续预训练行为，对所有问题都进行思考

过渡阶段 (Step 50-150):
  - 整体急剧下降至 ~4,000 tokens
  - is_nothinking 比例开始上升（从 0 → 0.5+）
  - NoThinking 准确率快速涌现（MATH500: 0 → 0.8）
  - 模型学习区分问题难度的关键时期

稳定阶段 (Step 150-300):
  - 整体稳定在 ~3,000-3,500 tokens
  - MATH500: 降至 ~1,800 tokens (80% NoThinking)
  - GSM8K: 降至 ~500 tokens (85% NoThinking)
  - AIME: 降至 ~9,000 tokens (55% NoThinking)
  - NoThinking 路由已经形成；不同数据集的准确率并非都持续提升
```

**关键观察**：保留的汇总数据与难度敏感路由一致，但不能证明响应长度与逐题难度完美匹配。

#### 2. 准确率的演变与 NoThinking 能力涌现

**GSM8K（简单数学）**：
- **报告选点 score/mean**：0.796816 → **0.818802**（+2.20 pp）
- **nothinking_acc**：在 Step 150 左右从 0 快速上升至 **0.88-0.90**
- **报告选点 is_nothinking**：**84.15%**
- **关键发现**：step 300 汇总中，84.15% 的 GSM8K 样本使用 NoThinking

**MATH500（中等数学）**：
- **报告选点 score/mean**：0.8100 → **0.8180**（+0.80 pp）
- **thinking_acc**：稳定在 0.5-0.65 之间（模型选择的困难题目）
- **nothinking_acc**：在 Step 150 时快速涌现，从 0 跃升至 **0.8-0.85**（模型选择的简单题目）
- **报告选点 is_nothinking**：**83.80%**
- **关键发现**：step 300 汇总中，83.80% 的 MATH500 样本使用 NoThinking

**AIME2024（困难数学）**：
- **报告选点 score/mean@16**：0.314583 → **0.310417**（-0.42 pp）
- **thinking_acc**：在 0.3-0.7 之间波动较大
- **nothinking_acc**：从 0.3 逐渐提升至 0.4-0.6
- **报告选点 is_nothinking/mean@16**：**56.25%**，低于另外两个数据集
- **关键发现**：报告选点的 AIME 更常使用 Thinking，但准确率略有回退

#### 2.1 NoThinking 能力的涌现现象

从图表 `nothinking_acc/mean` 可以清晰观察到一个令人惊讶的现象：

```
Step 0-150:   nothinking_acc ≈ 0 或未定义（几乎没有 NoThinking 样本）
Step 150:     急剧上升的拐点
Step 150-300: nothinking_acc ≈ 0.8-0.85 (MATH500), 0.88-0.90 (GSM8K)
```

这种**突然涌现**（emergence）表明：
- 模型不是简单地学习"何时跳过思考"
- 而是真正学会了"不思考也能解决简单问题"的能力
- 这是一种高层次的元学习（meta-learning）能力

#### 3. 自适应行为的涌现

从 `is_nothinking/mean` 指标可以看到不同数据集上的自适应行为清晰分层：

```
GSM8K:            84.15% NoThinking  ← 简单问题（小学数学）
MATH500:          83.80% NoThinking  ← 中等难度（高中数学）
AIME2024:         56.25% NoThinking  ← 困难问题（竞赛级）
```

**自适应模式的演变时间线**（以 MATH500 为例）：

```
Step 0-100:   is_nothinking ≈ 0-0.1 (几乎不使用 NoThinking)
Step 100-150: is_nothinking 快速上升 0.1 → 0.6
Step 150:     关键拐点，is_nothinking 跃升至 0.8
Step 150-300: is_nothinking 稳定在 0.78-0.82
```

这一汇总分层与**难度敏感的推理模式选择**一致。由于没有逐题输出，它不能证明每道题的路由均正确，也不能证明 Step 150 发生了因果意义上的能力突变。

#### 4. 历史曲线观察

以下是历史 `adapt_think` 曲线的描述性观察。它们不能覆盖 W&B 最终的 `crashed` 状态，也不能证明因果意义上的训练阶段：

**奖励演变**：
- **thinking_reward/mean**：从负值逐渐上升至接近 0 或正值
- **reward/mean**：在报告选取的区间内总体上升
- **nothinking_reward**：波动较大但总体向上

**Token 概率**：
- **first_eot_token_probs/mean**：从 ~0.2 上升至 **0.6-0.8**
  - 这表示首个结束思考 token 的概率上升
  - 它本身不能证明置信度校准或逐题路由正确

**思考链长度优化**（adapt_think/thinking_response_length）：
- 从 ~9,000 tokens 降至 **~4,500-5,000 tokens**
- Thinking 模式的响应在汇总层面变短
- **观测组合**：部分数据集减少 Thinking 使用，同时 Thinking 响应本身也变短

**响应长度的整体趋势**（response_length）：
- **mean**：5,500 → 3,000 (-45%)
- **min**：稳定在 50-150（最短响应）
- **max**：保持在 16,000-17,000（受响应长度上限限制）
- **clip_ratio**：从约 0.1 降至 **0.02**

### 不同难度的自适应行为

#### MATH500 分难度分析（来自论文）

| 难度级别 | NoThinking 比例 | 准确率变化 |
|---------|----------------|-----------|
| Level 1 | 95% | +3% |
| Level 2 | 88% | +2% |
| Level 3 | 72% | +1% |
| Level 4 | 45% | 持平 |
| Level 5 | 28% | 持平 |

**观察**：
1. **论文报告的单调趋势**：NoThinking 比例随难度增加而递减；这不等于证明“完美感知”
2. **效率与质量平衡**：简单问题大胆使用 NoThinking，困难问题谨慎保留 Thinking
3. **性能保持**：在各类问题上都维持了良好的准确率水平

### 效率与准确率的权衡

#### δ 参数的影响

论文对比了不同 δ 值的效果：

| δ 值 | NoThinking 比例 | 响应长度降低 | 准确率变化 |
|------|----------------|--------------|-----------|
| 0 | 最低 | 较小 | 小幅提升 |
| 0.01 | 中等 | ~40% | 小幅提升 |
| 0.02 | 较高 | ~50% | 持平 |
| **0.05** | **~80%** | **~53%** | **+2.4%** |
| 0.075 | 更高 | ~60% | 可能下降 |
| 0.1 | 最高 | 最大 | 轻微下降 |

**δ=0.05 的历史论文层面理由**：上表是横向比较背景，并非本次保留运行的精确 step-300 结果。规范运行中三个数据集的平均响应长度均下降，但准确率有正有负，AIME 下降 0.42 pp。

---

## 操作指南

### 环境配置

```bash
# 创建环境
conda create -n adapt_think python=3.13
conda activate adapt_think

# 安装依赖
cd chapter7/AdaptThink-original
pip install -r requirements.txt
pip install flash-attn --no-build-isolation
```

### 数据准备

#### 1. 预采样参考响应

```bash
# 启动 vLLM 服务器
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B \
  --served_model_name DeepSeek-R1-Distill-Qwen-1.5B \
  --tensor_parallel_size 4

# 采样 16 个响应
python src/presampling_ref_responses.py \
  --K 16 \
  --dataset_path ./data/train/deepscaler.json \
  --model_name DeepSeek-R1-Distill-Qwen-1.5B \
  --max_tokens 16384

# 后处理得到实例级准确率
python src/postprocess_ref_results.py \
  --input_path ./data/train/ref_presampling/DeepSeek-R1-Distill-Qwen-1.5B_deepscaler_n0_K16_len16384.json \
  --output_path ./data/train/ref_results/DeepSeek-R1-Distill-Qwen-1.5B_deepscaler_K16_len16384.json
```

**注意**：项目已提供预处理好的结果在 `./data/train/ref_results`，可直接使用。

#### 2. 预处理数据集

```bash
bash scripts/preprocess_dataset.sh
```

### 训练

```bash
# 1.5B 模型，单节点
bash scripts/run_adapt_think_1.5b_deepscaler_16k_delta0.05_btz128_lr2e-6.sh
```

**训练监控**：
- VeRL 会自动在 WandB 上记录训练指标
- 每 `trainer.test_freq` 步自动评估测试集
- 关键监控指标：
  - `val-aux/gsm8k/score/mean`：GSM8K 准确率
  - `val-aux/math/score/mean`：MATH500 准确率
  - `response_length/mean`：平均响应长度
  - `adapt_think/is_nothinking/mean`：NoThinking 比例
  - `adapt_think/thinking_response_length/mean`：思考链长度

### 评估

下述命令是上游宣传的工作流，不是成功评估所选 checkpoint 的回执。使用前须修正 `-fl-` 与 `-fl4096` 的实验名差异，以及缺失的 `adapt_think_verl/` 目录层级。

```bash
# 转换检查点为 HF 格式
bash scripts/convert_to_hf.sh

# 运行评估
bash scripts/run_eval_verl_hf.sh

# 或直接评估已发布的 HF 模型
bash scripts/run_eval_hf.sh
```

---

## 关键发现

### 1. NoThinking 的有效性

**关键发现**：step 300 时，GSM8K 和 MATH500 使用 NoThinking 的比例高于 AIME2024。

**观察**：
- 被路由到 NoThinking 的子集在汇总层面仍有较高准确率
- 三个数据集上的 NoThinking 响应均短于 Thinking 响应
- 由于没有保留逐题输出，报告无法判断每个路由选择是否正确

### 2. 自适应行为的涌现

step 300 的汇总结果在没有显式难度标签的情况下呈现出跨数据集的路由梯度：

```
简单问题 (GSM8K):     "简单算术"       → NoThinking (85%)
中等问题 (MATH500):   "高中数学"       → NoThinking (80%)
困难问题 (AIME):      "竞赛级问题"     → 混合使用 (55%)
```

### 3. 效率提升与有正有负的准确率

在报告选点，AdaptThink 降低了三个保留数据集的平均响应长度，但准确率变化有正有负：

- **效率大幅提升**：
  - GSM8K: 响应长度降低 **53.44%**（1025.24 → 477.33）
  - MATH500: 响应长度降低 **67.90%**（4911.46 → 1576.62）
  - AIME: 响应长度降低 **47.17%**（12119.51 → 6402.23）

- **准确率有正有负**：
  - MATH500: 准确率 **0.8100 → 0.8180**（+0.80 pp）
  - GSM8K: 准确率 **0.796816 → 0.818802**（+2.20 pp）
  - AIME mean@16: 准确率 **0.314583 → 0.310417**（-0.42 pp）

- **原因**：
  - 针对性使用推理资源，简单问题快速决策
  - Thinking 本身也变得更简洁（从 9K → 5K tokens）
  - 避免过度思考导致的错误累积

### 4. 训练稳定性与关键拐点

历史 W&B 曲线在 step 150 左右出现明显的汇总路由变化。运行后来在 step 410 后崩溃，因此不能描述为完整结束或全程稳定的训练。

**Step 150 - 描述性路由拐点**：
- 验证集 **is_nothinking** 明显上升
- 验证集 **nothinking_acc** 从接近 0 升至约 0.8-0.9
- 平均响应长度开始快速下降
- **first_eot_token_probs** 上升

训练配置在优化期间强制平衡采样 Thinking/NoThinking。验证曲线只是观察结果，不能证明发生了“相变”，也不能保证每个数据集都不回退；AIME 在 step 300 的准确率略低于基线。

---

## 与现有方法的对比

| 方法 | 核心思路 | 响应长度降低 | 准确率变化 | 自适应性 |
|------|---------|-------------|-----------|---------|
| **基线模型** | 所有问题都思考 | 0% | - | ❌ |
| **Length Reward** | RL 中加入长度惩罚 | ~30% | 持平/下降 | ❌ |
| **DPO (短偏好)** | 偏好短响应的对齐 | ~35% | 持平 | ❌ |
| **模型合并** | 推理/非推理模型融合 | ~25% | 持平 | 部分 |
| **AdaptThink** | 自适应模式选择 | **45-69%** | **+2-10%** | ✅ |

**本次实验（1.5B, δ=0.05）的具体数据**：
- GSM8K: 响应长度 ↓53.44%，准确率 +2.20 pp，84.15% NoThinking
- MATH500: 响应长度 ↓67.90%，准确率 +0.80 pp，83.80% NoThinking
- AIME mean@16: 响应长度 ↓47.17%，准确率 -0.42 pp，56.25% NoThinking

**AdaptThink 的独特优势**：
- **仅属论文层面比较**：保留运行不能独立证明 AdaptThink 是唯一同时改善两个维度的方法
- **汇总自适应信号**：AIME 的 NoThinking 使用率低于 MATH500/GSM8K
- ✅ **双重优化**：减少 Thinking 使用 + 优化 Thinking 本身
- **观测到的路由变化**：保留运行中期的 NoThinking 汇总指标发生明显变化
- ✅ **无需额外模型**：单一模型即可实现混合推理

---

## 实验环境与成本

### 硬件需求

**训练**：
- 保留的 1.5B W&B 运行：8 × NVIDIA H100 80GB；step 300 为 28.37 小时，step 410 为 36.92 小时
- 原说明中的 7B 资源数据属于论文背景，本次保留运行不能验证

**推理**：
- 可使用单张 GPU（根据模型大小）
- vLLM 加速推理

### 计算成本估算

以 1.5B 模型为例：
- **观测训练资源**：8×H100；到报告选点的墙钟时间为 28.37 小时，到最后记录 step 的时间为 36.92 小时
- **推理成本节省**：
  - GSM8K：step 300 的平均响应长度下降 53.44%
  - MATH500：step 300 的平均响应长度下降 67.90%
  - AIME2024：step 300 的平均响应长度下降 47.17%
- **边界**：token 降幅本身不能证明成比例的延迟加速或特定 ROI

---

## 局限性与未来方向

### 当前局限

1. **领域限制**：主要在数学任务上验证，其他领域需进一步测试
2. **δ 调优**：不同任务可能需要不同的 δ 值
3. **冷启动**：需要参考模型的预采样，增加了准备成本
4. **可解释性**：模型如何判断难度仍是黑盒

### 未来方向

1. **多级推理**：不只是 Thinking/NoThinking 二选一，可以有"浅层思考"、"深度思考"等多级
2. **在线适应**：根据实时反馈动态调整推理深度
3. **跨领域泛化**：在代码、推理、创意写作等更多任务上验证
4. **用户可控**：允许用户指定推理深度偏好

---

## 参考资源

### 论文与代码

- **论文**：[AdaptThink: LLM Can Learn When to Think](https://arxiv.org/abs/2505.13417)
- **代码**：[GitHub - THU-KEG/AdaptThink](https://github.com/THU-KEG/AdaptThink)
- **模型**：[HuggingFace Collection](https://huggingface.co/collections/THU-KEG/adaptthink-682a1059aa9f5102c4fa0470)

### 相关工作

- **DeepSeek-R1**：基座推理模型
- **VeRL**：RL 训练框架
- **vLLM**：高效推理引擎

---

## 引用

如果您觉得这项工作有帮助，请引用：

```bibtex
@article{zhang2025adapt_think,
  title = {AdaptThink: LLM Can Learn When to Think},
  author = {Jiajie Zhang and Nianyi Lin and Lei Hou and Ling Feng and Juanzi Li},
  journal = {arXiv preprint arXiv:2505.13417},
  url = {https://arxiv.org/abs/2505.13417},
  year = {2025}
}
```

---

## 致谢

本实验基于清华大学 THU-KEG 团队的 AdaptThink 项目，感谢团队开源的代码和模型。

**实验记录**：本长篇说明仅作历史背景。规范的 W&B step-300 数值、来源和负面证据以文首链接的历史训练报告为准。
