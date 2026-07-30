---
theme: default
title: "Attention Is All You Need"
author: "Ashish Vaswani et al."
---

# Attention Is All You Need

**Authors:** Ashish Vaswani et al.  
**Conference:** NIPS 2017

---

## Abstract: Key Innovation

- Proposes **Transformer** - first architecture based solely on attention
- Dispenses with recurrence and convolutions entirely
- More parallelizable and requires significantly less training time
- Generalizes well to other tasks beyond machine translation

---

## Abstract: Performance Highlights

- **WMT 2014 English-to-German**: 28.4 BLEU
  - Improves over existing best results by over 2 BLEU
- **WMT 2014 English-to-French**: 41.8 BLEU
  - New single-model state-of-the-art
  - Trained for 3.5 days on eight GPUs (small fraction of previous costs)

---

## Background: Traditional Sequence Modeling

### Recurrent Models
- LSTM and GRU as state-of-the-art approaches
- Factor computation along symbol positions
- Inherently sequential nature precludes parallelization

### Convolutional Models
- Fixed receptive fields limit long-range dependencies
- Computational complexity grows with distance between positions

---

## Limitations of Existing Approaches

- **Recurrent networks**: Sequential computation limits parallelization
- **Convolutional networks**: Difficulty modeling long-range dependencies
- **Hybrid models**: Still rely on recurrence/convolution as primary components
- **Attention mechanisms**: Previously used only as auxiliary component

---

## The Transformer: Model Architecture

<img src="/paper_figure_1_transformer.png" class="h-80 mx-auto" />

---

## Encoder Architecture

- **Stack of 6 identical layers**
- Each layer contains two sub-layers:
  1. Multi-head self-attention mechanism
  2. Position-wise fully connected feed-forward network
- Residual connections around each sub-layer
- Layer normalization: `LayerNorm(x + Sublayer(x))`

---

## Encoder: Key Details

- All sub-layers produce outputs of dimension `d_model = 512`
- Self-attention allows each position to attend to all positions
- Feed-forward network applied to each position separately
- Residual connections help with gradient flow in deep networks

---

## Decoder Architecture

- **Stack of 6 identical layers**
- Each layer contains three sub-layers:
  1. Masked multi-head self-attention
  2. Multi-head attention over encoder output
  3. Position-wise fully connected feed-forward network
- Residual connections and layer normalization

---

## Decoder: Masking Mechanism

- **Masked self-attention** prevents positions from attending to subsequent positions
- Ensures predictions for position i depend only on:
  - Known outputs at positions less than i
  - Input sequence through encoder-decoder attention
- Output embeddings offset by one position to maintain auto-regressive property

---

## Attention Mechanism: Definition

Maps a query and key-value pairs to an output:
- Query (Q), Keys (K), Values (V) are vectors
- Output is weighted sum of values
- Weights determined by query-key compatibility

---

## Scaled Dot-Product Attention

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

- Computes dot products of query with all keys
- Scales by $\sqrt{d_k}$ to prevent gradient vanishing
- Applies softmax to get weights over values
- More efficient than additive attention

---

## Multi-Head Attention

- Projects Q, K, V h times with different learned projections
- Performs attention in parallel on each projected version
- Concatenates outputs and applies final projection