---
theme: default
---

# Attention Is All You Need
Ashish Vaswani et al.  
NIPS 2017

---

## Problem Statement
- Traditional sequence models rely on RNNs/CNNs with sequential computation
- Recurrent networks have inherent parallelization limitations
- Convolutional models require increasing layers for long-range dependencies
- Attention mechanisms previously used alongside recurrence/convolution

---

## Key Motivation: Self-Attention Advantages
- **Parallelization**: O(1) sequential operations vs O(n) for RNNs
- **Long-range dependencies**: Constant path length between positions
- **Computational efficiency**: Better than RNNs for typical sequence lengths
- **Interpretability**: Attention distributions reveal linguistic structure

---

## Transformer Architecture Overview
<img src="/paper_figure_1_transformer.png" class="max-h-[500px] w-full object-contain" />  
Encoder-decoder structure with stacked self-attention and feed-forward layers

---

## Encoder Structure
- Stack of 6 identical layers with two sub-layers
- Multi-head self-attention and position-wise feed-forward network
- Residual connections + layer normalization around each sub-layer
- Input: Embeddings + positional encodings (dmodel=512)

---

## Decoder Structure
- Stack of 6 identical layers with three sub-layers
- Masked self-attention prevents access to future positions
- Encoder-decoder attention connects decoder to encoder outputs
- Same residual connections and layer normalization as encoder

---

## Attention Mechanism
- Maps queries, keys, values to output via weighted sum of values
- Two common approaches: additive (feed-forward) and dot-product (faster)
- Transformer uses Scaled Dot-Product Attention with 1/√dk scaling
- Prevents gradient vanishing with large dk compared to standard dot-product

---

## Multi-Head Attention
- Projects Q, K, V h times with different linear projections (h=8 heads)
- Performs attention in parallel on projected subspaces
- Concatenates results and applies final linear projection
- dk=dv=dmodel/h=64 in base model for diverse dependency modeling

---

## Attention Applications
- **Encoder self-attention**: Each position attends to all encoder positions
- **Decoder self-attention**: Each position attends to previous decoder positions
- **Encoder-decoder attention**: Decoder positions attend to all encoder positions

---

## Positional Encoding
- Injects sequence order information (no recurrence/convolution)
- Uses sine/cosine functions with varying frequencies
- PE(pos,2i)=sin(pos/10000^(2i/dmodel)), PE(pos,2i+1)=cos(...)
- Allows model to learn relative position relationships

---

## Training Setup
- **Datasets**: WMT 2014 EN-DE (4.5M pairs), EN-FR (36M pairs)
- **Hardware**: 8 NVIDIA P100 GPUs (12h for base, 3.5d for big model)
- **Optimizer**: Adam with β1=0.9, β2=0.98, and warmup learning rate
- **Regularization**: Residual dropout (Pdrop=0.1) and label smoothing (ϵls=0.1)

---

## Machine Translation Results
| Model | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|-------|------------|------------|-----------------------|
| ConvS2S Ensemble | 26.36 | 41.29 | 7.7×10¹⁹ |
| GNMT + RL Ensemble | 26.30 | 41.16 | 1.8×10²⁰ |
| **Transformer (big)** | **28.4** | **41.8** | **2.3×10¹⁹** |

- 2+ BLEU improvement over previous state-of-the-art on EN-DE
- New single-model state-of-the-art on EN-FR with 1/4 training cost

---

## Model Variations (Ablation Study)
| Configuration | Dev PPL | Dev BLEU |
|---------------|---------|----------|
| Base model | 4.92 | 25.8 |
| Single attention head | 5.29 | 24.9 |
| No dropout | 4.67 | 25.3 |
| Big model (dmodel=1024) | 4.33 | 26.4 |

- Multi-head attention critical for performance
- Dropout prevents overfitting
- Larger model dimensions improve translation quality

---

## Long-Distance Dependency Attention
<img src="/paper_figure_3_long_distance.png" class="max-h-[500px] w-full object-contain" />  
Encoder self-attention (layer 5) showing 'making' attending to distant 'difficult'

---

## Anaphora Resolution Attention
<img src="/paper_figure_4_anaphora.png" class="max-h-[500px] w-full object-contain" />  
Attention heads 5 and 6 resolving 'its' reference to 'The Law'

---

## English Constituency Parsing
| Parser | Training | WSJ 23 F1 |
|--------|----------|-----------|
| RNN Grammar [8] | WSJ only | 91.7 |
| **Transformer (4 layers)** | **WSJ only** | **91.3** |
| Previous semi-supervised | Semi-supervised | 92.1 |
| **Transformer (4 layers)** | **Semi-supervised** | **92.7** |

- Strong performance without task-specific tuning
- Outperforms RNN sequence-to-sequence models in small-data regime

---

## Computational Complexity
| Layer Type | Complexity | Sequential Ops | Max Path Length |
|------------|------------|----------------|-----------------|
| Self-Attention | O(n²·d) | O(1) | O(1) |
| Recurrent | O(n·d²) | O(n) | O(n) |
| Convolutional | O(k·n·d²) | O(1) | O(logk(n)) |

- Self-attention enables better parallelization than RNNs
- Constant path length improves long-range dependency learning

---

## Limitations
- Quadratic complexity with sequence length
- Less effective for very long sequences
- Requires positional encoding for sequence order
- Limited interpretability despite attention visualization

---

## Future Work
- Extend to other modalities (images, audio, video)
- Develop local/restricted attention for long sequences
- Reduce sequential nature of generation process
- Improve efficiency for very large inputs/outputs