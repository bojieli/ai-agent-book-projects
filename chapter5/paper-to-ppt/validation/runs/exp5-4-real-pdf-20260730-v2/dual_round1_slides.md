---
theme: default
---

# Attention Is All You Need
## A Revolutionary Architecture for Sequence Transduction

Ashish Vaswani et al.  
NIPS 2017

---

## Abstract

- Proposes **Transformer** - first model based solely on attention mechanisms
- Dispenses with recurrence and convolutions entirely
- Superior quality while being more parallelizable and requiring less training time
- Achieves 28.4 BLEU on WMT 2014 English-to-German (↑2 BLEU over previous best)
- Achieves 41.8 BLEU on WMT 2014 English-to-French (new state-of-the-art)
- Generalizes well to other tasks like English constituency parsing

---

## Background: The Problem with Existing Approaches

### Recurrent Neural Networks (RNNs/LSTMs/GRUs)
- Inherently sequential computation
- Cannot parallelize within training examples
- Difficult to learn long-range dependencies

### Convolutional Approaches
- ByteNet, ConvS2S use CNNs for parallelization
- Number of operations grows with distance between positions
- Linear (ConvS2S) or logarithmic (ByteNet) path lengths

---

## Key Insight: Attention is Sufficient

Attention mechanisms allow modeling dependencies without regard to distance, but were previously used with RNNs.

**Transformer**: First transduction model relying entirely on self-attention to compute representations without:
- Sequence-aligned RNNs
- Convolutions

---

## Transformer Architecture Overview

<img src="/paper_figure_1_transformer.png" class="h-80 mx-auto" />

*Encoder-decoder structure with stacked self-attention and feed-forward layers*

---

## Encoder Structure

- Stack of **6 identical layers**
- Each layer has two sub-layers:
  1. **Multi-head self-attention** mechanism
  2. **Position-wise fully connected feed-forward network**
- Residual connections around each sub-layer
- Layer normalization after each sub-layer
- All sub-layers produce outputs of dimension `d_model = 512`

---

## Decoder Structure

- Stack of **6 identical layers**
- Three sub-layers per layer:
  1. Masked multi-head self-attention (prevents leftward information flow)
  2. Multi-head attention over encoder output
  3. Position-wise fully connected feed-forward network
- Residual connections and layer normalization
- Output embeddings offset by one position (auto-regressive property)

---

## Attention Mechanism

### Scaled Dot-Product Attention
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

- $Q$ (queries), $K$ (keys), $V$ (values) are matrices
- Scaling by $\frac{1}{\sqrt{d_k}}$ prevents gradients from becoming too small
- Faster and more space-efficient than additive attention

---

## Multi-Head Attention

<img src="/paper_figure_1_transformer.png" class="h-40 mx-auto" />

- Projects queries, keys, values $h$ times with different learned projections
- Performs attention in parallel on projected versions
- Concatenates results and projects again

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$$
where $\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$

---

## Three Applications of Attention

1. **Encoder-decoder attention**: Queries from decoder, keys/values from encoder
2. **Encoder self-attention**: All keys, values, queries from previous encoder layer
3. **Decoder self-attention**: All positions in decoder up to current position (masked)

---

## Positional Encoding

Since model has no recurrence/convolution, we inject positional information:

$$\text{PE}_{(pos, 2i)} = \sin\left(pos / 10000^{2i/d_{\text{model}}}\right)$$
$$\text{PE}_{(pos, 2i+1)} = \cos\left(pos / 10000^{2i/d_{\text{model}}}\right)$$

- Same dimension as embeddings ($d_{\text{model}}$)
- Allows model to learn relative position information
- Performed nearly as well as learned positional embeddings

---

## Why Self-Attention?

| Layer Type | Complexity | Sequential Operations | Max Path Length |
|------------|------------|-----------------------|-----------------|
| Self-Attention | $O(n^2 \cdot d)$ | $O(1)$ | $O(1)$ |
| Recurrent | $O(n \cdot d^2)$ | $O(n)$ | $O(n)$ |
| Convolutional | $O(k \cdot n \cdot d^2)$ | $O(1)$ | $O(\log_k n)$ |

- Constant path length between any positions
- More parallelizable than RNNs
- Better computational efficiency for typical sentence lengths

---

## Training Details

### Data & Batching
- WMT 2014 English-German (4.5M sentence pairs)
- WMT 2014 English-French (36M sentence pairs)
- Byte-pair encoding (37K shared vocab for EN-DE)
- Batches with ~25000 source and target tokens

### Hardware & Schedule
- 8 NVIDIA P100 GPUs
- Base model: 100,000 steps (12 hours)
- Big model: 300,000 steps (3.5 days)

---

## Training Details (Cont.)

### Optimizer
- Adam with $\beta_1 = 0.9$, $\beta_2 = 0.98$, $\epsilon = 10^{-9}$
- Learning rate schedule:
  $$\text{lrate} = d_{\text{model}}^{-0.5} \cdot \min(\text{step\_num}^{-0.5}, \text{step\_num} \cdot \text{warmup\_steps}^{-1.5})$$
- Warmup steps = 4000

### Regularization
- Residual dropout (P_drop = 0.1)
- Label smoothing ($\epsilon_{ls} = 0.1$)

---

## Machine Translation Results

| Model | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|-------|------------|------------|-----------------------|
| GNMT + RL Ensemble | 26.30 | 41.16 | $1.8 \cdot 10^{20}$ |
| ConvS2S Ensemble | 26.36 | 41.29 | $7.7 \cdot 10^{19}$ |
| **Transformer (big)** | **28.4** | **41.8** | **$2.3 \cdot 10^{19}$** |

- Transformer outperforms all previous state-of-the-art models
- Achieves better results with significantly lower training cost
- 28.4 BLEU on EN-DE (↑2 BLEU over previous best)
- 41.8 BLEU on EN-FR (new state-of-the-art)

---

## Model Variations Analysis

| Variation | Dev PPL | Dev BLEU |
|-----------|---------|----------|
| Base model | 4.92 | 25.8 |
| Single attention head | 5.29 | 24.9 |
| No dropout | 5.77 | 24.6 |
| Learned positional embeddings | 4.92 | 25.7 |
| Big model | 4.33 | 26.4 |

- Multiple attention heads improve performance
- Dropout is crucial for avoiding overfitting
- Sinusoidal and learned positional encodings perform similarly
- Larger models (more dimensions, more heads) improve performance

---

## Generalization to Other Tasks: English Constituency Parsing

| Parser | Training | WSJ 23 F1 |
|--------|----------|-----------|
| Petrov et al. (2006) | WSJ only | 90.4 |
| Dyer et al. (2016) | WSJ only | 91.7 |
| **Transformer (4 layers)** | **WSJ only** | **91.3** |
| Vinyals & Kaiser et al. | Semi-supervised | 92.1 |
| **Transformer (4 layers)** | **Semi-supervised** | **92.7** |

- Transformer performs well despite no task-specific tuning
- Outperforms previous models in semi-supervised setting
- Shows generalization ability beyond machine translation

---

## Attention Visualization: Long-Distance Dependencies

<img src="/paper_figure_3_long_distance.png" class="h-70 mx-auto" />

*Encoder self-attention in layer 5 showing attention to distant dependency of the verb "making"*

---

## Attention Visualization: Anaphora Resolution

<img src="/paper_figure_4_anaphora.png" class="h-70 mx-auto" />

*Attention heads involved in resolving "its" reference to "The Law"*

---

## Limitations

- Computational complexity grows quadratically with sequence length
- Less effective for very long sequences (e.g., books, articles)
- Still requires sequential generation in decoder
- Limited ability to model hierarchical structure compared to some syntactic models

---

## Conclusion and Future Work

### Key Contributions
- Introduced Transformer architecture based solely on attention
- Achieved new state-of-the-art results in machine translation
- Demonstrated improved parallelization and reduced training time
- Showed generalization to other tasks like constituency parsing

### Future Directions
- Apply to other modalities (images, audio, video)
- Investigate local, restricted attention for large inputs
- Make generation less sequential
- Explore interpretability of attention mechanisms

---

## Thank You

Code available at: https://github.com/tensorflow/tensor2tensor

arXiv:1706.03762v7 [cs.CL]