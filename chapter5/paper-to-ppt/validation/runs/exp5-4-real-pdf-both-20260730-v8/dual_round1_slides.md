---
theme: default
---

# Attention Is All You Need
## Ashish Vaswani et al.
### NIPS 2017

---

## Abstract
- First sequence transduction model based solely on attention
- Dispenses with recurrence and convolutions entirely
- Superior quality with better parallelization and lower training cost
- State-of-the-art results: 28.4 BLEU (EN-DE) and 41.8 BLEU (EN-FR)

---

## Background & Key Innovation
- **Challenges**: RNNs have sequential computation; CNNs need O(log n) layers for long dependencies
- **Previous work**: Attention typically辅助 recurrent networks
- **Transformer**: Replaces recurrence/conv with self-attention for global dependencies
- **Advantages**: Massive parallelization, constant operations for long-range dependencies

---

## Model Architecture Overview
- Encoder-decoder structure with 6 stacked layers each
- Encoder: Multi-Head Self-Attention + Feed-Forward Network
- Decoder: Masked Self-Attention + Encoder-Decoder Attention + Feed-Forward
- Residual connections and layer normalization; d_model = 512

---

# Transformer Architecture (Figure 1)
<img src="/paper_figure_1_transformer.png" class="max-h-[500px] w-full object-contain" />
Complete Transformer architecture with encoder (left) and decoder (right) stacks.

---

## Attention Mechanism & Multi-Head
- **Scaled Dot-Product Attention**: Attention(Q,K,V) = softmax((QKᵀ)/√dₖ)V
- **Scaling**: Prevents softmax saturation for large dₖ (dₖ=64)
- **Multi-Head**: 8 parallel attention heads on projected subspaces
- **Concatenation**: Combines heads and applies final linear projection

---

## Attention Applications
1. **Encoder-decoder attention**: Decoder queries attend to encoder outputs
2. **Encoder self-attention**: All positions attend to each other (global context)
3. **Decoder self-attention**: Masked to prevent future position access (auto-regressive)

---

## Positional Encoding
- Injects sequence order information (no recurrence/convolution)
- Added to input embeddings (same d_model dimension)
- Uses sine/cosine functions: PE(pos,2i)=sin(pos/10000^(2i/d_model))
- Alternative: learned embeddings (nearly identical performance)

---

## Self-Attention Advantages

| Aspect               | Self-Attention | RNN        | CNN          |
|----------------------|----------------|------------|--------------|
| Complexity           | O(n²·d)        | O(n·d²)    | O(k·n·d²)    |
| Parallelization      | O(1)           | O(n)       | O(1)         |
| Long-range paths     | O(1)           | O(n)       | O(logₖn)     |

- Better parallelization than RNNs; shorter paths than CNNs/RNNs

---

## Training Setup
- Datasets: WMT 2014 EN-DE (4.5M) and EN-FR (36M sentences)
- Vocabulary: Byte-pair encoding (37K for EN-DE, 32K for EN-FR)
- Hardware: 8 P100 GPUs; 100K-300K steps (12h-3.5 days)
- Optimizer: Adam (β₁=0.9, β₂=0.98); learning rate with warmup

---

## Machine Translation Results
- EN-DE: 28.4 BLEU (↑2+ over previous best, including ensembles)
- EN-FR: 41.8 BLEU (new single-model state-of-the-art)
- Training cost: 3.3×10¹⁸ FLOPs (EN-DE base) vs 10¹⁹-10²¹ for competitors
- Achieves better quality with significantly lower computational resources

---

## Model Variations (Ablation Study)
- Single-head attention: 0.9 BLEU worse than 8-head setup
- Reducing dₖ (attention key size) degrades performance
- Larger models (d_model=1024): +1.1 BLEU over base model
- Dropout critical for preventing overfitting (P_drop=0.1)

---

# Long-Distance Attention (Figure 3)
<img src="/paper_figure_3_long_distance.png" class="max-h-[500px] w-full object-contain" />
Encoder self-attention showing "making" attending to distant "more difficult".

---

# Anaphora Attention (Figure 4)
<img src="/paper_figure_4_anaphora.png" class="max-h-[500px] w-full object-contain" />
Attention heads resolving anaphora: "its" attending to "Law" and "application".

---

## Generalization to Parsing
- Applied Transformer to English constituency parsing
- WSJ only (40K sentences): 91.3 F1 (comparable to state-of-the-art)
- Semi-supervised (17M sentences): 92.7 F1 (outperforms most prior models)
- Demonstrates transferability to structural NLP tasks

---

## Limitations
- O(n²) self-attention complexity for long sequences
- Memory-intensive with extended input lengths
- Decoder still generates output sequentially
- Attention patterns show interpretability but not fully understood

---

## Conclusion & Future Work
- **Conclusion**: Establishes new state-of-the-art in translation; replaces recurrence with attention
- **Future directions**: Extend to multi-modal inputs; develop local restricted attention
- Explore non-sequential generation; enhance attention interpretability
- Significantly reduces training time while improving quality

---

## References
- Vaswani et al. (2017). Attention is all you need. NIPS 2017
- Code: https://github.com/tensorflow/tensor2tensor