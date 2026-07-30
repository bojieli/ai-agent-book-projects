---
theme: default
title: "Attention Is All You Need"
author: "Ashish Vaswani et al."
---

# Attention Is All You Need

**Authors:** Ashish Vaswani et al.  
**Conference:** NIPS 2017

---

## Abstract

- Proposes **Transformer** - a new network architecture based solely on attention
- Dispenses with recurrence and convolutions entirely
- More parallelizable and requires significantly less training time
- Achieves state-of-the-art results on machine translation tasks:
  - 28.4 BLEU on WMT 2014 English-to-German
  - 41.8 BLEU on WMT 2014 English-to-French
- Generalizes well to other tasks like English constituency parsing

---

## Background: Sequence Modeling Challenges

### Traditional Approaches
- **Recurrent models** (LSTM, GRU) process input sequentially
- **Convolutional models** have limited receptive fields
- Both struggle with:
  - Long-range dependencies
  - Parallelization
  - Computational efficiency for long sequences

---

## The Need for a New Architecture

### Key Limitations of Existing Models
- **Recurrent networks**: Inherently sequential computation
- **Convolutional networks**: Limited long-range connectivity
- **Hybrid models**: Still rely on recurrence/convolution as primary components

### Attention Mechanisms
- Already used as auxiliary component in sequence models
- Allows modeling dependencies without regard to position distance
- Not yet used as the primary architectural component

---

## The Transformer: Model Architecture

<img src="/paper_figure_1_transformer.png" class="h-76 mx-auto" />

*Encoder-decoder structure using stacked self-attention and feed-forward layers*

---

## Encoder Architecture

- **Stack of 6 identical layers**
- Each layer contains two sub-layers:
  1. Multi-head self-attention mechanism
  2. Position-wise fully connected feed-forward network
- Residual connections around each sub-layer
- Layer normalization: `LayerNorm(x + Sublayer(x))`
- Output dimension: `d_model = 512`

---

## Decoder Architecture

- **Stack of 6 identical layers**
- Each layer contains three sub-layers:
  1. Masked multi-head self-attention
  2. Multi-head attention over encoder output
  3. Position-wise fully connected feed-forward network
- Residual connections and layer normalization
- Masking prevents attending to future positions

---

## Attention Mechanism Basics

### Definition
An attention function maps a query and key-value pairs to an output:
- Query (Q), Keys (K), Values (V) are vectors
- Output is weighted sum of values
- Weights determined by compatibility of query with corresponding key

### Two Common Types
- Additive attention (feed-forward network)
- Dot-product attention (scaled in Transformer)

---

## Scaled Dot-Product Attention

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

- Computes dot products of query with all keys
- Scales by $\sqrt{d_k}$ to prevent gradient vanishing
- Applies softmax to get weights over values
- More efficient than additive attention (matrix operations)

---

## Multi-Head Attention