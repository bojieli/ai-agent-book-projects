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

    svg.text(w / 2, 32, "Bab 3: Basis Pengetahuan & RAG — Peta Pengetahuan", size=FS_TITLE, bold=True)

    # --- Row 1: RAG foundations ---
    r1_y = 70
    svg.rect(30, r1_y, 800, 130, fill='white', stroke='border', dash=True)
    svg.text(80, r1_y + 20, "Dasar-dasar RAG", size=FS_BODY, bold=True, anchor='start')

    boxes_r1 = [
        ("Embedding Padat", 50, "Word2Vec → BGE-M3"),
        ("Embedding Jarang", 230, "TF-IDF / BM25"),
        ("Pengambilan Hibrida + Pemeringkatan Ulang", 410, "Pengambilan Dua Menara + Cross-Encoder"),
        ("Ekstraksi Multimodal", 650, "Asli / Teks / Alat"),
    ]
    for label, bx, sub in boxes_r1:
        svg.box(bx, r1_y + 38, 160, 50, label, fill='light', bold=True, font_size=FS_SMALL)
        svg.text(bx + 80, r1_y + 38 + 50 + 18, sub, size=FS_TINY, fill='text_light')

    # --- Arrow down ---
    svg.arrow(w / 2, r1_y + 130, w / 2, r1_y + 160)

    # --- Row 2: Advanced knowledge structuring ---
    r2_y = 230
    svg.rect(30, r2_y, 800, 100, fill='white', stroke='border', dash=True)
    svg.text(80, r2_y + 20, "Belajar dari Pengetahuan yang Ada", size=FS_BODY, bold=True, anchor='start')

    boxes_r2 = [
        ("RAPTOR\n Indeks Hierarkis Pohon", 50),
        ("GraphRAG\n Grafik Relasi Entitas", 230),
        ("RAG Agentic\n Pengambilan sebagai Alat", 410),
        ("Pengambilan Sadar Konteks\n Peningkatan Ringkasan Prefiks", 590),
    ]
    for label, bx in boxes_r2:
        svg.box(bx, r2_y + 35, 160, 55, label, fill='medium', font_size=FS_SMALL)

    # --- Arrow down ---
    svg.arrow(w / 2, r2_y + 100, w / 2, r2_y + 130)

    # --- Row 3: Learning from experience ---
    r3_y = 360
    svg.rect(30, r3_y, 800, 100, fill='white', stroke='border', dash=True)
    svg.text(80, r3_y + 20, "Belajar dari Eksplorasi Otonom", size=FS_BODY, bold=True, anchor='start')

    boxes_r3 = [
        ("Pasca-pelatihan\n RL → Memori Otot", 100),
        ("Pembelajaran Dalam Konteks\n Pengambilan Halus Saat Inferensi", 330),
        ("Pembelajaran Eksternal\n Basis Pengetahuan + Pembuatan Alat", 560),
    ]
    for label, bx in boxes_r3:
        svg.box(bx, r3_y + 35, 200, 55, label, fill='light', font_size=FS_SMALL)

    # --- Bottom: core insight ---
    svg.rect(180, 490, 500, 44, fill='dark')
    svg.text(w / 2, 512, "Pelajaran Pahit: Pencarian + Pembelajaran = Metode Umum", size=FS_BODY, fill='white', bold=True)
    svg.arrow(w / 2, r3_y + 100, w / 2, 488)

    svg.save(os.path.join(OUT, 'fig3-1.svg'))


# ──────────────────────── fig3-2 ────────────────────────

def fig3_2():
    """RAG End-to-End Pipeline (Concrete Example)"""
    w, h = 880, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Alur Kerja RAG End-to-End", size=FS_TITLE, bold=True)

    # Step 1: User query
    svg.box(20, 65, 180, 55, "① Kueri Pengguna", fill='medium', bold=True, font_size=FS_BODY)
    q_lines = ['"Berapa tahun hukuman untuk pembunuhan disengaja?"']
    svg.text(110, 145, q_lines[0], size=FS_SMALL, fill='text_light')

    svg.arrow(200, 92, 238, 92)

    # Step 2: Retrieval
    svg.box(240, 65, 180, 55, "② Pengambilan", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 140, "Pengambilan Padat + BM25", size=FS_SMALL, fill='text_light')
    svg.text(330, 160, "→ Kepingan Teks Top-K", size=FS_SMALL, fill='text_light')

    svg.arrow(420, 92, 458, 92)

    # Step 3: Augmentation
    svg.box(460, 65, 180, 55, "③ Augmentasi", fill='light', bold=True, font_size=FS_BODY)
    svg.text(550, 140, "Kueri + Hasil Pengambilan", size=FS_SMALL, fill='text_light')
    svg.text(550, 160, "→ Bangun Prompt Penuh", size=FS_SMALL, fill='text_light')

    svg.arrow(640, 92, 678, 92)

    # Step 4: Generation
    svg.box(680, 65, 180, 55, "④ Pembangkitan", fill='medium', bold=True, font_size=FS_BODY)
    svg.text(770, 140, "LLM mensintesis konteks", size=FS_SMALL, fill='text_light')
    svg.text(770, 160, "→ Bangkitkan respons", size=FS_SMALL, fill='text_light')

    # Concrete data flow example
    svg.line(20, 195, 860, 195, color='dark', dash=True)
    svg.text(w / 2, 215, "Contoh aliran data", size=FS_BODY, bold=True)

    # Retrieved chunks
    svg.rect(20, 235, 400, 90, fill='code_bg', stroke='dark', rx=4)
    svg.text(220, 253, "Kepingan teks yang diambil", size=FS_SMALL, bold=True)
    svg.mono(30, 278, "Pasal 232 KUHP: Barang siapa dengan sengaja menghilangkan nyawa orang lain, diancam pidana mati,", size=FS_TINY)
    svg.mono(30, 298, "pidana penjara seumur hidup atau pidana penjara paling singkat sepuluh tahun...", size=FS_TINY)

    # Augmented prompt
    svg.rect(440, 235, 420, 90, fill='code_bg', stroke='dark', rx=4)
    svg.text(650, 253, "Prompt Teriaugmentasi", size=FS_SMALL, bold=True)
    svg.mono(450, 278, "Jawab pertanyaan berdasarkan ketentuan hukum berikut:", size=FS_TINY)
    svg.mono(450, 298, "[Pasal 232 KUHP...] T: Apa hukuman untuk pembunuhan disengaja?", size=FS_TINY)

    # Generated answer
    svg.rect(20, 345, 840, 80, fill='light', stroke='border')
    svg.text(w / 2, 363, "Respons yang dibangkitkan", size=FS_SMALL, bold=True)
    svg.mono(30, 390, "Menurut Pasal 232 KUHP, tindak pidana pembunuhan disengaja dapat dihukum mati, penjara seumur hidup, atau penjara paling singkat sepuluh tahun;", size=FS_TINY)
    svg.mono(30, 412, "jika keadaannya ringan, hukumannya adalah penjara paling singkat tiga tahun dan paling lama sepuluh tahun.", size=FS_TINY)

    svg.save(os.path.join(OUT, 'fig3-2.svg'))


# ──────────────────────── fig3-3 ────────────────────────

def fig3_3():
    """Evolusi teknik embedding padat"""
    w, h = 860, 340
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Evolusi teknik embedding padat", size=FS_TITLE, bold=True)

    items = [
        ("Word2Vec", "2013", "300D\nVektor kata statis", "Kehadiran bersama\nPelatihan prediktif"),
        ("GloVe", "2014", "300D\nStatistik global", "Faktorisasi matriks\n+ Kehadiran bersama"),
        ("BERT", "2018", "768D\nSadar konteks", "Transformer\nPra-pelatihan MLM"),
        ("Sentence-BERT", "2019", "768D\nEmbedding tingkat kalimat", "Jaringan Siamese\nPembelajaran kontrastif"),
        ("BGE-M3", "2024", "1024D\nTeks panjang multibahasa", "Multi-tahap\nPelatihan hibrida"),
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
             "Vektor kata statis (satu vektor per kata)", size=FS_SMALL, fill='text_light')
    svg.text(pad_l + gap * 3.5, h - 18,
             "Embedding sadar konteks (banyak vektor per kata)", size=FS_SMALL, fill='text_light')

    svg.line(pad_l + gap * 1.5, 75, pad_l + gap * 1.5, h - 35, color='dark', dash=True)

    svg.save(os.path.join(OUT, 'fig3-3.svg'))


# ──────────────────────── fig3-4 ────────────────────────

def fig3_4():
    """Struktur indeks HNSW"""
    w, h = 750, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Struktur indeks HNSW", size=FS_TITLE, bold=True)

    layers = [
        ("Lapisan 2 (jarang · koneksi jarak jauh)", 70, 3),
        ("Lapisan 1 (kepadatan menengah)", 185, 6),
        ("Lapisan 0 (padat · semua simpul)", 300, 10),
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
    svg.text(w / 2 + 80, 148, "Pencarian dimulai dari tingkat atas", size=FS_SMALL, fill='text_light')
    svg.arrow(w / 2 - 50, 245, w / 2 - 80, 280, color='border')
    svg.text(w / 2 + 60, 263, "Perhalus lapisan demi lapisan ke bawah", size=FS_SMALL, fill='text_light')

    # Key properties
    svg.rect(50, h - 45, 300, 32, fill='light')
    svg.text(200, h - 29, "Mendukung pembaruan inkremental · Recall tinggi", size=FS_SMALL, bold=True)
    svg.rect(400, h - 45, 300, 32, fill='code_bg', stroke='dark', rx=4)
    svg.text(550, h - 29, "Kompleksitas kueri O(log N)", size=FS_SMALL)

    svg.save(os.path.join(OUT, 'fig3-4.svg'))


# ──────────────────────── fig3-5 ────────────────────────

def fig3_5():
    """Mekanisme penilaian BM25"""
    w, h = 800, 380
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Mekanisme penilaian BM25", size=FS_TITLE, bold=True)

    # Formula
    svg.rect(40, 50, w - 80, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(60, 75,
             "Skor(Q,D) = Σ IDF(qi) × TF(qi,D)×(k1+1) / (TF + k1×(1-b+b×|D|/avgdl))",
             size=FS_SMALL)

    # Three components
    boxes = [
        ("Saturasi frekuensi istilah (TF)", 40, 'light', [
            "k₁ mengontrol kecepatan saturasi",
            "TF ↑ tetapi kontribusi menurun",
            "Contoh: kemunculan 5→10",
            "Skor hanya meningkat ~20%",
        ]),
        ("Frekuensi dokumen invers (IDF)", 290, 'light', [
            "Mengukur kelangkaan kata",
            "\"di\" → IDF ≈ 0",
            "\"hukuman\" → IDF ≈ 5.2",
            "Bobot kata langka >> kata umum",
        ]),
        ("Normalisasi panjang (b)", 540, 'light', [
            "Kekuatan normalisasi b ∈ [0,1]",
            "b=0: abaikan panjang",
            "b=1: normalisasi penuh",
            "Hindari bias terhadap dokumen panjang",
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
    svg.text(w / 2, 339, "Skor akhir = Σ (Saturasi TF × pembobotan IDF × normalisasi panjang)", size=FS_BODY, bold=True)

    svg.save(os.path.join(OUT, 'fig3-5.svg'))


# ──────────────────────── fig3-6 ────────────────────────

def fig3_6():
    """Hybrid retrieval and re-ranking pipeline (with score examples)"""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Alur kerja pengambilan hibrida dan pemeringkatan ulang", size=FS_TITLE, bold=True)

    # Query
    svg.rect(30, 55, 160, 50, fill='medium')
    svg.text(110, 73, "Kueri pengguna", size=FS_BODY, bold=True)
    svg.mono(110, 93, '"perilaku kitty"', size=FS_TINY, anchor='middle')

    # Dense retrieval
    svg.arrow(190, 68, 238, 68)
    svg.box(240, 50, 180, 50, "Pengambilan padat", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 118, "Pencocokan semantik: kitty ≈ cat", size=FS_SMALL, fill='text_light')

    dense_results = [
        ("dok3: \"kebiasaan felines dan permainan kucing...\"", "cos=0.87"),
        ("dok7: \"pola dandan kucing...\"", "cos=0.82"),
        ("dok1: \"dasar perawatan hewan peliharaan...\"", "cos=0.71"),
    ]
    for i, (doc, score) in enumerate(dense_results):
        y = 140 + i * 32
        svg.mono(250, y, doc, size=FS_TINY)
        svg.text(700, y, score, size=FS_TINY, fill='text_light', anchor='start')

    # Sparse retrieval
    svg.arrow(190, 90, 238, 270)
    svg.box(240, 250, 180, 50, "Pengambilan jarang (BM25)", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 318, "Pencocokan persis: kata kunci \"kitty\"", size=FS_SMALL, fill='text_light')

    sparse_results = [
        ("dok5: \"pelatihan kotak kotoran kitty...\"", "BM25=8.4"),
        ("dok9: \"panduan adopsi kitty...\"", "BM25=6.1"),
        ("dok2: \"tips kesehatan anak kucing...\"", "BM25=3.2"),
    ]
    for i, (doc, score) in enumerate(sparse_results):
        y = 340 + i * 32
        svg.mono(250, y, doc, size=FS_TINY)
        svg.text(700, y, score, size=FS_TINY, fill='text_light', anchor='start')

    # Merge + rerank
    svg.arrow(770, 180, 808, 220)
    svg.arrow(770, 370, 808, 330)

    svg.rect(790, 215, 70, 120, fill='medium')
    svg.text(825, 250, "Gabung", size=FS_BODY, bold=True)
    svg.text(825, 275, "Deduplikasi", size=FS_BODY, bold=True)
    svg.text(825, 300, "6→5", size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-6.svg'))


# ──────────────────────── fig3-7 ────────────────────────

def fig3_7():
    """RAPTOR tree structure"""
    w, h = 800, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Indeks hierarkis pohon RAPTOR", size=FS_TITLE, bold=True)

    # Root
    svg.box(300, 55, 200, 50, "Ringkasan global", fill='dark', bold=True, font_size=FS_BODY)
    svg.text(300 + 200 + 15, 80, "← Simpul akar", size=FS_SMALL, fill='text_light', anchor='start')

    # Mid-level
    mid_nodes = [("Ringkasan klaster A", 80), ("Ringkasan klaster B", 320), ("Ringkasan klaster C", 560)]
    for label, x in mid_nodes:
        svg.box(x, 150, 160, 48, label, fill='medium', font_size=FS_BODY)
    svg.line(400, 105, 160, 150, color='border')
    svg.line(400, 105, 400, 150, color='border')
    svg.line(400, 105, 640, 150, color='border')
    svg.text(35, 230, "Lapisan tengah ↑", size=FS_SMALL, fill='text_light', anchor='start')

    # Leaf nodes — 7 boxes evenly distributed, narrower to avoid overlap
    chunks = [
        [(40, "Kepingan teks 1"), (140, "Kepingan teks 2"), (240, "Kepingan teks 3")],   # Cluster A → cluster center ~160
        [(360, "Kepingan teks 4"), (460, "Kepingan teks 5")],                    # Cluster B → cluster center ~410
        [(560, "Kepingan teks 6"), (660, "Kepingan teks 7")],                    # Cluster C → cluster center ~640
    ]
    leaf_w = 88
    mid_cxs = [160, 400, 640]
    for gi, group in enumerate(chunks):
        for cx, label in group:
            svg.box(cx, 250, leaf_w, 40, label, fill='light', font_size=FS_SMALL)
            svg.line(cx + leaf_w / 2, 250, mid_cxs[gi], 198, color='dark')
    svg.text(35, 295, "Lapisan daun ↑", size=FS_SMALL, fill='text_light', anchor='start')

    # Original document
    svg.rect(40, 320, 720, 55, fill='white', stroke='dark', dash=True)
    svg.text(400, 340, "Dokumen asli", size=FS_BODY, fill='text_light')
    for bx in range(60, 720, 110):
        svg.rect(bx, 350, 90, 16, fill='light')

    # Bottom label
    svg.text(w / 2, h - 20, "Abstraksi rekursif bottom-up: detail → topik → gambaran global", size=FS_BODY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-7.svg'))


# ──────────────────────── fig3-8 ────────────────────────

def fig3_8():
    """GraphRAG relational network"""
    w, h = 750, 430
    svg = SVG(w, h)
    svg.text(w / 2, 28, "Grafik pengetahuan relasi-entitas GraphRAG", size=FS_TITLE, bold=True)

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
    svg.text(200, 395, "Komunitas: Set instruksi SSE", size=FS_SMALL, fill='text_light')

    for label, x, y, fill in nodes:
        svg.circle(x, y, node_r, fill=fill, label=label, font_size=FS_SMALL)

    edges = [
        (0, 1, "Pengembangan"), (0, 2, "Pengembangan"),
        (1, 3, "Penggunaan"), (1, 6, ""), (1, 4, "Berisi"),
        (2, 5, "Penggunaan"), (2, 6, "Eksekusi"),
        (6, 3, ""), (6, 5, "Operasi"),
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
    svg.text(lx + col_w / 2, 73, "RAG Non-Agentic", size=FS_BODY, bold=True)

    steps_l = [
        ("Kueri: \"Bagaimana hukuman untuk menyebabkan cedera serius karena kelalaian saat mabuk \ndan dengan riwayat hukuman pencurian?\"", 'light'),
        ("Pengambilan tunggal:\n\"Hukuman karena menyebabkan cedera serius oleh kelalaian\"", 'light'),
        ("Hasil pengambilan: Hanya menemukan ketentuan dasar untuk cedera kelalaian\n (konteks tidak lengkap)", 'code_bg'),
        ("Pembangkitan langsung: Hilang faktor pengaruh \"mabuk\"\ndan \"riwayat hukuman\"", 'light'),
    ]
    prev_y = 95
    for i, (s, fill) in enumerate(steps_l):
        y = 110 + i * 108
        svg.box(lx + 30, y, 340, 80, s, fill=fill, font_size=FS_SMALL)
        if i > 0:
            svg.arrow(lx + 200, prev_y + 80 + 2, lx + 200, y - 2)
        prev_y = y

    svg.text(lx + col_w / 2, h - 15, "Lewatan tunggal · Informasi tidak lengkap", size=FS_BODY, fill='text_light')

    # --- Separator ---
    svg.line(440, 50, 440, h - 5, color='dark', dash=True)

    # --- Right: Agentic ---
    svg.rect(rx, 50, col_w, 45, fill='medium')
    svg.text(rx + col_w / 2, 73, "RAG Agentic (ReAct)", size=FS_BODY, bold=True)

    steps_r = [
        ("Pikiran: Perlu menguraikan menjadi 3 sub-pertanyaan", 'light'),
        ("Pencarian ①: \"Hukuman untuk menyebabkan cedera serius oleh kelalaian\"\nPencarian ②: \"Kewajiban pidana untuk mabuk\"\nPencarian ③: \"Dampak riwayat hukuman pencurian\"", 'code_bg'),
        ("Observasi: Menemukan ketentuan dasar tetapi\nhilang kaitan antara \"riwayat hukuman\" dan \"cedera kelalaian\"", 'light'),
        ("Pencarian ④: \"Residivisme kejahatan berbeda\ninterpretasi yudisial\"", 'code_bg'),
        ("Sintesis: Jawaban lengkap mencakup semua\nketentuan hukum dan analisis hukuman", 'medium'),
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
    svg.text(loop_x + 4, (ys[1] + ys[2]) / 2 + 34, "Iterasi", size=FS_SMALL, fill='text_light',
             anchor='start')

    svg.text(rx + col_w / 2, h - 15, "Iterasi multi-putaran · Informasi lengkap", size=FS_BODY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-9.svg'))


# ──────────────────────── fig3-10 ────────────────────────

def fig3_10():
    """Agentic RAG System Architecture (Experiment 3.6)"""
    w, h = 880, 500
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Eksperimen 3.6: Arsitektur Sistem RAG Agentic", size=FS_TITLE, bold=True)

    # Agent core
    svg.rect(220, 55, 440, 200, fill='white', stroke='border')
    svg.text(440, 78, "Agen (Putaran ReAct)", size=FS_BODY, bold=True)

    # ReAct steps inside agent
    react_items = [
        ("① Pikiran", 240, 100, 180, 45, 'light'),
        ("② Tindakan", 460, 100, 180, 45, 'medium'),
        ("③ Observasi", 350, 180, 180, 45, 'light'),
    ]
    for label, bx, by, bw, bh, fill in react_items:
        svg.box(bx, by, bw, bh, label, fill=fill, font_size=FS_SMALL, bold=True)

    svg.arrow(420, 122, 458, 122)
    svg.arrow(640, 130, 530, 178, color='border')
    svg.arrow(350, 202, 280, 145, color='border')

    # Loop label
    svg.text(360, 165, "Ulangi hingga informasi cukup", size=FS_TINY, fill='text_light')

    # User
    svg.box(20, 95, 160, 55, "Kueri pengguna", fill='medium', bold=True, font_size=FS_BODY)
    svg.arrow(180, 122, 218, 122)

    # Final answer
    svg.box(700, 95, 160, 55, "Jawaban akhir", fill='medium', bold=True, font_size=FS_BODY)
    svg.arrow(660, 122, 698, 122)

    # Tool layer
    svg.rect(100, 290, 680, 85, fill='white', stroke='border', dash=True)
    svg.text(440, 312, "Lapisan alat", size=FS_BODY, bold=True)
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
    svg.text(440, 420, "Backend basis pengetahuan (dapat dialihkan)", size=FS_BODY, bold=True)
    backends = [
        ("retrieval-pipeline\nPengambilan hibrida", 120),
        ("structured-index\nRAPTOR/GraphRAG", 340),
        ("contextual-retrieval\nSadar konteks", 560),
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
    svg.text(w / 2, 30, "Pengambilan sadar konteks", size=FS_TITLE, bold=True)

    # Left: Traditional chunking
    svg.rect(20, 55, 400, 170, fill='white', stroke='border')
    svg.text(220, 78, "Pemotongan tradisional (tanpa konteks)", size=FS_BODY, bold=True)

    svg.rect(40, 95, 360, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(50, 112, "Pendapatan perusahaan pada kuartal kedua tumbuh sebesar 3%,", size=FS_TINY)
    svg.mono(50, 132, "terutama didorong oleh lini produk baru.", size=FS_TINY)

    svg.text(220, 170, "Pertanyaan: \"Siapa \"perusahaan\" tersebut? Tahun berapa?", size=FS_SMALL, fill='text_light')
    svg.text(220, 195, "→ Pengambilan mencocokkan data pendapatan dari banyak perusahaan yang tidak relevan", size=FS_SMALL, fill='text_light')

    # Right: Contextual
    svg.rect(460, 55, 400, 170, fill='white', stroke='border')
    svg.text(660, 78, "Pemotongan sadar konteks", size=FS_BODY, bold=True)

    svg.rect(480, 95, 360, 35, fill='medium')
    svg.mono(490, 113, "[Laporan Laba ACME Company 2025 Q2 · Indikator Kinerja Utama]", size=FS_TINY)

    svg.rect(480, 130, 360, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(490, 148, "Pendapatan perusahaan pada kuartal kedua tumbuh sebesar 3%,", size=FS_TINY)
    svg.mono(490, 168, "terutama didorong oleh lini produk baru.", size=FS_TINY)

    svg.text(660, 200, "→ Pencocokan persis ACME + Q2 + pertumbuhan pendapatan", size=FS_SMALL, fill='text_light')

    # Arrow between
    svg.text(440, 140, "→", size=FS_TITLE, bold=True)

    # Process flow
    svg.line(20, 250, 860, 250, color='dark', dash=True)
    svg.text(w / 2, 275, "Tahap pengindeksan: LLM menghasilkan prefiks konteks", size=FS_BODY, bold=True)

    flow_y = 300
    svg.box(30, flow_y, 180, 55, "Dokumen asli", fill='light', bold=True, font_size=FS_BODY)
    svg.arrow(210, flow_y + 27, 248, flow_y + 27)

    svg.box(250, flow_y, 180, 55, "Pemotongan", fill='light', bold=True, font_size=FS_BODY)
    svg.arrow(430, flow_y + 27, 468, flow_y + 27)

    svg.box(470, flow_y, 180, 55, "LLM menghasilkan prefiks\n(caching prompt)", fill='medium',
            font_size=FS_SMALL, bold=True)
    svg.arrow(650, flow_y + 27, 688, flow_y + 27)

    svg.box(690, flow_y, 170, 55, "Prefiks + teks asli\n→ Indeks", fill='light', font_size=FS_SMALL, bold=True)

    # Stats
    svg.text(w / 2, h - 20,
             "Efek: Tingkat kegagalan pengambilan ↓49% (+BM25), ↓67% (+reranking) — data Anthropic",
             size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-11.svg'))


# ──────────────────────── fig3-12 ────────────────────────

def fig3_12():
    """Structured knowledge extraction pipeline (Experiment 3.10)"""
    w, h = 880, 510
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Eksperimen 3.10: Ekstraksi pengetahuan terstruktur (preseden yudisial)", size=FS_TITLE, bold=True)

    # Phase 1 header
    svg.rect(20, 55, 840, 200, fill='white', stroke='border')
    svg.text(440, 78, "Fase 1: Ekstraksi dan penstrukturan pengetahuan", size=FS_BODY, bold=True)

    # Raw cases
    svg.rect(40, 95, 180, 65, fill='code_bg', stroke='dark', rx=4)
    svg.text(130, 113, "Dokumen putusan asli", size=FS_SMALL, bold=True)
    svg.mono(50, 138, "Dataset CAIL2018", size=FS_TINY)

    svg.arrow(220, 127, 258, 127)

    # LLM extraction
    svg.rect(260, 95, 180, 65, fill='medium')
    svg.text(350, 113, "Penemuan faktor LLM", size=FS_SMALL, bold=True)
    svg.text(350, 138, "Skema Bottom-up", size=FS_SMALL, fill='text_light')

    svg.arrow(440, 127, 478, 127)

    # Structured JSON
    svg.rect(480, 95, 200, 65, fill='code_bg', stroke='dark', rx=4)
    svg.text(580, 113, "JSON Terstruktur", size=FS_SMALL, bold=True)
    svg.mono(490, 138, "{voluntary_surrender:true, compensation:500000,", size=FS_TINY)
    svg.mono(490, 155, " injury_level:severe_second_degree}", size=FS_TINY)

    # Schema detail
    svg.rect(40, 170, 400, 70, fill='light')
    svg.text(240, 188, "Skema data modular", size=FS_SMALL, bold=True)
    svg.text(240, 212, "Skema inti (menyerahkan diri/kompensasi/catatan kriminal) + skema ekstensi dakwaan", size=FS_SMALL, fill='text_light')
    svg.text(240, 232, "(pencurian→jumlah yang terlibat, cedera→tingkat cedera)", size=FS_SMALL, fill='text_light')

    # Phase 2 header
    svg.rect(20, 270, 840, 200, fill='white', stroke='border')
    svg.text(440, 293, "Fase 2: Analisis faktor dan pemodelan pengetahuan", size=FS_BODY, bold=True)

    # Vectorization
    svg.rect(40, 310, 200, 65, fill='light')
    svg.text(140, 328, "Vektorisasi fitur", size=FS_SMALL, bold=True)
    svg.text(140, 350, "Pengkodean one-hot + pengkodean multi-hot", size=FS_SMALL, fill='text_light')
    svg.text(140, 370, "+ transformasi log + standardisasi", size=FS_SMALL, fill='text_light')

    svg.arrow(240, 342, 278, 342)

    # Clustering
    svg.rect(280, 310, 200, 65, fill='medium')
    svg.text(380, 328, "Pengklasteran HDBSCAN", size=FS_SMALL, bold=True)
    svg.text(380, 350, "temukan \"prototipe kasus\"", size=FS_SMALL, fill='text_light')
    svg.text(380, 370, "misal., pertengkaran kecil → cedera ringan", size=FS_SMALL, fill='text_light')

    svg.arrow(480, 342, 518, 342)

    # Factor importance
    svg.rect(520, 310, 200, 65, fill='light')
    svg.text(620, 328, "model kepentingan faktor", size=FS_SMALL, bold=True)
    svg.text(620, 350, "kuantifikasi bobot setiap faktor", size=FS_SMALL, fill='text_light')
    svg.text(620, 370, "bangun logika keputusan hukuman", size=FS_SMALL, fill='text_light')

    # Application
    svg.arrow(620, 375, 620, 400)
    svg.rect(40, 400, 720, 60, fill='light')
    svg.text(400, 420, "Aplikasi: Agen nasihat hukum percakapan", size=FS_BODY, bold=True)
    svg.text(400, 445, "pandu pertanyaan dengan kepentingan faktor → ambil prototipe kasus serupa → analisis hukuman berbasis data",
             size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-12.svg'))


# ──────────────────────── fig3-13 ────────────────────────

def fig3_13():
    """Externalized learning loop (concrete example)"""
    w, h = 880, 490
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Pembelajaran eksternal: putaran tertutup dari pengalaman menuju kemampuan", size=FS_TITLE, bold=True)

    # Central Agent
    cx, cy = 440, 210
    svg.circle(cx, cy, 55, fill='medium', label="Agent", font_size=FS_BODY)

    # 5 steps around the loop
    steps = [
        ("① Eksekusi tugas", 120, 100, "proses permintaan pengembalian dana\npanggil API layanan pelanggan"),
        ("② Dapatkan umpan balik", 680, 100, "berhasil mengembalikan dana $45\nditemukan kebutuhan untuk verifikasi empat digit terakhir"),
        ("③ Refleksikan dan saring", 680, 310, "LLM merangkum pengalaman:\n\"Pengembalian dana Perusahaan A memerlukan verifikasi\""),
        ("④ Simpan dalam basis pengetahuan", 340, 380, "pengalaman → indeks tervektorisasi\nproses → bangkitkan kode alat"),
        ("⑤ Pengambilan dan penggunaan kembali di masa depan", 120, 310, "tugas serupa → ambil pengalaman\ngunakan kembali strategi berhasil secara langsung"),
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
    svg.text(120, 409, "Pengetahuan: ringkasan/ringkasan pohon", size=FS_SMALL, fill='white')
    svg.rect(670, 395, 180, 28, fill='dark')
    svg.text(760, 409, "Alat: proses → kode", size=FS_SMALL, fill='white')

    svg.save(os.path.join(OUT, 'fig3-13.svg'))


# ──────────────────────── fig3-14 ────────────────────────

def fig3_14():
    """GAIA experience learning system (Experiment 3.11)"""
    w, h = 880, 510
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Eksperimen 3.11: Sistem pembelajaran pengalaman GAIA", size=FS_TITLE, bold=True)

    box_h = 60
    step_gap = 75
    base_y = 100

    # --- Left: Learning Mode ---
    lx = 20
    svg.rect(lx, 55, 400, 420, fill='white', stroke='border')
    svg.text(lx + 200, 80, "Mode Pembelajaran", size=FS_BODY, bold=True)

    learn_steps = [
        ("Tugas GAIA", 'medium', "masalah multi-langkah kompleks"),
        ("Eksekusi agen", 'light', "peramban + berkas + penerjemah kode"),
        ("Tugas berhasil?", 'light', "Evaluasi Otomatis (AWorld)"),
        ("Refleksi & Ringkasan LLM", 'medium', "Ekstrak Ringkasan Strategi"),
        ("Pengalaman → Vektorisasi", 'light', "Simpan di Basis Pengetahuan Pengalaman"),
    ]
    for i, (label, fill, sub) in enumerate(learn_steps):
        y = base_y + i * step_gap
        svg.box(lx + 50, y, 300, box_h, label, sublabel=sub, fill=fill, bold=True, font_size=FS_BODY)
        if i > 0:
            svg.arrow(lx + 200, base_y + (i - 1) * step_gap + box_h + 2, lx + 200, y - 2)

    # --- Right: Apply Mode ---
    rx = 460
    svg.rect(rx, 55, 400, 420, fill='white', stroke='border')
    svg.text(rx + 200, 80, "Mode Penerapan", size=FS_BODY, bold=True)

    apply_steps = [
        ("Tugas GAIA Baru", 'medium', "Terima Pertanyaan Baru"),
        ("Pengambilan Semantik Pengalaman", 'light', "Cari Tugas Serupa di Basis Pengalaman"),
        ("Suntikkan ke Prompt Sistem", 'medium', "Strategi Berhasil Historis sebagai Contoh"),
        ("Eksekusi agen", 'light', "Manfaatkan Pengalaman untuk Penyelesaian Masalah Lebih Efisien"),
        ("Tingkat Keberhasilan ↑ Efisiensi ↑", 'dark', "Evolusi Diri: Menjadi Lebih Kuat Seiring Waktu"),
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
    svg.text((kb_x1 + kb_x2) / 2, kb_cy - 8, "Basis Pengetahuan Pengalaman", size=FS_SMALL, fill='white', bold=True)
    svg.text((kb_x1 + kb_x2) / 2, kb_cy + 12, "(Indeks Vektor)", size=FS_TINY, fill='white')

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
