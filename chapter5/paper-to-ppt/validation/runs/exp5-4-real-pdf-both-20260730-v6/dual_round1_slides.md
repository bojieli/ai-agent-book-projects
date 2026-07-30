---
theme: default
---

# Attention Is All You Need
## Transformer: A Revolutionary Architecture for Sequence Transduction

Ashish Vaswani et al.  
NIPS 2017

---

# Abstract

- Proposes Transformer: first sequence transduction model based solely on attention
- Dispenses with recurrence and convolutions entirely
- Achieves superior quality while being more parallelizable
- Sets new state-of-the-art on WMT 2014 translation tasks (28.4/41.8 BLEU)

---

# Background & Motivation

- RNN/LSTM/GRU have been state-of-the-art for sequence modeling
- Sequential nature of RNNs limits parallelization and long-range dependencies
- Attention mechanisms complement RNNs but rarely replace them
- Convolutional approaches (ByteNet, ConvS2S) have limited receptive fields

---

# The Transformer Architecture

<img src="/paper_figure_1_transformer.png" class="max-h-[500px] w-full object-contain" />

Encoder-decoder structure using stacked self-attention and feed-forward layers

---

# Encoder Stack

- Stack of 6 identical layers with two sub-layers
- Multi-head self-attention mechanism
- Position-wise fully connected feed-forward network
- Residual connections + layer normalization around each sub-layer

---

# Decoder Stack

- Stack of 6 identical layers with three sub-layers
- Masked multi-head self-attention (prevents future access)
- Multi-head attention over encoder output
- Residual connections + layer normalization around each sub-layer

---

# Attention Mechanism

- Maps query and key-value pairs to output via weighted sum of values
- Transformer uses Scaled Dot-Product Attention:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

- Scaling by √d_k prevents gradients from becoming too small
- More efficient than additive attention with similar complexity

---

# Multi-Head Attention

- Projects Q, K, V h times with different learned projections
- Performs attention in parallel on each projected version
- Concatenates results and projects again to get final output
- h=8 heads, d_k=d_v=d_model/h=64 for base model

---

# Attention Applications

- **Encoder-decoder attention**: Decoder queries attend to encoder outputs
- **Encoder self-attention**: Each position attends to all positions in previous layer
- **Decoder self-attention**: Each position attends to previous positions only
- Masking in decoder preserves auto-regressive property

---

# Positional Encoding

- Injects positional information since no recurrence/convolution
- Added to input embeddings (same dimension d_model=512)
- Uses sine and cosine functions of different frequencies
- Alternative: learned positional embeddings (similar performance)

---

# Why Self-Attention?

| Aspect | Self-Attention | Recurrent | Convolutional |
|--------|----------------|-----------|---------------|
| Complexity | O(n²·d) | O(n·d²) | O(k·n·d²) |
| Parallelization | O(1) | O(n) | O(1) |
| Long-range paths | O(1) | O(n) | O(log k(n)) |

- Self-attention connects all positions with constant sequential operations
- More efficient than RNNs for typical NLP sequence lengths

---

# Training Details

- **Data**: WMT 2014 EN-DE (4.5M pairs), EN-FR (36M pairs)
- **Hardware**: 8 NVIDIA P100 GPUs (base model: 12h, big model: 3.5 days)
- **Optimizer**: Adam with learning rate scheduling
- **Regularization**: Residual dropout (P_drop=0.1), label smoothing (ϵ_ls=0.1)

---

# Machine Translation Results

| Model | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|-------|------------|------------|-----------------------|
| GNMT+RL Ensemble | 26.30 | 41.16 | 1.8×10²⁰ |
| ConvS2S Ensemble | 26.36 | 41.29 | 7.7×10¹⁹ |
| **Transformer (big)** | **28.4** | **41.8** | **2.3×10¹⁹** |

- Transformer outperforms all previous models by >2 BLEU on EN-DE
- Achieves new state-of-the-art with significantly lower training cost

---

# Model Variations (Ablation Study)

| Variation | Dev PPL | Dev BLEU |
|-----------|---------|----------|
| Base model | 4.92 | 25.8 |
| Single attention head | 5.29 | 24.9 |
| No dropout | 4.67 | 25.3 |
| Big model | 4.33 | 26.4 |

- Multiple attention heads improve performance
- Dropout helps prevent overfitting

---

# Attention Visualization: Long-Distance Dependencies

<img src="/paper_figure_3_long_distance.png" class="max-h-[500px] w-full object-contain" />

Encoder self-attention in layer 5 showing attention to distant dependency of the verb "making"

---

# Attention Visualization: Anaphora Resolution

<img src="/paper_figure_4_anaphora.png" class="max-h-[500px] w-full object-contain" />

Attention heads 5 and 6 showing sharp attention from "its" to "The Law" (anaphora resolution)

---

# Generalization to Other Tasks

- **English Constituency Parsing**:
  - 91.3 F1 on WSJ only (comparable to state-of-the-art)
  - 92.7 F1 with semi-supervised training
- Performs well with minimal task-specific tuning

---

# Limitations

- O(n²) complexity for long sequences
- Less effective for very long sequences (e.g., books)
- Reduced effective resolution due to attention averaging

---

# Future Work

- Local, restricted attention mechanisms for large inputs
- Extend to other modalities (images, audio, video)
- Make generation less sequential

---

# Conclusion

- Transformer: first transduction model based entirely on attention
- Significantly faster training with better parallelization
- State-of-the-art results on WMT 2014 translation tasks
- Generalizes well to other sequence tasks and paves the way for modern NLP