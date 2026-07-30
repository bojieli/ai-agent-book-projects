---
theme: default
---

# Attention Is All You Need
## A Revolutionary Architecture for Sequence Transduction

Ashish Vaswani et al.  
NIPS 2017

---

## Abstract

- Proposes Transformer: first model based solely on attention mechanisms
- Dispenses with recurrence and convolutions entirely
- Achieves superior quality while being more parallelizable
- 28.4 BLEU on WMT 2014 English-to-German (↑2+ BLEU)
- 41.8 BLEU on WMT 2014 English-to-French (new state-of-the-art)
- Generalizes well to other tasks like English constituency parsing

---

## Background: The Problem with Traditional Approaches

- **Recurrent models (RNN/LSTM/GRU)**
  - Inherently sequential computation
  - Limited parallelization
  - Difficult to learn long-range dependencies

- **Convolutional models**
  - Fixed kernel size limits long-range dependencies
  - O(n/k) or O(logk(n)) operations for distant connections
  - Less efficient than attention for sequence tasks

---

## Key Innovation: Attention as the Core Mechanism

- **Self-attention** connects all positions with constant operations
- **Parallelization** possible across sequence positions
- **Long-range dependencies** modeled directly
- **Interpretability** through attention distributions
- **Computational efficiency** for typical sequence lengths

---

## Transformer Model Architecture

<img src="/paper_figure_1_transformer.png" class="h-[560px] w-full object-contain" />

The overall encoder-decoder structure with stacked self-attention and feed-forward layers.

---

## Encoder Architecture

- Stack of 6 identical layers
- Each layer has two sub-layers:
  1. Multi-head self-attention mechanism
  2. Position-wise fully connected feed-forward network
- Residual connections around each sub-layer
- Layer normalization after each sub-layer
- All sub-layers produce outputs of dimension dmodel = 512

---

## Decoder Architecture

- Stack of 6 identical layers
- Three sub-layers per layer:
  1. Masked multi-head self-attention
  2. Multi-head attention over encoder outputs
  3. Position-wise fully connected feed-forward network
- Residual connections and layer normalization
- Masking prevents attending to future positions
- Output embeddings offset by one position

---

## Attention Mechanism

- Maps query and key-value pairs to output
- Output = weighted sum of values
- Weights computed by compatibility function of query and keys

**Scaled Dot-Product Attention:**
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

- Scaling prevents gradients from becoming too small
- More efficient than additive attention in practice

---

## Multi-Head Attention

- Projects queries, keys, values h times with different linear projections
- Performs attention in parallel on projected subspaces
- Concatenates results and projects again

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$$
where $\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$

- h = 8 parallel attention heads in base model
- $d_k = d_v = d_{\text{model}}/h = 64$

---

## Three Applications of Attention

1. **Encoder-decoder attention**
   - Queries from decoder, keys/values from encoder
   - Allows decoder to attend to all input positions

2. **Encoder self-attention**
   - All keys, values, queries from previous encoder layer
   - Each position attends to all positions in previous layer

3. **Decoder self-attention**
   - Each position attends to previous positions in decoder
   - Masking prevents attending to future positions

---

## Positional Encoding

- Injects sequence order information since no recurrence/convolution
- Added to input embeddings (same dimension dmodel)
- Uses sine and cosine functions of different frequencies:

$$PE_{(pos,2i)} = \sin(pos/10000^{2i/d_{\text{model}}})$$
$$PE_{(pos,2i+1)} = \cos(pos/10000^{2i/d_{\text{model}}})$$

- Allows model to learn relative position relationships
- Performed as well as learned positional embeddings

---

## Why Self-Attention?

| Aspect | Self-Attention | Recurrent | Convolutional |
|--------|----------------|-----------|---------------|
| Complexity | O(n²·d) | O(n·d²) | O(k·n·d²) |
| Parallelization | O(1) | O(n) | O(1) |
| Long-range paths | O(1) | O(n) | O(logk(n)) |

- More parallelizable than RNNs
- Better at capturing long-range dependencies than CNNs
- More efficient for typical sequence lengths (n < d)
- More interpretable through attention weights

---

## Training Details

- **Datasets**: WMT 2014 EN-DE (4.5M) and EN-FR (36M)
- **Batching**: ~25,000 source and target tokens per batch
- **Hardware**: 8 NVIDIA P100 GPUs
- **Optimizer**: Adam (β1=0.9, β2=0.98, ϵ=10⁻⁹)
- **Learning rate**: $d_{\text{model}}^{-0.5} \cdot \min(\text{step_num}^{-0.5}, \text{step_num} \cdot \text{warmup_steps}^{-1.5})$
- **Regularization**: Residual dropout (Pdrop=0.1), label smoothing (ϵls=0.1)

---

## Machine Translation Results

| Model | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|-------|------------|------------|-----------------------|
| GNMT + RL Ensemble | 26.30 | 41.16 | 1.8×10²⁰ / 1.1×10²¹ |
| ConvS2S Ensemble | 26.36 | 41.29 | 7.7×10¹⁹ / 1.2×10²¹ |
| **Transformer (big)** | **28.4** | **41.8** | **2.3×10¹⁹** |

- Transformer (big) outperforms all previous models
- Achieves new state-of-the-art with significantly lower training cost
- Trained in 3.5 days on 8 GPUs (vs. weeks for competitors)

---

## Model Architecture Ablations

| Variation | Dev PPL | Dev BLEU |
|-----------|---------|----------|
| Base model | 4.92 | 25.8 |
| Single attention head | 5.29 | 24.9 |
| 32 attention heads | 5.01 | 25.4 |
| No dropout | 4.67 | 25.3 |
| Learned positional embeddings | 4.92 | 25.7 |
| Big model | 4.33 | 26.4 |

-多头注意力优于单头注意力
- dropout对防止过拟合至关重要
- 正弦位置编码与学习的位置编码效果相当
- 增大模型尺寸(dmodel=1024, dff=4096)提升性能

---

## Generalization to English Constituency Parsing

| Parser | Training | WSJ 23 F1 |
|--------|----------|-----------|
| Petrov et al. (2006) | WSJ only | 90.4 |
| Dyer et al. (2016) | WSJ only | 91.7 |
| **Transformer (4 layers)** | **WSJ only** | **91.3** |
| Vinyals & Kaiser (2014) | Semi-supervised | 92.1 |
| **Transformer (4 layers)** | **Semi-supervised** | **92.7** |

- Transformer performs well without task-specific modifications
- Outperforms RNN approaches in small-data regimes
- Achieves 92.7 F1 in semi-supervised setting

---

## Attention Visualization: Long-Distance Dependencies

<img src="/paper_figure_3_long_distance.png" class="h-[560px] w-full object-contain" />

Encoder self-attention in layer 5 showing attention to distant dependency of the verb "making".

---

## Attention Visualization: Anaphora Resolution

<img src="/paper_figure_4_anaphora.png" class="h-[560px] w-full object-contain" />

Attention heads involved in resolving the pronoun "its" to its referent "The Law".

---

## Limitations and Future Work

- **Limitations**:
  - Quadratic complexity in sequence length
  - Less effective for very long sequences
  - Still generates output sequentially

- **Future work**:
  - Local, restricted attention mechanisms
  - Applications to other modalities (images, audio, video)
  - Less sequential generation approaches
  - Efficient handling of large inputs/outputs

---

## Conclusion

- Transformer achieves state-of-the-art results in machine translation
- Eliminates recurrence and convolution in favor of self-attention
- Significantly faster training through parallelization
- Generalizes well to other sequence tasks like constituency parsing
- Paves the way for modern attention-based models in NLP
- Code available at https://github.com/tensorflow/tensor2tensor