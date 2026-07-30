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
- Inherently sequential computation → limited parallelization
- O(n) sequential operations for long-range dependencies

### Convolutional Models
- Fixed kernel size restricts context → requires multiple layers
- Logarithmic path length for distant connections

---

## Key Innovation: Self-Attention Mechanism

- Connects all positions with constant operations
- Enables parallel computation across sequence
- Directly models long-range dependencies
- More efficient than RNN/CNN for typical sequence lengths

---

## Transformer Model Architecture

<img src="/paper_figure_1_transformer.png" class="h-[560px] w-full object-contain" />

Encoder-decoder structure with stacked self-attention and feed-forward layers.

---

## Encoder Architecture

- Stack of 6 identical layers
- Each layer has two sub-layers:
  1. Multi-head self-attention mechanism
  2. Position-wise feed-forward network
- Residual connections + layer normalization
- Output dimension: dmodel = 512

---

## Decoder Architecture

- Stack of 6 identical layers
- Three sub-layers per layer:
  1. Masked multi-head self-attention (prevents future positions)
  2. Encoder-decoder attention (queries from decoder, keys/values from encoder)
  3. Position-wise feed-forward network
- Residual connections + layer normalization

---

## Attention Mechanisms

### Scaled Dot-Product Attention
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$
- Scaling avoids gradient vanishing for large dk

### Multi-Head Attention
$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1,...,\text{head}_h)W^O$$
- h=8 parallel heads, dk=dv=64 → captures diverse patterns

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
- WMT 2014 EN-DE (4.5M) and EN-FR (36M) sentence pairs
- 8 NVIDIA P100 GPUs, 12h (base)/3.5d (big model) training

### Optimization
- Adam (β1=0.9, β2=0.98, ϵ=10⁻⁹) with linear warmup (4000 steps) + inverse square root decay
- Regularization: residual dropout (0.1), label smoothing (0.1)

---

## Machine Translation Results

| Model | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|-------|------------|------------|-----------------------|
| GNMT + RL Ensemble | 26.30 | 41.16 | 1.8×10²⁰ / 1.1×10²¹ |
| ConvS2S Ensemble | 26.36 | 41.29 | 7.7×10¹⁹ / 1.2×10²¹ |
| **Transformer (big)** | **28.4** | **41.8** | **2.3×10¹⁹** |

- New state-of-the-art with 4× lower training cost

---

## Model Ablations & Generalization

### Key Ablations (EN-DE Dev Set)
| Variation | Dev BLEU | Insight |
|-----------|----------|---------|
| Single head | 24.9 | Multi-head critical |
| No dropout | 25.3 | Regularization needed |
| Learned pos encoding | 25.7 | Sinusoidal ≈ learned |

### Constituency Parsing
- 91.3 F1 (WSJ only) vs. 91.7 (state-of-the-art)
- 92.7 F1 (semi-supervised) → strong generalization

---

## Attention Visualization: Long-Distance Dependencies

<img src="/paper_figure_3_long_distance.png" class="h-[650px] w-full object-contain" />

Encoder self-attention (layer 5) showing how "making" attends to distant words to complete the phrase "making...more difficult".

---

## Attention Visualization: Anaphora Resolution

<img src="/paper_figure_4_anaphora.png" class="h-[650px] w-full object-contain" />

Attention heads resolving the pronoun "its" to its referent "The Law" with sharp attention focusing.

---

## Limitations

- Quadratic complexity in sequence length
- Less efficient for very long sequences
- Still sequential in generation process

---

## Future Work

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