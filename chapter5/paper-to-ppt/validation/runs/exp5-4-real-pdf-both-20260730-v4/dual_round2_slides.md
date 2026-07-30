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

<img src="/paper_figure_1_transformer.png" class="h-96 mx-auto" />

*Encoder (left) and Decoder (right) with self-attention and feed-forward layers*

---

## Encoder & Decoder Stacks

### Encoder (6 identical layers)
- **Sub-layer 1**: Multi-head self-attention
- **Sub-layer 2**: Position-wise feed-forward network
- Residual connections + layer normalization
- Output dimension: `d_model = 512`

### Decoder (6 identical layers)
- **Sub-layer 1**: Masked multi-head self-attention (prevents leftward flow)
- **Sub-layer 2**: Multi-head attention over encoder output
- **Sub-layer 3**: Position-wise feed-forward network
- Same residual connections and normalization

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

## Training Setup

### Data & Batching
- WMT 2014 EN-DE (4.5M pairs), EN-FR (36M pairs)
- Byte-pair encoding (37K/32K vocab)
- Batches with ~25K source/target tokens

### Hardware & Schedule
- 8 NVIDIA P100 GPUs
- Base model: 100K steps (12h), Big model: 300K steps (3.5d)

### Optimization
- Adam ($\beta_1=0.9$, $\beta_2=0.98$), learning rate warmup
- Dropout (0.1), label smoothing (0.1)

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

<img src="/paper_figure_3_long_distance.png" class="h-96 w-full object-contain" />

*Encoder self-attention (layer 5) tracking "making...more difficult" dependency*

---

## Attention Visualization: Anaphora Resolution

<img src="/paper_figure_4_anaphora.png" class="h-96 w-full object-contain" />

*Attention heads resolving "its" to "The Law"*

---

## Conclusion & Future Work

### Key Contributions
- Introduced Transformer, first attention-only transduction model
- Eliminated recurrence/convolution → better parallelization
- Set new SOTA in machine translation with lower training cost
- Generalizes to other tasks (e.g., constituency parsing)

### Future Work
- Apply to other modalities (images, audio)
- Explore local attention for large sequences
- Improve generation sequentiality
- Enhance attention interpretability

**Code:** https://github.com/tensorflow/tensor2tensor