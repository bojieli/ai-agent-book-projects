---
theme: default
---

# Attention Is All You Need
## A Revolutionary Architecture for Sequence Transduction
Ashish Vaswani et al.  
NIPS 2017

---

## Background
- Dominant sequence models rely on RNNs/LSTMs/GRUs
- Encoder-decoder architectures with auxiliary attention
- Sequential computation limits parallelization
- Long-range dependencies are challenging to model

---

## Motivation
- Recurrent networks: Inherently sequential, poor parallelization
- Convolutional networks: Limited receptive field, layered dependencies
- Both: Computation grows with distance between positions
- Need for architecture with parallelization and global dependencies

---

## Transformer: Key Innovation
- First sequence transduction model based entirely on attention
- Dispenses with recurrence and convolutions entirely
- Significantly more parallelizable than RNN/CNN models
- Achieves state-of-the-art results with lower training cost

---

## Transformer Architecture (Figure 1)

<img src="/paper_figure_1_transformer.png" style="max-height: 460px; width: 100%; object-fit: contain;" />

Encoder (left) and decoder (right) stacks with self-attention and feed-forward layers.

---

## Encoder Structure
- Stack of 6 identical layers
- Each layer: Multi-head self-attention + feed-forward network
- Residual connections around each sub-layer
- Layer normalization; output dimension dmodel=512

---

## Decoder Structure
- Stack of 6 identical layers
- Three sub-layers: Masked self-attention, encoder-decoder attention, feed-forward
- Residual connections and layer normalization
- Masking prevents attending to future positions

---

## Attention Mechanism
- Maps query (Q) and key-value (K,V) pairs to output
- Output: Weighted sum of values, weights from query-key compatibility
- Two primary types: Additive attention and dot-product attention
- Transformer uses scaled dot-product attention with multi-head extension

---

## Scaled Dot-Product Attention
- Compute dot products of Q with all K
- Scale by 1/√dk to prevent softmax gradient vanishing
- Apply softmax to get weights on values
- Formula: Attention(Q,K,V) = softmax(QKT/√dk)V

---

## Multi-Head Attention
- Project Q, K, V h times with learned linear projections
- Perform attention in parallel on each projection (heads)
- Concatenate results and project to final output
- h=8 heads, dk=dv=dmodel/h=64 (total cost similar to single-head)

---

## Self-Attention Advantages
- Computational complexity: O(n²·d) vs O(n·d²) for RNNs
- Parallelization: O(1) sequential operations vs O(n) for RNNs
- Long-range dependencies: Constant path length vs O(n) for RNNs
- Interpretability: Attention distributions reveal dependency patterns

---

## Positional Encoding
- Inject sequence order information (no recurrence/convolution)
- Added to input embeddings (same dimension dmodel=512)
- Uses sine/cosine functions with varying frequencies
- Supports learning of relative position relationships

---

## Training Setup
- Datasets: WMT 2014 EN-DE (4.5M) and EN-FR (36M) sentence pairs
- Hardware: 8 NVIDIA P100 GPUs; base model trained 12h, big model 3.5 days
- Optimizer: Adam (β1=0.9, β2=0.98, ϵ=10⁻⁹) with linear warmup learning rate
- Regularization: Residual dropout (Pdrop=0.1), label smoothing (ϵls=0.1)

---

## Translation Performance
- EN-DE: 28.4 BLEU (+2+ over previous SOTA including ensembles)
- EN-FR: 41.8 BLEU (new single-model state-of-the-art)
- Training cost: Significantly lower than competitors (e.g., 1/4 of prior SOTA)
- Base model outperforms most previous models at fraction of training time

---

## Long-Distance Attention (Figure 3)

<img src="/paper_figure_3_long_distance.png" style="max-height: 460px; width: 100%; object-fit: contain;" />

Encoder self-attention linking "making" to distant "more difficult" (layer 5).

---

## Anaphora Attention (Figure 4)

<img src="/paper_figure_4_anaphora.png" style="max-height: 460px; width: 100%; object-fit: contain;" />

Attention heads resolving "its" to "Law" and "application" (layer 5).

---

## Generalization: Constituency Parsing
- 4-layer Transformer with dmodel=1024
- WSJ only (40K sentences): 91.3 F1 (comparable to SOTA)
- Semi-supervised (17M sentences): 92.7 F1 (outperforms most prior models)
- Demonstrates transferability to non-translation tasks

---

## Limitations
- O(n²) complexity for sequence length n (challenging for very long sequences)
- Requires explicit positional encoding for sequence order
- Generation remains auto-regressive (sequential)
- Less explored for non-text modalities (images, audio, video)

---

## Conclusion
- Transformer establishes new SOTA in machine translation
- Significantly faster training due to parallelization
- Self-attention effectively captures global dependencies
- Generalizes well to other sequence tasks beyond translation

---

## Future Work
- Extend to multi-modal inputs/outputs (images, audio, video)
- Develop local restricted attention for long sequences
- Reduce sequential constraints in generation process
- Explore more interpretable attention patterns