---
theme: default
---

# Attention Is All You Need
## A Revolutionary Architecture for Sequence Transduction

Ashish Vaswani et al.  
NIPS 2017

---

## Abstract

- First sequence transduction model based solely on attention
- Dispenses with recurrence and convolutions entirely
- More parallelizable and faster to train than traditional models
- New state-of-the-art: 28.4 BLEU (EN-DE) and 41.8 BLEU (EN-FR)
- Generalizes well to English constituency parsing

---

## Background: Limitations of Traditional Models

### Recurrent Models (RNN/LSTM/GRU)
- Inherently sequential computation
- Limited parallelization capability
- O(n) sequential operations for long sequences

### Convolutional Models
- Fixed kernel size restricts context
- O(k·n·d²) complexity with kernel size k
- Logarithmic path length for distant dependencies

---

## Key Innovation: Self-Attention Mechanism

- Connects all positions with constant operations
- Enables parallel computation across sequence
- Directly models long-range dependencies
- More efficient than RNN/CNN for typical sequence lengths
- Provides interpretable attention distributions

---

## Transformer Model Architecture

<img src="/paper_figure_1_transformer.png" class="h-[560px] w-full object-contain" />

Encoder-decoder structure with stacked self-attention and feed-forward layers.

---

## Encoder & Decoder Architecture

### Encoder (6 identical layers)
- **Sub-layer 1**: Multi-head self-attention
- **Sub-layer 2**: Position-wise feed-forward network
- Residual connections + layer normalization
- Output dimension: dmodel = 512

### Decoder (6 identical layers)
- **Sub-layer 1**: Masked multi-head self-attention
- **Sub-layer 2**: Encoder-decoder attention
- **Sub-layer 3**: Position-wise feed-forward network
- Residual connections + layer normalization
- Masking prevents future position attention

---

## Attention Mechanisms

### Scaled Dot-Product Attention
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$
- Scaling avoids gradient vanishing for large dk
- More efficient than additive attention

### Multi-Head Attention
$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1,...,\text{head}_h)W^O$$
- h=8 parallel heads, dk=dv=64
- Captures diverse dependency patterns

---

## Positional Encoding

- Injects sequence order information (no recurrence/convolution)
- Added to input embeddings (same dmodel dimension)
- Uses sine/cosine functions with varying frequencies:
  $$PE_{(pos,2i)} = \sin(pos/10000^{2i/d_{\text{model}}})$$
  $$PE_{(pos,2i+1)} = \cos(pos/10000^{2i/d_{\text{model}}})$$
- Enables learning of relative position relationships

---

## Why Self-Attention?

| Aspect               | Self-Attention | Recurrent | Convolutional |
|----------------------|----------------|-----------|---------------|
| Complexity           | O(n²·d)        | O(n·d²)   | O(k·n·d²)     |
| Parallelization      | O(1)           | O(n)      | O(1)          |
| Long-range path length | O(1)         | O(n)      | O(logk(n))    |

- Superior parallelization and dependency modeling

---

## Training Setup

### Data & Hardware
- WMT 2014 EN-DE (4.5M) and EN-FR (36M)
- 8 NVIDIA P100 GPUs, 0.4s/step (base), 1.0s/step (big)

### Optimization
- Adam (β1=0.9, β2=0.98, ϵ=10⁻⁹)
- Learning rate: $d_{\text{model}}^{-0.5} \cdot \min(\text{step\_num}^{-0.5}, \text{step\_num} \cdot \text{warmup\_steps}^{-1.5})$

### Regularization
- Residual dropout (Pdrop=0.1)
- Label smoothing (ϵls=0.1)

---

## Machine Translation Results

| Model | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|-------|------------|------------|-----------------------|
| GNMT + RL Ensemble | 26.30 | 41.16 | 1.8×10²⁰ / 1.1×10²¹ |
| ConvS2S Ensemble | 26.36 | 41.29 | 7.7×10¹⁹ / 1.2×10²¹ |
| **Transformer (big)** | **28.4** | **41.8** | **2.3×10¹⁹** |

- New state-of-the-art with 4× lower training cost

---

## Model Ablations (EN-DE Dev Set)

| Variation | Dev PPL | Dev BLEU |
|-----------|---------|----------|
| Base model | 4.92 | 25.8 |
| Single attention head | 5.29 | 24.9 |
| No dropout | 4.67 | 25.3 |
| Learned positional embeddings | 4.92 | 25.7 |
| Big model | 4.33 | 26.4 |

■ Multi-head attention and dropout critical for performance
■ Sinusoidal positional encoding ≈ learned embeddings

---

## Generalization to Constituency Parsing

| Parser | Training | WSJ 23 F1 |
|--------|----------|-----------|
| Dyer et al. (2016) | WSJ only | 91.7 |
| **Transformer (4 layers)** | **WSJ only** | **91.3** |
| Vinyals & Kaiser (2014) | Semi-supervised | 92.1 |
| **Transformer (4 layers)** | **Semi-supervised** | **92.7** |

- Strong performance without task-specific modifications

---

## Attention Visualization: Long-Distance Dependencies

<img src="/paper_figure_3_long_distance.png" class="h-[580px] w-full object-contain" />

Encoder self-attention (layer 5) tracking "making...more difficult" dependency.

---

## Attention Visualization: Anaphora Resolution

<img src="/paper_figure_4_anaphora.png" class="h-[580px] w-full object-contain" />

Attention heads resolving "its" to referent "The Law".

---

## Limitations & Future Work

### Limitations
- Quadratic complexity in sequence length
- Less efficient for very long sequences
- Still sequential in generation

### Future Work
- Local/restricted attention mechanisms
- Extension to other modalities (images, audio)
- Non-sequential generation approaches
- Efficient handling of large inputs/outputs

---

## Conclusion

- Transformer replaces recurrence/convolution with self-attention
- Sets new state-of-the-art in machine translation
- Faster training via parallelization
- Generalizes well to diverse sequence tasks
- Foundation for modern attention-based NLP models