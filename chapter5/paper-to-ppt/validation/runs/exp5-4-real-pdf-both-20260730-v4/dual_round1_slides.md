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

- Proposes **Transformer** - a new network architecture based solely on attention
- Dispenses with recurrence and convolutions entirely
- More parallelizable and requires significantly less training time
- State-of-the-art results:
  - 28.4 BLEU on WMT 2014 English-to-German
  - 41.8 BLEU on WMT 2014 English-to-French
- Generalizes well to other tasks like English constituency parsing

---

## Background & Key Idea

### Traditional Sequence Models
- **Recurrent models** (LSTM, GRU): Sequential computation, limited parallelization
- **Convolutional models**: Limited long-range dependencies

### Attention Mechanism
- Already used with recurrent networks
- Allows modeling dependencies without regard to distance

### The Transformer
- **Key innovation**: Replace recurrence and convolution with self-attention
- Enables more parallelization and better long-range dependencies

---

## Transformer Architecture

<img src="/paper_figure_1_transformer.png" class="h-80 mx-auto" />

*Encoder (left) and Decoder (right) stacks with self-attention and feed-forward layers*

---

## Encoder & Decoder Stacks

### Encoder
- **6 identical layers** each with:
  1. Multi-head self-attention mechanism
  2. Position-wise fully connected feed-forward network
- Residual connections + layer normalization
- Output dimension: `d_model = 512`

### Decoder
- **6 identical layers** each with:
  1. Masked multi-head self-attention (prevents leftward flow)
  2. Multi-head attention over encoder output
  3. Position-wise feed-forward network
- Same residual connections and layer normalization

---

## Attention Mechanism

### Scaled Dot-Product Attention
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

- $Q$ (queries), $K$ (keys), $V$ (values) are matrices
- Scaling by $\sqrt{d_k}$ prevents gradients from becoming too small
- More efficient than additive attention

---

## Multi-Head Attention

- Projects queries, keys, values $h$ times with different linear projections
- Performs attention in parallel on each projected version
- Concatenates results and projects again:

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$$

- $h = 8$ heads, $d_k = d_v = d_{\text{model}}/h = 64$

### Applications
1. **Encoder-decoder attention**: Queries from decoder, keys/values from encoder
2. **Encoder self-attention**: All positions attend to all positions
3. **Decoder self-attention**: Positions attend to previous positions (masked)

---

## Positional Encoding

Since there's no recurrence/convolution, we add positional information:

$$\text{PE}_{(pos, 2i)} = \sin\left(pos / 10000^{2i/d_{\text{model}}}\right)$$
$$\text{PE}_{(pos, 2i+1)} = \cos\left(pos / 10000^{2i/d_{\text{model}}}\right)$$

- Same dimension as embeddings ($d_{\text{model}}$)
- Allows model to learn relative position information
- Performed similarly to learned positional embeddings

---

## Why Self-Attention?

| Layer Type | Complexity | Sequential Operations | Max Path Length |
|------------|------------|-----------------------|-----------------|
| Self-Attention | $O(n^2 \cdot d)$ | $O(1)$ | $O(1)$ |
| Recurrent | $O(n \cdot d^2)$ | $O(n)$ | $O(n)$ |
| Convolutional | $O(k \cdot n \cdot d^2)$ | $O(1)$ | $O(\log_k n)$ |

- Better parallelization than RNNs
- Shorter path length than CNNs/RNNs
- More interpretable attention distributions

---

## Training Details

### Data & Batching
- WMT 2014 English-German (4.5M pairs), English-French (36M pairs)
- Byte-pair encoding with shared vocabulary
- Batches with ~25,000 source and target tokens

### Hardware & Schedule
- 8 NVIDIA P100 GPUs
- Base model: 100,000 steps (12 hours)
- Big model: 300,000 steps (3.5 days)

### Optimizer & Regularization
- Adam with $\beta_1=0.9$, $\beta_2=0.98$, $\epsilon=10^{-9}$
- Learning rate schedule with warmup steps=4000
- Residual dropout (P_drop=0.1) and label smoothing ($\epsilon_{ls}=0.1$)

---

## Machine Translation Results

| Model | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|-------|------------|------------|-----------------------|
| GNMT + RL Ensemble | 26.30 | 41.16 | $1.8 \cdot 10^{20}$ |
| ConvS2S Ensemble | 26.36 | 41.29 | $7.7 \cdot 10^{19}$ |
| **Transformer (big)** | **28.4** | **41.8** | **$2.3 \cdot 10^{19}$** |

- Transformer outperforms all previous state-of-the-art models
- Achieves better results with significantly lower training cost
- 2+ BLEU improvement on English-to-German

---

## Model Architecture Ablations

| Variation | Dev PPL | Dev BLEU |
|-----------|---------|----------|
| Base model | 4.92 | 25.8 |
| (A) 1 attention head | 5.29 | 24.9 |
| (B) d_k = 16 | 5.75 | 24.5 |
| (C) 2 layers | 6.11 | 23.7 |
| (D) No dropout | 5.77 | 24.6 |
| (E) Learned positional embeddings | 4.92 | 25.7 |

- Multi-head attention improves performance
- Dropout is crucial for avoiding overfitting
- Sinusoidal and learned positional encodings perform similarly

---

## English Constituency Parsing

| Parser | Training | WSJ 23 F1 |
|--------|----------|-----------|
| Petrov et al. (2006) | WSJ only | 90.4 |
| Dyer et al. (2016) | WSJ only | 91.7 |
| **Transformer (4 layers)** | **WSJ only** | **91.3** |
| Vinyals & Kaiser et al. (2014) | Semi-supervised | 92.1 |
| **Transformer (4 layers)** | **Semi-supervised** | **92.7** |

- Transformer generalizes well to other sequence tasks
- Performs comparably to state-of-the-art parsers
- Better than RNN models in small-data regimes

---

## Attention Visualization: Long-Distance Dependencies

<img src="/paper_figure_3_long_distance.png" class="h-70 mx-auto" />

*Encoder self-attention in layer 5 showing attention to distant dependency "making...more difficult"*

---

## Attention Visualization: Anaphora Resolution

<img src="/paper_figure_4_anaphora.png" class="h-70 mx-auto" />

*Attention heads focusing on resolving "its" to "The Law"*

---

## Conclusion & Future Work

### Contributions
- Introduced **Transformer**, first transduction model based entirely on attention
- Eliminated recurrence and convolution
- Achieved new state-of-the-art in machine translation
- More parallelizable and faster to train
- Generalizes well to other tasks

### Future Work
- Apply to other modalities (images, audio, video)
- Investigate local, restricted attention mechanisms
- Make generation less sequential
- Explore interpretability of attention patterns

**Code available at:** https://github.com/tensorflow/tensor2tensor