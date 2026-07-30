---
theme: default
---

# Attention Is All You Need
## A Revolutionary Architecture for Sequence Transduction

Ashish Vaswani et al.  
NIPS 2017

---

## Problem Statement

- Traditional sequence models rely on RNNs or CNNs
- RNNs have inherent sequential computation (hard to parallelize)
- CNNs require multiple layers to capture long-range dependencies
- Both have increasing path lengths between distant positions

**Key Insight**: Replace recurrence and convolution with attention mechanisms

---

## The Transformer: Model Architecture

<img src="/paper_figure_1_transformer.png" class="h-96 mx-auto" />

- Encoder-decoder structure with stacked self-attention layers
- No recurrence or convolution
- Significantly more parallelizable

---

## Encoder Stack

- 6 identical layers with two sub-layers each:
  1. Multi-head self-attention mechanism
  2. Position-wise fully connected feed-forward network
- Residual connections + layer normalization
- Output dimension: d<sub>model</sub> = 512

---

## Decoder Stack

- 6 identical layers with three sub-layers each:
  1. Masked multi-head self-attention
  2. Multi-head attention over encoder output
  3. Position-wise fully connected feed-forward network
- Residual connections + layer normalization
- Masking prevents attending to future positions

---

## Scaled Dot-Product Attention

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

- Queries (Q), Keys (K), Values (V) are matrices
- Scaling by $\sqrt{d_k}$ prevents gradient vanishing
- More efficient than additive attention

---

## Multi-Head Attention

<img src="/paper_figure_1_transformer.png" class="h-60 mx-auto" />

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$$

- Project Q, K, V h times with different linear projections
- Perform attention in parallel on each projection
- Concatenate results and project again

---

## Applications of Attention

1. **Encoder-decoder attention**:
   - Queries from decoder, keys/values from encoder

2. **Encoder self-attention**:
   - All Q, K, V from previous encoder layer
   - Each position attends to all positions

3. **Decoder self-attention**:
   - All Q, K, V from previous decoder layer
   - Masked to prevent attending to future positions

---

## Positional Encoding

Since model has no recurrence/convolution, we add positional information:

$$PE_{(pos, 2i)} = \sin\left(pos / 10000^{2i/d_{\text{model}}}\right)$$
$$PE_{(pos, 2i+1)} = \cos\left(pos / 10000^{2i/d_{\text{model}}}\right)$$

- Sinusoidal functions with varying frequencies
- Allows model to learn relative position information
- Performed as well as learned positional embeddings

---

## Why Self-Attention?

| Layer Type | Complexity | Sequential Ops | Max Path Length |
|------------|------------|----------------|-----------------|
| Self-Attention | O(n²·d) | O(1) | O(1) |
| Recurrent | O(n·d²) | O(n) | O(n) |
| Convolutional | O(k·n·d²) | O(1) | O(logₖn) |

- Better parallelization than RNNs
- Shorter path lengths than CNNs/RNNs
- More interpretable attention patterns

---

## Training Details

- **Datasets**: WMT 2014 EN-DE (4.5M) and EN-FR (36M)
- **Hardware**: 8 NVIDIA P100 GPUs
- **Optimizer**: Adam (β₁=0.9, β₂=0.98, ϵ=10⁻⁹)
- **Learning Rate**: 
  $$lrate = d_{\text{model}}^{-0.5} \cdot \min(\text{step\_num}^{-0.5}, \text{step\_num} \cdot \text{warmup\_steps}^{-1.5})$$
- **Regularization**: Dropout (P=0.1), Label Smoothing (ϵ=0.1)

---

## Machine Translation Results

| Model | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|-------|------------|------------|------------------------|
| GNMT + RL | 24.6 | 39.92 | 2.3·10¹⁹ |
| ConvS2S | 25.16 | 40.46 | 9.6·10¹⁸ |
| Transformer (base) | 27.3 | 38.1 | 3.3·10¹⁸ |
| **Transformer (big)** | **28.4** | **41.8** | **2.3·10¹⁹** |

- Transformer (big) outperforms all previous state-of-the-art
- Achieves new SOTA with significantly less training cost

---

## Model Variations

| Configuration | Dev PPL | Dev BLEU |
|---------------|---------|----------|
| Base | 4.92 | 25.8 |
| 1 attention head | 5.29 | 24.9 |
| 32 attention heads | 5.01 | 25.4 |
| No dropout | 5.77 | 24.6 |
| Learned positional embeddings | 4.92 | 25.7 |
| Big model | 4.33 | 26.4 |

---

## English Constituency Parsing

| Parser | Training | WSJ 23 F1 |
|--------|----------|-----------|
| Petrov et al. (2006) | WSJ only | 90.4 |
| Dyer et al. (2016) | WSJ only | 91.7 |
| **Transformer (4 layers)** | **WSJ only** | **91.3** |
| Vinyals & Kaiser et al. | Semi-supervised | 92.1 |
| **Transformer (4 layers)** | **Semi-supervised** | **92.7** |

- Transformer generalizes well to other sequence tasks

---

## Attention Visualization: Long-Distance Dependencies

<img src="/paper_figure_3_long_distance.png" class="h-80 mx-auto" />

- Attention heads follow distant dependencies
- Example: Verb "making" attends to "more difficult"
- Different colors represent different attention heads

---

## Attention Visualization: Anaphora Resolution

<img src="/paper_figure_4_anaphora.png" class="h-80 mx-auto" />

- Some heads specialize in resolving pronouns
- Example: "its" clearly attends to "The Law"
- Sharp attention patterns for coreference resolution

---

## Limitations and Future Work

### Limitations:
- High memory consumption with long sequences (O(n²))
- Still generates output sequentially

### Future Work:
- Local, restricted attention mechanisms for large inputs
- Extend to other modalities (images, audio, video)
- Make generation less sequential

---

## Conclusion

- Transformer is the first transduction model based entirely on attention
- Replaces RNNs/CNNs with multi-headed self-attention
- Significantly faster training with better parallelization
- Achieves new state-of-the-art in machine translation
- Generalizes well to other sequence tasks like constituency parsing

**Code**: https://github.com/tensorflow/tensor2tensor