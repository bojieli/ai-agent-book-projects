---
theme: default
---

# Attention Is All You Need
## A Revolutionary Architecture for Sequence Transduction

Ashish Vaswani et al.  
NIPS 2017

---

## Abstract: Key Innovation

- Proposes **Transformer** - first model based solely on attention mechanisms
- Dispenses with recurrence and convolutions entirely
- More parallelizable and requires significantly less training time

---

## Abstract: Performance Highlights

- Achieves 28.4 BLEU on WMT 2014 English-to-German
  - Improves over existing best results by over 2 BLEU
- Establishes new state-of-the-art 41.8 BLEU on WMT 2014 English-to-French
- Generalizes well to other tasks like English constituency parsing

---

## Background: Limitations of RNNs

### Recurrent Neural Networks (RNNs/LSTMs/GRUs)
- Inherently sequential computation
- Cannot parallelize within training examples
- Difficult to learn long-range dependencies
- Memory constraints limit batching for long sequences

---

## Background: Limitations of Convolutional Approaches

### CNN-based Models (ByteNet, ConvS2S)
- Use convolutions for parallelization
- Number of operations grows with distance between positions
  - Linear growth for ConvS2S
  - Logarithmic growth for ByteNet
- Longer path lengths between distant positions

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
- Residual connections around each sub-layer
- Layer normalization after each sub-layer
- All sub-layers produce outputs of dimension `d_model = 512`

---

## Encoder: Sub-layer Details

Each encoder layer contains two sub-layers:

1. **Multi-head self-attention** mechanism
   - All positions attend to all positions in previous layer
   - Enables modeling of dependencies throughout sequence

2. **Position-wise fully connected feed-forward network**
   - Applied to each position separately and identically
   - Two linear transformations with ReLU activation

---

## Decoder Structure

- Stack of **6 identical layers**
- Residual connections and layer normalization
- Output embeddings offset by one position (auto-regressive property)

---

## Decoder: Sub-layer Details

Each decoder layer contains three sub-layers:

1. **Masked multi-head self-attention**
   - Prevents positions from attending to subsequent positions

2. **Multi-head attention over encoder output**
   - Queries from decoder, keys/values from encoder

3. **Position-wise fully connected feed-forward network**
   - Same structure as encoder's feed-forward network

---

## Attention Mechanism

### Scaled Dot-Product Attention
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

- $Q$ (queries), $K$ (keys), $V$ (values) are matrices
- Scaling by $\frac{1}{\sqrt{d_k}}$ prevents gradients from becoming too small
- Faster and more space-efficient than additive attention

---

## Multi-Head Attention

<img src="/paper_figure_1_transformer.png" class="h-60 mx-auto" />

- Projects queries, keys, values $h$ times with different learned projections
- Performs attention in parallel on projected versions
- Concatenates results and projects again

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$$

---

## Attention Application: Encoder-Decoder

**Encoder-decoder attention**:
- Queries come from previous decoder layer
- Memory keys and values come from encoder output
- Allows every position in decoder to attend over all positions in input sequence
- Mimics typical encoder-decoder attention mechanisms

---

## Attention Application: Encoder Self-Attention

**Encoder self-attention**:
- Keys, values and queries all come from previous encoder layer
- Each position attends to all positions in previous encoder layer
- Enables modeling of relationships between all words in input sequence
- No regard to distance between positions

---

## Attention Application: Decoder Self-Attention

**Decoder self-attention**:
- Keys, values and queries come from previous decoder layer
- Each position attends to all positions up to and including itself
- Masking prevents attending to subsequent positions
- Preserves auto-regressive property (predictions depend only on known outputs)

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

---

## Training: Data & Batching

- WMT 2014 English-German (4.5M sentence pairs)
- WMT 2014 English-French (36M sentence pairs)
- Byte-pair encoding (37K shared vocab for EN-DE)
- Batches with ~25000 source and target tokens

---

## Training: Hardware & Schedule

- 8 NVIDIA P100 GPUs
- Base model: 100,000 steps (12 hours)
- Big model: 300,000 steps (3.5 days)
- Adam optimizer with scheduled learning rate

---

## Machine Translation Results

| Model | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|-------|------------|------------|-----------------------|
| GNMT + RL Ensemble | 26.30 | 41.16 | $1.8 \cdot 10^{20}$ |
| ConvS2S Ensemble | 26.36 | 41.29 | $7.7 \cdot 10^{19}$ |
| **Transformer (big)** | **28.4** | **41.8** | **$2.3 \cdot 10^{19}$** |

---

## Generalization to Constituency Parsing

| Parser | Training | WSJ 23 F1 |
|--------|----------|-----------|
| Previous state-of-the-art | WSJ only | 91.7 |
| **Transformer (4 layers)** | **WSJ only** | **91.3** |
| Previous state-of-the-art | Semi-supervised | 92.1 |
| **Transformer (4 layers)** | **Semi-supervised** | **92.7** |

---

## Attention Visualization: Long-Distance Dependencies

<img src="/paper_figure_3_long_distance.png" class="h-full w-full object-contain" />

---

## Attention Visualization: Anaphora Resolution

<img src="/paper_figure_4_anaphora.png" class="h-full w-full object-contain" />

---

## Limitations

- Computational complexity grows quadratically with sequence length
- Less effective for very long sequences
- Still requires sequential generation in decoder
- Limited ability to model hierarchical structure

---

## Key Contributions

- Introduced Transformer architecture based solely on attention
- Achieved new state-of-the-art results in machine translation
- Demonstrated improved parallelization and reduced training time
- Showed generalization to other tasks like constituency parsing

---

## Future Work

- Apply to other modalities (images, audio, video)
- Investigate local, restricted attention for large inputs
- Make generation less sequential
- Explore interpretability of attention mechanisms

---

## Thank You

Code available at: https://github.com/tensorflow/tensor2tensor

arXiv:1706.03762v7 [cs.CL]