---
theme: default
---

# Attention Is All You Need
Ashish Vaswani et al.  
NIPS 2017

---

## Abstract
- First sequence transduction model based solely on attention
- Dispenses with recurrence and convolutions entirely
- Achieves superior translation quality (28.4 BLEU EN-DE, 41.8 BLEU EN-FR)
- Better parallelization and significantly less training time

---

## Background: Limitations of Current Models
- **RNN/LSTM**: Inherently sequential, poor parallelization
- **Convolutional models**: Limited long-range dependencies (linear/logarithmic growth)
- **Attention mechanisms**: Typically used alongside recurrent networks
- Key challenge: Learning long-range dependencies efficiently

---

## Key Innovation: Self-Attention
- Relates different positions of single sequence to compute representation
- Constant path length between any two positions (vs. O(n) for RNN)
- Higher parallelization capability than sequential models
- Lower computational complexity for typical sequence lengths

---

## Transformer Architecture (Figure 1)
<img src="/paper_figure_1_transformer.png" style="max-height: 460px; width: 100%; object-fit: contain;" />
Encoder-decoder structure with stacked self-attention and feed-forward layers

---

## Encoder Architecture
- Stack of 6 identical layers with two sub-layers:
  1. Multi-head self-attention mechanism
  2. Position-wise fully connected feed-forward network
- Residual connections around each sub-layer + layer normalization
- All sub-layers produce outputs of dimension dmodel = 512

---

## Decoder Architecture
- Stack of 6 identical layers with three sub-layers:
  1. Masked multi-head self-attention (prevents leftward flow)
  2. Multi-head attention over encoder outputs
  3. Position-wise fully connected feed-forward network
- Residual connections and layer normalization as in encoder

---

## Scaled Dot-Product Attention
- Attention function: maps queries, keys, values to output
- Computation: Attention(Q, K, V) = softmax(QKT/√dk)V
- Scaling by 1/√dk prevents gradients from becoming too small
- More efficient than additive attention for small dk

---

## Multi-Head Attention
- Projects queries, keys, values h times with different linear projections
- Performs attention in parallel on projected versions, concatenates results
- Benefits: Jointly attends to information from different subspaces
- Hyperparameters: h=8 heads, dk=dv=dmodel/h=64

---

## Attention Applications in Transformer
- **Encoder self-attention**: Each position attends to all positions in previous encoder layer
- **Decoder self-attention**: Each position attends to previous positions (masked)
- **Encoder-decoder attention**: Decoder positions attend to all encoder positions

---

## Position-wise Feed-Forward Networks
- Applied to each position separately and identically
- Two linear transformations with ReLU activation
- Inner layer dimensionality dff = 2048, output dmodel = 512
- Can be viewed as 1x1 convolutions

---

## Positional Encoding
- Inject sequence order information (no recurrence/convolution)
- Added to input embeddings (same dimension dmodel)
- Uses sine/cosine functions of different frequencies: PE(pos,2i) = sin(pos/10000^(2i/dmodel))
- PE(pos,2i+1) = cos(pos/10000^(2i/dmodel))

---

## Training Setup
- **Datasets**: WMT 2014 EN-DE (4.5M pairs), EN-FR (36M pairs)
- **Hardware**: 8 NVIDIA P100 GPUs (base: 12h, big: 3.5 days)
- **Optimizer**: Adam (β1=0.9, β2=0.98, ϵ=10⁻⁹) with scheduled learning rate
- **Regularization**: Residual dropout (Pdrop=0.1), label smoothing (ϵls=0.1)

---

## Machine Translation Results
- **EN-DE**: 28.4 BLEU (big model) - 2+ BLEU improvement over previous SOTA
- **EN-FR**: 41.8 BLEU (big model) - new single-model state-of-the-art
- Base model outperforms all published models at 1/10 training cost
- Significantly lower training FLOPs than competing architectures

---

## Model Variations (Ablation Study)
- **Attention heads**: 8 heads optimal (single head: -0.9 BLEU)
- **Model size**: Larger models (dmodel=1024, dff=4096) improve BLEU
- **Positional encoding**: Learned embeddings perform nearly identical to sinusoidal
- **Dropout**: Critical for avoiding overfitting (no dropout: -1.2 BLEU)

---

## Long-Distance Attention (Figure 3)
<img src="/paper_figure_3_long_distance.png" style="max-height: 460px; width: 100%; object-fit: contain;" />
Encoder self-attention showing 'making' attending to distant 'more difficult'

---

## Anaphora Attention (Figure 4)
<img src="/paper_figure_4_anaphora.png" style="max-height: 460px; width: 100%; object-fit: contain;" />
Attention heads resolving 'its' reference to 'Law' and 'application'

---

## Generalization to Constituency Parsing
- 4-layer Transformer achieves 91.3 F1 on WSJ (WSJ only training)
- Semi-supervised setting: 92.7 F1 with 17M additional sentences
- Outperforms RNN sequence-to-sequence models in small-data regimes
- Demonstrates Transformer's versatility beyond machine translation

---

## Limitations and Future Work
- **Limitations**: Less effective for very long sequences; sequential generation
- **Future directions**: Extend to other modalities (images, audio, video)
- Investigate local restricted attention mechanisms for large inputs
- Develop less sequential generation approaches

---

## Conclusion
- Transformer achieves new state-of-the-art in machine translation
- Eliminates recurrence/convolution in favor of self-attention
- Significantly faster training with better parallelization
- Attention mechanisms enable interpretable model behavior