---
theme: default
title: 'Attention Is All You Need'
author: 'Ashish Vaswani et al.'
date: 'NIPS 2017'
---

# Attention Is All You Need

**Authors:** Ashish Vaswani et al.  
**Conference:** NIPS 2017

---

## Abstract

### Key Innovation
- First sequence transduction model based **solely on attention**
- Dispenses with recurrence and convolutions entirely
- More parallelizable with significantly less training time

### Performance Highlights
- **WMT 2014 EN-DE**: 28.4 BLEU (+2+ over previous SOTA)
- **WMT 2014 EN-FR**: 41.8 BLEU (new single-model SOTA)
- Trained in 3.5 days on 8 GPUs (small fraction of previous costs)

---

## Background & Key Idea

### Traditional Sequence Models
- **Recurrent (LSTM/GRU)**: Sequential computation limits parallelization
- **Convolutional**: Requires multiple layers for long-range dependencies

### The Transformer
- Replaces recurrence/convolution with **self-attention**
- Enables direct modeling of long-range dependencies
- Massive parallelization → faster training

---

## Transformer Architecture

<img src="/paper_figure_1_transformer.png" class="h-[600px] w-full object-contain" />

---

## Encoder Stack

- **6 identical layers** with two sub-layers:
  1. Multi-head self-attention mechanism
  2. Position-wise feed-forward network
- Residual connections around each sub-layer
- Layer normalization after each sub-layer
- Output dimension: `d_model = 512`

---

## Decoder Stack

- **6 identical layers** with three sub-layers:
  1. Masked multi-head self-attention (prevents leftward flow)
  2. Multi-head attention over encoder output
  3. Position-wise feed-forward network
- Same residual connections and normalization as encoder
- Output embeddings offset by one position (auto-regressive property)

---

## Attention Mechanism

### Scaled Dot-Product Attention
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$
- Scaling by $\sqrt{d_k}$ prevents small gradients
- Efficient with matrix multiplication

### Multi-Head Attention
$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1,...,\text{head}_h)W^O$$
- $h=8$ parallel heads, $d_k=d_v=64$
- Captures diverse dependency patterns

---

## Attention Applications

1. **Encoder-decoder attention**: Queries from decoder, keys/values from encoder  
2. **Encoder self-attention**: All positions attend to all input positions  
3. **Decoder self-attention**: Positions attend to previous positions (masked)  

---

## Positional Encoding

Adds sequence position information via sinusoidal functions:
$$\text{PE}_{(pos,2i)}=\sin(pos/10000^{2i/d_{\text{model}}})$$
$$\text{PE}_{(pos,2i+1)}=\cos(pos/10000^{2i/d_{\text{model}}})$$

- Same dimension as embeddings ($d_{\text{model}}$)
- Enables learning of relative positions
- Performs similarly to learned embeddings

---

## Why Self-Attention?

| Layer Type       | Complexity       | Sequential Ops | Max Path Length |
|------------------|------------------|----------------|-----------------|
| Self-Attention   | $O(n^2 \cdot d)$ | $O(1)$         | $O(1)$          |
| Recurrent        | $O(n \cdot d^2)$ | $O(n)$         | $O(n)$          |
| Convolutional    | $O(k \cdot n \cdot d^2)$ | $O(1)$ | $O(\log_k n)$   |

- Better parallelization than RNNs
- Shorter path length than CNNs
- More interpretable attention patterns

---

## Training Data & Batching

- **Datasets**:
  - WMT 2014 EN-DE (4.5M sentence pairs)
  - WMT 2014 EN-FR (36M sentence pairs)
- **Tokenization**:
  - Byte-pair encoding with shared vocabulary
  - 37K tokens (EN-DE), 32K tokens (EN-FR)
- **Batching**:
  - Sentences grouped by approximate length
  - Each batch contains ~25K source and target tokens

---

## Training Hardware & Schedule

- **Hardware**: 8 NVIDIA P100 GPUs
- **Base model**:
  - 100,000 training steps
  - ~12 hours total training time
- **Big model**:
  - 300,000 training steps
  - ~3.5 days total training time

---

## Training Optimization

- **Optimizer**: Adam
  - $\beta_1 = 0.9$, $\beta_2 = 0.98$, $\epsilon = 10^{-9}$
  - Learning rate schedule with warmup steps=4000

- **Regularization**:
  - Residual dropout (P_drop = 0.1)
  - Label smoothing ($\epsilon_{ls} = 0.1$)
  - Dropout on embeddings + positional encodings

---

## Machine Translation Results

| Model                | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|----------------------|------------|------------|-----------------------|
| GNMT + RL Ensemble   | 26.30      | 41.16      | $1.8 \cdot 10^{20}$   |
| ConvS2S Ensemble     | 26.36      | 41.29      | $7.7 \cdot 10^{19}$   |
| **Transformer (big)**| **28.4**   | **41.8**   | **$2.3 \cdot 10^{19}$**|

- Outperforms all previous SOTA with lower training cost

---

## Attention Visualization: Long-Distance Dependencies

<img src="/paper_figure_3_long_distance.png" class="h-[600px] w-full object-contain" />

*Tracking "making...more difficult" dependency across distant positions*

---

## Attention Visualization: Anaphora Resolution

<img src="/paper_figure_4_anaphora.png" class="h-[600px] w-full object-contain" />

*Resolving "its" to antecedent "The Law"*

---

## Key Contributions

- Introduced Transformer, first attention-only transduction model
- Eliminated recurrence/convolution → better parallelization
- Set new SOTA in machine translation with lower training cost
- Generalizes to other tasks (e.g., constituency parsing)

---

## Future Work

- Apply to other modalities (images, audio, video)
- Explore local attention for large sequences
- Improve generation sequentiality
- Enhance attention interpretability

**Code:** https://github.com/tensorflow/tensor2tensor