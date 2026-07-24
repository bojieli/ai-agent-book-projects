#!/usr/bin/env python3
"""Generate all SVG illustrations for Chapter 3 (Knowledge Base & RAG).

Figures (14 total):
  fig3-1:  Chapter roadmap
  fig3-2:  RAG end-to-end pipeline (concrete example)
  fig3-3:  Dense embedding evolution (with dimensions & training)
  fig3-4:  HNSW index structure (enlarged)
  fig3-5:  BM25 scoring mechanism (enlarged)
  fig3-6:  Hybrid retrieval + reranking (with scores)
  fig3-7:  RAPTOR tree structure (enlarged)
  fig3-8:  GraphRAG relation network (enlarged)
  fig3-9:  Agentic vs Non-Agentic RAG (concrete queries)
  fig3-10: Agentic RAG system architecture (Exp 3.6)
  fig3-11: Contextual retrieval (concrete prefix example)
  fig3-12: Structured knowledge extraction pipeline (Exp 3.10)
  fig3-13: Externalized learning loop (concrete)
  fig3-14: GAIA experience learning (Exp 3.11)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    SVG, COLORS, FONT, MONO, STROKE_W, CORNER_R, _escape, _marker_def,
    FS_TITLE, FS_BODY, FS_SMALL, FS_TINY, FS_LABEL,
)

OUT = os.path.join(os.path.dirname(__file__), 'images')


# ──────────────────────── Helpers ────────────────────────

def _pill(svg, x, y, w, h, label, fill='light', font_size=FS_SMALL, bold=False):
    """Rounded pill / tag shape."""
    svg.rect(x, y, w, h, fill=fill, rx=h // 2)
    c = 'white' if fill in ('dark', 'darker') else 'text'
    svg.text(x + w / 2, y + h / 2, label, size=font_size, fill=c, bold=bold)


# ──────────────────────── fig3-1 ────────────────────────

def fig3_1():
    """Knowledge map of this chapter"""
    w, h = 860, 580
    svg = SVG(w, h)

    svg.text(w / 2, 32, "Chapter 3: Knowledge Base & RAG — Knowledge Map", size=FS_TITLE, bold=True)

    # --- Row 1: RAG foundations ---
    r1_y = 70
    svg.rect(30, r1_y, 800, 130, fill='white', stroke='border', dash=True)
    svg.text(80, r1_y + 20, "RAG Basics", size=FS_BODY, bold=True, anchor='start')

    boxes_r1 = [
        ("Dense Embedding", 50, "Word2Vec → BGE-M3"),
        ("Sparse Embedding", 230, "TF-IDF / BM25"),
        ("Hybrid Retrieval + Reranking", 410, "Two-tower Retrieval + Cross-Encoder"),
        ("Multimodal Extraction", 650, "Native / Text / Tool"),
    ]
    for label, bx, sub in boxes_r1:
        svg.box(bx, r1_y + 38, 160, 50, label, fill='light', bold=True, font_size=FS_SMALL)
        svg.text(bx + 80, r1_y + 38 + 50 + 18, sub, size=FS_TINY, fill='text_light')

    # --- Arrow down ---
    svg.arrow(w / 2, r1_y + 130, w / 2, r1_y + 160)

    # --- Row 2: Advanced knowledge structuring ---
    r2_y = 230
    svg.rect(30, r2_y, 800, 100, fill='white', stroke='border', dash=True)
    svg.text(80, r2_y + 20, "Learning from Existing Knowledge", size=FS_BODY, bold=True, anchor='start')

    boxes_r2 = [
        ("RAPTOR\n Tree Hierarchical Index", 50),
        ("GraphRAG\n Entity Relation Graph", 230),
        ("Agentic RAG\n Retrieval as Tool", 410),
        ("Context-Aware Retrieval\n Prefix Summary Enhancement", 590),
    ]
    for label, bx in boxes_r2:
        svg.box(bx, r2_y + 35, 160, 55, label, fill='medium', font_size=FS_SMALL)

    # --- Arrow down ---
    svg.arrow(w / 2, r2_y + 100, w / 2, r2_y + 130)

    # --- Row 3: Learning from experience ---
    r3_y = 360
    svg.rect(30, r3_y, 800, 100, fill='white', stroke='border', dash=True)
    svg.text(80, r3_y + 20, "Learning from Autonomous Exploration", size=FS_BODY, bold=True, anchor='start')

    boxes_r3 = [
        ("Post-training\n RL → Muscle Memory", 100),
        ("In-Context Learning\n Inference-time Soft Retrieval", 330),
        ("Externalized Learning\n Knowledge Base + Tool Generation", 560),
    ]
    for label, bx in boxes_r3:
        svg.box(bx, r3_y + 35, 200, 55, label, fill='light', font_size=FS_SMALL)

    # --- Bottom: core insight ---
    svg.rect(180, 490, 500, 44, fill='dark')
    svg.text(w / 2, 512, "Bitter Lesson: Search + Learning = General Method", size=FS_BODY, fill='white', bold=True)
    svg.arrow(w / 2, r3_y + 100, w / 2, 488)

    svg.save(os.path.join(OUT, 'fig3-1.svg'))


# ──────────────────────── fig3-2 ────────────────────────

def fig3_2():
    """RAG End-to-End Pipeline (Concrete Example)"""
    w, h = 880, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "RAG End-to-End Pipeline", size=FS_TITLE, bold=True)

    # Step 1: User query
    svg.box(20, 65, 180, 55, "① User Query", fill='medium', bold=True, font_size=FS_BODY)
    q_lines = ['"How many years for intentional homicide?"']
    svg.text(110, 145, q_lines[0], size=FS_SMALL, fill='text_light')

    svg.arrow(200, 92, 238, 92)

    # Step 2: Retrieval
    svg.box(240, 65, 180, 55, "② Retrieval", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 140, "Dense Retrieval + BM25", size=FS_SMALL, fill='text_light')
    svg.text(330, 160, "→ Top-K Text Chunks", size=FS_SMALL, fill='text_light')

    svg.arrow(420, 92, 458, 92)

    # Step 3: Augmentation
    svg.box(460, 65, 180, 55, "③ Augment", fill='light', bold=True, font_size=FS_BODY)
    svg.text(550, 140, "Query + Retrieved Results", size=FS_SMALL, fill='text_light')
    svg.text(550, 160, "→ Construct Full Prompt", size=FS_SMALL, fill='text_light')

    svg.arrow(640, 92, 678, 92)

    # Step 4: Generation
    svg.box(680, 65, 180, 55, "④ Generate", fill='medium', bold=True, font_size=FS_BODY)
    svg.text(770, 140, "LLM synthesizes context", size=FS_SMALL, fill='text_light')
    svg.text(770, 160, "→ Generate response", size=FS_SMALL, fill='text_light')

    # Concrete data flow example
    svg.line(20, 195, 860, 195, color='dark', dash=True)
    svg.text(w / 2, 215, "Example data flow", size=FS_BODY, bold=True)

    # Retrieved chunks
    svg.rect(20, 235, 400, 90, fill='code_bg', stroke='dark', rx=4)
    svg.text(220, 253, "Retrieved text chunks", size=FS_SMALL, bold=True)
    svg.mono(30, 278, "Article 232 of the Criminal Law: Whoever intentionally kills another shall be sentenced to death,", size=FS_TINY)
    svg.mono(30, 298, "life imprisonment or fixed-term imprisonment of not less than ten years...", size=FS_TINY)

    # Augmented prompt
    svg.rect(440, 235, 420, 90, fill='code_bg', stroke='dark', rx=4)
    svg.text(650, 253, "Augmented Prompt", size=FS_SMALL, bold=True)
    svg.mono(450, 278, "Answer the question based on the following legal provisions:", size=FS_TINY)
    svg.mono(450, 298, "[Article 232 of the Criminal Law...] Q: What is the sentence for intentional homicide?", size=FS_TINY)

    # Generated answer
    svg.rect(20, 345, 840, 80, fill='light', stroke='border')
    svg.text(w / 2, 363, "Generated response", size=FS_SMALL, bold=True)
    svg.mono(30, 390, "According to Article 232 of the Criminal Law, the crime of intentional homicide is punishable by death, life imprisonment, or fixed-term imprisonment of not less than ten years;", size=FS_TINY)
    svg.mono(30, 412, "if the circumstances are minor, the sentence is fixed-term imprisonment of not less than three years but not more than ten years.", size=FS_TINY)

    svg.save(os.path.join(OUT, 'fig3-2.svg'))


# ──────────────────────── fig3-3 ────────────────────────

def fig3_3():
    """Evolution of dense embedding techniques"""
    w, h = 860, 340
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Evolution of dense embedding techniques", size=FS_TITLE, bold=True)

    items = [
        ("Word2Vec", "2013", "300D\nStatic word vectors", "Co-occurrence\nPredictive training"),
        ("GloVe", "2014", "300D\nGlobal statistics", "Matrix factorization\n+ Co-occurrence"),
        ("BERT", "2018", "768D\nContext-aware", "Transformer\nMLM pre-training"),
        ("Sentence-BERT", "2019", "768D\nSentence-level embeddings", "Siamese network\nContrastive learning"),
        ("BGE-M3", "2024", "1024D\nMultilingual long texts", "Multi-stage\nHybrid training"),
    ]
    n = len(items)
    pad_l, pad_r = 80, 80
    usable = w - pad_l - pad_r
    gap = usable / (n - 1)
    line_y = 90

    svg.line(pad_l - 30, line_y, w - pad_r + 30, line_y, color='dark')
    svg.elems.append(
        f'<polygon points="{w - pad_r + 30},{line_y - 6} {w - pad_r + 42},{line_y} '
        f'{w - pad_r + 30},{line_y + 6}" fill="{COLORS["dark"]}"/>'
    )

    for i, (name, year, dims, training) in enumerate(items):
        x = pad_l + i * gap
        svg.circle(x, line_y, 8, fill='dark')
        svg.text(x, line_y - 30, name, size=FS_BODY, bold=True)
        svg.text(x, line_y + 28, year, size=FS_SMALL, fill='text_light')

        svg.rect(x - 65, line_y + 50, 130, 55, fill='light')
        for j, dl in enumerate(dims.split('\n')):
            svg.text(x, line_y + 68 + j * 22, dl, size=FS_SMALL)

        svg.rect(x - 65, line_y + 115, 130, 55, fill='code_bg', stroke='dark', rx=4)
        for j, tl in enumerate(training.split('\n')):
            svg.text(x, line_y + 133 + j * 22, tl, size=FS_SMALL, fill='text_light')

    # Bottom labels
    svg.text(pad_l + gap * 0.5, h - 18,
             "Static word vectors (one vector per word)", size=FS_SMALL, fill='text_light')
    svg.text(pad_l + gap * 3.5, h - 18,
             "Context-aware embeddings (multiple vectors per word)", size=FS_SMALL, fill='text_light')

    svg.line(pad_l + gap * 1.5, 75, pad_l + gap * 1.5, h - 35, color='dark', dash=True)

    svg.save(os.path.join(OUT, 'fig3-3.svg'))


# ──────────────────────── fig3-4 ────────────────────────

def fig3_4():
    """HNSW index structure"""
    w, h = 750, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "HNSW index structure", size=FS_TITLE, bold=True)

    layers = [
        ("Layer 2 (sparse · long-range connections)", 70, 3),
        ("Layer 1 (medium density)", 185, 6),
        ("Layer 0 (dense · all nodes)", 300, 10),
    ]
    for label, base_y, count in layers:
        svg.rect(30, base_y - 30, w - 60, 90, fill='white', stroke='dark', dash=True)
        svg.text(100, base_y - 14, label, size=FS_SMALL, fill='text_light', anchor='start')
        spacing = (w - 140) / (count + 1)
        positions = []
        for j in range(count):
            cx = 70 + spacing * (j + 1)
            cy = base_y + 25
            svg.circle(cx, cy, 14, fill='light')
            positions.append((cx, cy))
        for j in range(count - 1):
            skip = 1 if count <= 6 else (2 if j % 2 == 0 else 1)
            if j + skip < count:
                x1, y1 = positions[j]
                x2, y2 = positions[j + skip]
                svg.line(x1 + 14, y1, x2 - 14, y2, color='dark')

    # Search path arrows
    svg.arrow(w / 2, 130, w / 2 - 50, 165, color='border')
    svg.text(w / 2 + 80, 148, "Search starts from the top level", size=FS_SMALL, fill='text_light')
    svg.arrow(w / 2 - 50, 245, w / 2 - 80, 280, color='border')
    svg.text(w / 2 + 60, 263, "Refine layer by layer downward", size=FS_SMALL, fill='text_light')

    # Key properties
    svg.rect(50, h - 45, 300, 32, fill='light')
    svg.text(200, h - 29, "Supports incremental updates · High recall", size=FS_SMALL, bold=True)
    svg.rect(400, h - 45, 300, 32, fill='code_bg', stroke='dark', rx=4)
    svg.text(550, h - 29, "O(log N) query complexity", size=FS_SMALL)

    svg.save(os.path.join(OUT, 'fig3-4.svg'))


# ──────────────────────── fig3-5 ────────────────────────

def fig3_5():
    """BM25 scoring mechanism"""
    w, h = 800, 380
    svg = SVG(w, h)
    svg.text(w / 2, 30, "BM25 scoring mechanism", size=FS_TITLE, bold=True)

    # Formula
    svg.rect(40, 50, w - 80, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(60, 75,
             "Score(Q,D) = Σ IDF(qi) × TF(qi,D)×(k1+1) / (TF + k1×(1-b+b×|D|/avgdl))",
             size=FS_SMALL)

    # Three components
    boxes = [
        ("Term frequency saturation (TF)", 40, 'light', [
            "k₁ controls saturation speed",
            "TF ↑ but contribution diminishes",
            "Example: 5→10 occurrences",
            "Score increases only ~20%",
        ]),
        ("Inverse document frequency (IDF)", 290, 'light', [
            "Measures word rarity",
            "\"的\" → IDF ≈ 0",
            "\"量刑\" → IDF ≈ 5.2",
            "Rare word weight >> common word",
        ]),
        ("Length normalization (b)", 540, 'light', [
            "b ∈ [0,1] normalization strength",
            "b=0: ignore length",
            "b=1: full normalization",
            "Avoid bias towards long documents",
        ]),
    ]
    for title, bx, fill, details in boxes:
        svg.rect(bx, 120, 220, 170, fill=fill)
        svg.text(bx + 110, 148, title, size=FS_BODY, bold=True)
        svg.line(bx + 20, 163, bx + 200, 163, color='dark')
        for k, line in enumerate(details):
            svg.text(bx + 110, 190 + k * 28, line, size=FS_SMALL, fill='text_light')

    # Result bar
    for bx in [150, 400, 650]:
        svg.line(bx, 290, bx, 315, color='dark')
    svg.rect(40, 315, w - 80, 48, fill='medium')
    svg.text(w / 2, 339, "Final score = Σ (TF saturation × IDF weighting × length normalization)", size=FS_BODY, bold=True)

    svg.save(os.path.join(OUT, 'fig3-5.svg'))


# ──────────────────────── fig3-6 ────────────────────────

def fig3_6():
    """Hybrid retrieval and re-ranking pipeline (with score examples)"""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Hybrid retrieval and re-ranking pipeline", size=FS_TITLE, bold=True)

    # Query
    svg.rect(30, 55, 160, 50, fill='medium')
    svg.text(110, 73, "User query", size=FS_BODY, bold=True)
    svg.mono(110, 93, '"kitty behavior"', size=FS_TINY, anchor='middle')

    # Dense retrieval
    svg.arrow(190, 68, 238, 68)
    svg.box(240, 50, 180, 50, "Dense retrieval", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 118, "Semantic matching: kitty ≈ cat", size=FS_SMALL, fill='text_light')

    dense_results = [
        ("doc3: \"feline habits and cat play...\"", "cos=0.87"),
        ("doc7: \"cat grooming patterns...\"", "cos=0.82"),
        ("doc1: \"pet care basics...\"", "cos=0.71"),
    ]
    for i, (doc, score) in enumerate(dense_results):
        y = 140 + i * 32
        svg.mono(250, y, doc, size=FS_TINY)
        svg.text(700, y, score, size=FS_TINY, fill='text_light', anchor='start')

    # Sparse retrieval
    svg.arrow(190, 90, 238, 270)
    svg.box(240, 250, 180, 50, "Sparse retrieval (BM25)", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 318, "Exact match: \"kitty\" keyword", size=FS_SMALL, fill='text_light')

    sparse_results = [
        ("doc5: \"kitty litter training...\"", "BM25=8.4"),
        ("doc9: \"kitty adoption guide...\"", "BM25=6.1"),
        ("doc2: \"kitten health tips...\"", "BM25=3.2"),
    ]
    for i, (doc, score) in enumerate(sparse_results):
        y = 340 + i * 32
        svg.mono(250, y, doc, size=FS_TINY)
        svg.text(700, y, score, size=FS_TINY, fill='text_light', anchor='start')

    # Merge + rerank
    svg.arrow(770, 180, 808, 220)
    svg.arrow(770, 370, 808, 330)

    svg.rect(790, 215, 70, 120, fill='medium')
    svg.text(825, 250, "Merge", size=FS_BODY, bold=True)
    svg.text(825, 275, "Deduplicate", size=FS_BODY, bold=True)
    svg.text(825, 300, "6→5", size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-6.svg'))


# ──────────────────────── fig3-7 ────────────────────────

def fig3_7():
    """RAPTOR tree structure"""
    w, h = 800, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "RAPTOR tree hierarchical index", size=FS_TITLE, bold=True)

    # Root
    svg.box(300, 55, 200, 50, "Global summary", fill='dark', bold=True, font_size=FS_BODY)
    svg.text(300 + 200 + 15, 80, "← Root node", size=FS_SMALL, fill='text_light', anchor='start')

    # Mid-level
    mid_nodes = [("Cluster summary A", 80), ("Cluster summary B", 320), ("Cluster summary C", 560)]
    for label, x in mid_nodes:
        svg.box(x, 150, 160, 48, label, fill='medium', font_size=FS_BODY)
    svg.line(400, 105, 160, 150, color='border')
    svg.line(400, 105, 400, 150, color='border')
    svg.line(400, 105, 640, 150, color='border')
    svg.text(35, 230, "Middle layer ↑", size=FS_SMALL, fill='text_light', anchor='start')

    # Leaf nodes — 7 boxes evenly distributed, narrower to avoid overlap
    chunks = [
        [(40, "Text chunk 1"), (140, "Text chunk 2"), (240, "Text chunk 3")],   # Cluster A → cluster center ~160
        [(360, "Text chunk 4"), (460, "Text chunk 5")],                    # Cluster B → cluster center ~410
        [(560, "Text chunk 6"), (660, "Text chunk 7")],                    # Cluster C → cluster center ~640
    ]
    leaf_w = 88
    mid_cxs = [160, 400, 640]
    for gi, group in enumerate(chunks):
        for cx, label in group:
            svg.box(cx, 250, leaf_w, 40, label, fill='light', font_size=FS_SMALL)
            svg.line(cx + leaf_w / 2, 250, mid_cxs[gi], 198, color='dark')
    svg.text(35, 295, "Leaf layer ↑", size=FS_SMALL, fill='text_light', anchor='start')

    # Original document
    svg.rect(40, 320, 720, 55, fill='white', stroke='dark', dash=True)
    svg.text(400, 340, "Original document", size=FS_BODY, fill='text_light')
    for bx in range(60, 720, 110):
        svg.rect(bx, 350, 90, 16, fill='light')

    # Bottom label
    svg.text(w / 2, h - 20, "Bottom-up recursive abstraction: details → topics → global overview", size=FS_BODY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-7.svg'))


# ──────────────────────── fig3-8 ────────────────────────

def fig3_8():
    """GraphRAG relational network"""
    w, h = 750, 430
    svg = SVG(w, h)
    svg.text(w / 2, 28, "GraphRAG entity-relation knowledge graph", size=FS_TITLE, bold=True)

    nodes = [
        ("Intel", 375, 100, 'medium'),
        ("SSE", 150, 190, 'light'),
        ("AVX", 550, 190, 'light'),
        ("XMM reg", 100, 320, 'light'),
        ("ADDPS", 280, 340, 'light'),
        ("YMM reg", 520, 320, 'light'),
        ("FP ops", 375, 250, 'light'),
    ]
    node_r = 42

    # Community box (drawn first, as background layer, to avoid covering subsequent nodes and edges)
    svg.rect(50, 275, 300, 110, fill='none', stroke='border', dash=True)
    svg.text(200, 395, "Community: SSE instruction set", size=FS_SMALL, fill='text_light')

    for label, x, y, fill in nodes:
        svg.circle(x, y, node_r, fill=fill, label=label, font_size=FS_SMALL)

    edges = [
        (0, 1, "Development"), (0, 2, "Development"),
        (1, 3, "Usage"), (1, 6, ""), (1, 4, "Contains"),
        (2, 5, "Usage"), (2, 6, "Execute"),
        (6, 3, ""), (6, 5, "Operation"),
    ]
    for i, j, elabel in edges:
        x1, y1 = nodes[i][1], nodes[i][2]
        x2, y2 = nodes[j][1], nodes[j][2]
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / dist, dy / dist
        ax1 = x1 + ux * (node_r + 3)
        ay1 = y1 + uy * (node_r + 3)
        ax2 = x2 - ux * (node_r + 14)
        ay2 = y2 - uy * (node_r + 14)
        svg.arrow(ax1, ay1, ax2, ay2, label=elabel, color='dark')

    svg.save(os.path.join(OUT, 'fig3-8.svg'))


# ──────────────────────── fig3-9 ────────────────────────

def fig3_9():
    """Agentic RAG vs Non-Agentic RAG (Specific Example)"""
    w, h = 880, 560
    svg = SVG(w, h)
    col_w = 400
    lx, rx = 20, 460

    # --- Left: Non-Agentic ---
    svg.rect(lx, 50, col_w, 45, fill='medium')
    svg.text(lx + col_w / 2, 73, "Non-Agentic RAG", size=FS_BODY, bold=True)

    steps_l = [
        ("Query: \"How to sentence for causing serious injury by negligence while drunk \nand with a previous theft conviction?\"", 'light'),
        ("Single retrieval:\n\"Sentencing for causing serious injury by negligence\"", 'light'),
        ("Retrieval result: Only found basic provisions for negligent injury\n (incomplete context)", 'code_bg'),
        ("Direct generation: Missing \"drunk\"\nand \"previous conviction\" influencing factors", 'light'),
    ]
    prev_y = 95
    for i, (s, fill) in enumerate(steps_l):
        y = 110 + i * 108
        svg.box(lx + 30, y, 340, 80, s, fill=fill, font_size=FS_SMALL)
        if i > 0:
            svg.arrow(lx + 200, prev_y + 80 + 2, lx + 200, y - 2)
        prev_y = y

    svg.text(lx + col_w / 2, h - 15, "Single pass · Incomplete information", size=FS_BODY, fill='text_light')

    # --- Separator ---
    svg.line(440, 50, 440, h - 5, color='dark', dash=True)

    # --- Right: Agentic ---
    svg.rect(rx, 50, col_w, 45, fill='medium')
    svg.text(rx + col_w / 2, 73, "Agentic RAG (ReAct)", size=FS_BODY, bold=True)

    steps_r = [
        ("Thought: Need to decompose into 3 sub-questions", 'light'),
        ("Search ①: \"Sentencing for causing serious injury by negligence\"\nSearch ②: \"Criminal liability for drunkenness\"\nSearch ③: \"Impact of previous theft conviction\"", 'code_bg'),
        ("Observation: Found basic provisions but\nmissing link between \"previous conviction\" and \"negligent injury\"", 'light'),
        ("Search ④: \"Recidivism different crimes\njudicial interpretation\"", 'code_bg'),
        ("Synthesis: Complete answer including all\nlegal provisions and sentencing analysis", 'medium'),
    ]
    ys = []
    for i, (s, fill) in enumerate(steps_r):
        y = 105 + i * 86
        hh = 68
        svg.box(rx + 30, y, 340, hh, s, fill=fill, font_size=FS_SMALL)
        ys.append(y)
        if i > 0:
            svg.arrow(rx + 200, ys[i - 1] + hh + 2, rx + 200, y - 2)

    # Iteration loop arrow
    loop_x = rx + 370 + 10
    svg.elems.append(
        f'<path d="M {loop_x},{ys[2] + 34} C {loop_x + 28},{ys[2] + 34} '
        f'{loop_x + 28},{ys[1] + 34} {loop_x},{ys[1] + 34}" '
        f'fill="none" stroke="{COLORS["border"]}" stroke-width="{STROKE_W}" '
        f'stroke-dasharray="6,3" marker-end="url(#ah)"/>'
    )
    svg.text(loop_x + 4, (ys[1] + ys[2]) / 2 + 34, "Iteration", size=FS_SMALL, fill='text_light',
             anchor='start')

    svg.text(rx + col_w / 2, h - 15, "Multi-round iteration · Complete information", size=FS_BODY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-9.svg'))


# ──────────────────────── fig3-10 ────────────────────────

def fig3_10():
    """Agentic RAG System Architecture (Experiment 3.6)"""
    w, h = 880, 500
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experiment 3.6: Agentic RAG System Architecture", size=FS_TITLE, bold=True)

    # Agent core
    svg.rect(220, 55, 440, 200, fill='white', stroke='border')
    svg.text(440, 78, "Agent (ReAct Loop)", size=FS_BODY, bold=True)

    # ReAct steps inside agent
    react_items = [
        ("① Thought", 240, 100, 180, 45, 'light'),
        ("② Action", 460, 100, 180, 45, 'medium'),
        ("③ Observation", 350, 180, 180, 45, 'light'),
    ]
    for label, bx, by, bw, bh, fill in react_items:
        svg.box(bx, by, bw, bh, label, fill=fill, font_size=FS_SMALL, bold=True)

    svg.arrow(420, 122, 458, 122)
    svg.arrow(640, 130, 530, 178, color='border')
    svg.arrow(350, 202, 280, 145, color='border')

    # Loop label
    svg.text(360, 165, "Loop until information is sufficient", size=FS_TINY, fill='text_light')

    # User
    svg.box(20, 95, 160, 55, "User query", fill='medium', bold=True, font_size=FS_BODY)
    svg.arrow(180, 122, 218, 122)

    # Final answer
    svg.box(700, 95, 160, 55, "Final answer", fill='medium', bold=True, font_size=FS_BODY)
    svg.arrow(660, 122, 698, 122)

    # Tool layer
    svg.rect(100, 290, 680, 85, fill='white', stroke='border', dash=True)
    svg.text(440, 312, "Tool layer", size=FS_BODY, bold=True)
    tools = [
        ("knowledge_base_search", 120, 330, 220),
        ("web_search", 370, 330, 140),
        ("code_interpreter", 540, 330, 160),
    ]
    for label, tx, ty, tw in tools:
        svg.rect(tx, ty, tw, 35, fill='light')
        svg.mono(tx + tw / 2, ty + 17, label, size=FS_TINY, anchor='middle')

    svg.arrow(440, 255, 440, 288)
    svg.arrow(440, 288, 440, 255)

    # Knowledge base backends
    svg.rect(100, 400, 680, 85, fill='white', stroke='dark', dash=True)
    svg.text(440, 420, "Knowledge base backend (switchable)", size=FS_BODY, bold=True)
    backends = [
        ("retrieval-pipeline\nHybrid retrieval", 120),
        ("structured-index\nRAPTOR/GraphRAG", 340),
        ("contextual-retrieval\nContext-aware", 560),
    ]
    for label, bx in backends:
        svg.box(bx, 435, 180, 45, label, fill='light', font_size=FS_SMALL)

    svg.arrow(230, 365, 230, 398)
    svg.arrow(440, 375, 440, 398)

    svg.save(os.path.join(OUT, 'fig3-10.svg'))


# ──────────────────────── fig3-11 ────────────────────────

def fig3_11():
    """Context-aware retrieval (specific prefix example)"""
    w, h = 880, 430
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Context-aware retrieval", size=FS_TITLE, bold=True)

    # Left: Traditional chunking
    svg.rect(20, 55, 400, 170, fill='white', stroke='border')
    svg.text(220, 78, "Traditional chunking (no context)", size=FS_BODY, bold=True)

    svg.rect(40, 95, 360, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(50, 112, "The company's second-quarter revenue grew by 3%,", size=FS_TINY)
    svg.mono(50, 132, "mainly driven by new product lines.", size=FS_TINY)

    svg.text(220, 170, "Question: \"Who is \"the company\"? Which year?", size=FS_SMALL, fill='text_light')
    svg.text(220, 195, "→ Retrieval matches revenue data of many irrelevant companies", size=FS_SMALL, fill='text_light')

    # Right: Contextual
    svg.rect(460, 55, 400, 170, fill='white', stroke='border')
    svg.text(660, 78, "Context-aware chunking", size=FS_BODY, bold=True)

    svg.rect(480, 95, 360, 35, fill='medium')
    svg.mono(490, 113, "[ACME Company 2025 Q2 Earnings Report · Key Performance Indicators]", size=FS_TINY)

    svg.rect(480, 130, 360, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(490, 148, "The company's second-quarter revenue grew by 3%,", size=FS_TINY)
    svg.mono(490, 168, "mainly driven by new product lines.", size=FS_TINY)

    svg.text(660, 200, "→ Exact match ACME + Q2 + revenue growth", size=FS_SMALL, fill='text_light')

    # Arrow between
    svg.text(440, 140, "→", size=FS_TITLE, bold=True)

    # Process flow
    svg.line(20, 250, 860, 250, color='dark', dash=True)
    svg.text(w / 2, 275, "Indexing stage: LLM generates context prefix", size=FS_BODY, bold=True)

    flow_y = 300
    svg.box(30, flow_y, 180, 55, "Original document", fill='light', bold=True, font_size=FS_BODY)
    svg.arrow(210, flow_y + 27, 248, flow_y + 27)

    svg.box(250, flow_y, 180, 55, "Chunking", fill='light', bold=True, font_size=FS_BODY)
    svg.arrow(430, flow_y + 27, 468, flow_y + 27)

    svg.box(470, flow_y, 180, 55, "LLM generates prefix\n(prompt caching)", fill='medium',
            font_size=FS_SMALL, bold=True)
    svg.arrow(650, flow_y + 27, 688, flow_y + 27)

    svg.box(690, flow_y, 170, 55, "Prefix + original text\n→ Index", fill='light', font_size=FS_SMALL, bold=True)

    # Stats
    svg.text(w / 2, h - 20,
             "Effect: Retrieval failure rate ↓49% (+BM25), ↓67% (+reranking) — Anthropic data",
             size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-11.svg'))


# ──────────────────────── fig3-12 ────────────────────────

def fig3_12():
    """Structured knowledge extraction pipeline (Experiment 3.10)"""
    w, h = 880, 510
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experiment 3.10: Structured knowledge extraction (judicial precedents)", size=FS_TITLE, bold=True)

    # Phase 1 header
    svg.rect(20, 55, 840, 200, fill='white', stroke='border')
    svg.text(440, 78, "Phase 1: Knowledge extraction and structuring", size=FS_BODY, bold=True)

    # Raw cases
    svg.rect(40, 95, 180, 65, fill='code_bg', stroke='dark', rx=4)
    svg.text(130, 113, "Original judgment documents", size=FS_SMALL, bold=True)
    svg.mono(50, 138, "CAIL2018 dataset", size=FS_TINY)

    svg.arrow(220, 127, 258, 127)

    # LLM extraction
    svg.rect(260, 95, 180, 65, fill='medium')
    svg.text(350, 113, "LLM factor discovery", size=FS_SMALL, bold=True)
    svg.text(350, 138, "Bottom-up Schema", size=FS_SMALL, fill='text_light')

    svg.arrow(440, 127, 478, 127)

    # Structured JSON
    svg.rect(480, 95, 200, 65, fill='code_bg', stroke='dark', rx=4)
    svg.text(580, 113, "Structured JSON", size=FS_SMALL, bold=True)
    svg.mono(490, 138, "{voluntary_surrender:true, compensation:500000,", size=FS_TINY)
    svg.mono(490, 155, " injury_level:severe_second_degree}", size=FS_TINY)

    # Schema detail
    svg.rect(40, 170, 400, 70, fill='light')
    svg.text(240, 188, "Modular data schema", size=FS_SMALL, bold=True)
    svg.text(240, 212, "Core schema (voluntary surrender/compensation/criminal record) + charge extension schema", size=FS_SMALL, fill='text_light')
    svg.text(240, 232, "(theft→amount involved, injury→injury level)", size=FS_SMALL, fill='text_light')

    # Phase 2 header
    svg.rect(20, 270, 840, 200, fill='white', stroke='border')
    svg.text(440, 293, "Phase 2: Factor analysis and knowledge modeling", size=FS_BODY, bold=True)

    # Vectorization
    svg.rect(40, 310, 200, 65, fill='light')
    svg.text(140, 328, "Feature vectorization", size=FS_SMALL, bold=True)
    svg.text(140, 350, "One-hot encoding + multi-hot encoding", size=FS_SMALL, fill='text_light')
    svg.text(140, 370, "+ log transformation + standardization", size=FS_SMALL, fill='text_light')

    svg.arrow(240, 342, 278, 342)

    # Clustering
    svg.rect(280, 310, 200, 65, fill='medium')
    svg.text(380, 328, "HDBSCAN clustering", size=FS_SMALL, bold=True)
    svg.text(380, 350, "discover \"case prototype\"", size=FS_SMALL, fill='text_light')
    svg.text(380, 370, "e.g., minor quarrel → minor injury", size=FS_SMALL, fill='text_light')

    svg.arrow(480, 342, 518, 342)

    # Factor importance
    svg.rect(520, 310, 200, 65, fill='light')
    svg.text(620, 328, "factor importance model", size=FS_SMALL, bold=True)
    svg.text(620, 350, "quantify the weight of each factor", size=FS_SMALL, fill='text_light')
    svg.text(620, 370, "build sentencing decision logic", size=FS_SMALL, fill='text_light')

    # Application
    svg.arrow(620, 375, 620, 400)
    svg.rect(40, 400, 720, 60, fill='light')
    svg.text(400, 420, "Application: conversational legal advice Agent", size=FS_BODY, bold=True)
    svg.text(400, 445, "guide questions by factor importance → retrieve similar case prototypes → data-driven sentencing analysis",
             size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-12.svg'))


# ──────────────────────── fig3-13 ────────────────────────

def fig3_13():
    """Externalized learning loop (concrete example)"""
    w, h = 880, 490
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Externalized learning: a closed loop from experience to capability", size=FS_TITLE, bold=True)

    # Central Agent
    cx, cy = 440, 210
    svg.circle(cx, cy, 55, fill='medium', label="Agent", font_size=FS_BODY)

    # 5 steps around the loop
    steps = [
        ("① Execute task", 120, 100, "process refund request\ncall customer service API"),
        ("② Get feedback", 680, 100, "successfully refunded $45\nfound need to verify last four digits"),
        ("③ Reflect and distill", 680, 310, "LLM summarizes experience:\n\"Company A refund requires verification\""),
        ("④ Store in knowledge base", 340, 380, "experience → vectorized index\nprocess → generate tool code"),
        ("⑤ Future retrieval and reuse", 120, 310, "similar task → retrieve experience\ndirectly reuse successful strategy"),
    ]

    positions = []
    for label, x, y, detail in steps:
        svg.box(x, y, 200, 80, label + "\n" + detail,
                fill='light', font_size=FS_SMALL)
        positions.append((x + 100, y + 40))

    # Arrows connecting steps
    arrow_pairs = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 0),
    ]
    for si, ei in arrow_pairs:
        sx, sy = positions[si]
        ex, ey = positions[ei]
        dx, dy = ex - sx, ey - sy
        dist = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / dist, dy / dist
        svg.arrow(sx + ux * 105, sy + uy * 45,
                  ex - ux * 105, ey - uy * 45, color='dark')

    # Two output types
    svg.rect(30, 395, 180, 28, fill='dark')
    svg.text(120, 409, "Knowledge: summary/tree summary", size=FS_SMALL, fill='white')
    svg.rect(670, 395, 180, 28, fill='dark')
    svg.text(760, 409, "Tool: process → code", size=FS_SMALL, fill='white')

    svg.save(os.path.join(OUT, 'fig3-13.svg'))


# ──────────────────────── fig3-14 ────────────────────────

def fig3_14():
    """GAIA experience learning system (Experiment 3.11)"""
    w, h = 880, 510
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experiment 3.11: GAIA experience learning system", size=FS_TITLE, bold=True)

    box_h = 60
    step_gap = 75
    base_y = 100

    # --- Left: Learning Mode ---
    lx = 20
    svg.rect(lx, 55, 400, 420, fill='white', stroke='border')
    svg.text(lx + 200, 80, "Learning Mode", size=FS_BODY, bold=True)

    learn_steps = [
        ("GAIA task", 'medium', "complex multi-step problem"),
        ("Agent execution", 'light', "browser + file + code interpreter"),
        ("Task successful?", 'light', "Auto Evaluation (AWorld)"),
        ("LLM Reflection & Summary", 'medium', "Extract Strategy Summary"),
        ("Experience → Vectorization", 'light', "Store in Experience Knowledge Base"),
    ]
    for i, (label, fill, sub) in enumerate(learn_steps):
        y = base_y + i * step_gap
        svg.box(lx + 50, y, 300, box_h, label, sublabel=sub, fill=fill, bold=True, font_size=FS_BODY)
        if i > 0:
            svg.arrow(lx + 200, base_y + (i - 1) * step_gap + box_h + 2, lx + 200, y - 2)

    # --- Right: Apply Mode ---
    rx = 460
    svg.rect(rx, 55, 400, 420, fill='white', stroke='border')
    svg.text(rx + 200, 80, "Apply Mode", size=FS_BODY, bold=True)

    apply_steps = [
        ("New GAIA Task", 'medium', "Receive New Question"),
        ("Semantic Retrieval of Experience", 'light', "Search for Similar Tasks in Experience Base"),
        ("Inject into System Prompt", 'medium', "Historical Successful Strategies as Examples"),
        ("Agent execution", 'light', "Leverage Experience for More Efficient Problem Solving"),
        ("Success Rate ↑ Efficiency ↑", 'dark', "Self-Evolution: Getting Stronger Over Time"),
    ]
    for i, (label, fill, sub) in enumerate(apply_steps):
        y = base_y + i * step_gap
        svg.box(rx + 50, y, 300, box_h, label, sublabel=sub, fill=fill, bold=True, font_size=FS_BODY)
        if i > 0:
            svg.arrow(rx + 200, base_y + (i - 1) * step_gap + box_h + 2, rx + 200, y - 2)

    # Arrow from learning to apply: the experience KB (centered vertically)
    kb_cy = base_y + 2 * step_gap + box_h / 2  #Align with Step 3 Center
    kb_x1, kb_x2 = 375, 505
    svg.rect(kb_x1, kb_cy - 25, kb_x2 - kb_x1, 50, fill='dark')
    svg.text((kb_x1 + kb_x2) / 2, kb_cy - 8, "Experience Knowledge Base", size=FS_SMALL, fill='white', bold=True)
    svg.text((kb_x1 + kb_x2) / 2, kb_cy + 12, "(Vector Index)", size=FS_TINY, fill='white')

    # Last learn step right-middle → KB left
    last_y = base_y + 4 * step_gap + box_h / 2
    svg.arrow(lx + 350, last_y, kb_x1 - 2, kb_cy + 10)
    # KB right → second apply step left-middle
    apply2_y = base_y + 1 * step_gap + box_h / 2
    svg.arrow(kb_x2 + 2, kb_cy - 10, rx + 50, apply2_y)

    svg.save(os.path.join(OUT, 'fig3-14.svg'))


# ──────────────────────── Main ────────────────────────

ALL_FIGS = [
    fig3_1, fig3_2, fig3_3, fig3_4, fig3_5, fig3_6, fig3_7,
    fig3_8, fig3_9, fig3_10, fig3_11, fig3_12, fig3_13, fig3_14,
]

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for fn in ALL_FIGS:
        fn()
        print(f"  ✓ {fn.__name__}: {fn.__doc__}")
    print(f"\nDone — {len(ALL_FIGS)} SVGs saved to {OUT}/")
