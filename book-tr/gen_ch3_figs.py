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

    svg.text(w / 2, 32, "Bölüm 3: Bilgi Tabanı ve RAG — Bilgi Haritası", size=FS_TITLE, bold=True)

    # --- Row 1: RAG foundations ---
    r1_y = 70
    svg.rect(30, r1_y, 800, 130, fill='white', stroke='border', dash=True)
    svg.text(80, r1_y + 20, "RAG Temelleri", size=FS_BODY, bold=True, anchor='start')

    boxes_r1 = [
        ("Yoğun Gömme", 50, "Word2Vec → BGE-M3"),
        ("Seyrek Gömme", 230, "TF-IDF / BM25"),
        ("Hibrit Erişim + Yeniden Sıralama", 410, "İki Kuleli Erişim + Cross-Encoder"),
        ("Çok Modlu Çıkarım", 650, "Yerel / Metin / Araç"),
    ]
    for label, bx, sub in boxes_r1:
        svg.box(bx, r1_y + 38, 160, 50, label, fill='light', bold=True, font_size=FS_SMALL)
        svg.text(bx + 80, r1_y + 38 + 50 + 18, sub, size=FS_TINY, fill='text_light')

    # --- Arrow down ---
    svg.arrow(w / 2, r1_y + 130, w / 2, r1_y + 160)

    # --- Row 2: Advanced knowledge structuring ---
    r2_y = 230
    svg.rect(30, r2_y, 800, 100, fill='white', stroke='border', dash=True)
    svg.text(80, r2_y + 20, "Mevcut Bilgiden Öğrenme", size=FS_BODY, bold=True, anchor='start')

    boxes_r2 = [
        ("RAPTOR\n Ağaç Hiyerarşik İndeks", 50),
        ("GraphRAG\n Varlık İlişki Grafiği", 230),
        ("Agentic RAG\n Araç Olarak Erişim", 410),
        ("Bağlam Duyarlı Erişim\n Önek Özet Zenginleştirme", 590),
    ]
    for label, bx in boxes_r2:
        svg.box(bx, r2_y + 35, 160, 55, label, fill='medium', font_size=FS_SMALL)

    # --- Arrow down ---
    svg.arrow(w / 2, r2_y + 100, w / 2, r2_y + 130)

    # --- Row 3: Learning from experience ---
    r3_y = 360
    svg.rect(30, r3_y, 800, 100, fill='white', stroke='border', dash=True)
    svg.text(80, r3_y + 20, "Özerk Keşiften Öğrenme", size=FS_BODY, bold=True, anchor='start')

    boxes_r3 = [
        ("Eğitim sonrası\n RL → Kas Hafızası", 100),
        ("Bağlam İçi Öğrenme\n Çıkarım Anı Yumuşak Erişim", 330),
        ("Dışsallaştırılmış Öğrenme\n Bilgi Tabanı + Araç Üretimi", 560),
    ]
    for label, bx in boxes_r3:
        svg.box(bx, r3_y + 35, 200, 55, label, fill='light', font_size=FS_SMALL)

    # --- Bottom: core insight ---
    svg.rect(180, 490, 500, 44, fill='dark')
    svg.text(w / 2, 512, "Acı Ders: Arama + Öğrenme = Genel Yöntem", size=FS_BODY, fill='white', bold=True)
    svg.arrow(w / 2, r3_y + 100, w / 2, 488)

    svg.save(os.path.join(OUT, 'fig3-1.svg'))


# ──────────────────────── fig3-2 ────────────────────────

def fig3_2():
    """RAG End-to-End Pipeline (Concrete Example)"""
    w, h = 880, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "RAG Uçtan Uca Boru Hattı", size=FS_TITLE, bold=True)

    # Step 1: User query
    svg.box(20, 65, 180, 55, "① Kullanıcı Sorgusu", fill='medium', bold=True, font_size=FS_BODY)
    q_lines = ['"Kasten adam öldürmenin cezası kaç yıl?"']
    svg.text(110, 145, q_lines[0], size=FS_SMALL, fill='text_light')

    svg.arrow(200, 92, 238, 92)

    # Step 2: Retrieval
    svg.box(240, 65, 180, 55, "② Erişim", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 140, "Yoğun Erişim + BM25", size=FS_SMALL, fill='text_light')
    svg.text(330, 160, "→ En İyi K Metin Parçası", size=FS_SMALL, fill='text_light')

    svg.arrow(420, 92, 458, 92)

    # Step 3: Augmentation
    svg.box(460, 65, 180, 55, "③ Zenginleştirme", fill='light', bold=True, font_size=FS_BODY)
    svg.text(550, 140, "Sorgu + Erişilen Sonuçlar", size=FS_SMALL, fill='text_light')
    svg.text(550, 160, "→ Tam İstemi Oluştur", size=FS_SMALL, fill='text_light')

    svg.arrow(640, 92, 678, 92)

    # Step 4: Generation
    svg.box(680, 65, 180, 55, "④ Üretim", fill='medium', bold=True, font_size=FS_BODY)
    svg.text(770, 140, "LLM bağlamı sentezler", size=FS_SMALL, fill='text_light')
    svg.text(770, 160, "→ Yanıt üret", size=FS_SMALL, fill='text_light')

    # Concrete data flow example
    svg.line(20, 195, 860, 195, color='dark', dash=True)
    svg.text(w / 2, 215, "Örnek veri akışı", size=FS_BODY, bold=True)

    # Retrieved chunks
    svg.rect(20, 235, 400, 90, fill='code_bg', stroke='dark', rx=4)
    svg.text(220, 253, "Erişilen metin parçaları", size=FS_SMALL, bold=True)
    svg.mono(30, 278, "Ceza Kanunu Madde 232: Kasten başkasını öldüren kişi ölüm cezası,", size=FS_TINY)
    svg.mono(30, 298, "ömür boyu hapis veya on yıldan az olmamak üzere hapis cezasına çarptırılır...", size=FS_TINY)

    # Augmented prompt
    svg.rect(440, 235, 420, 90, fill='code_bg', stroke='dark', rx=4)
    svg.text(650, 253, "Zenginleştirilmiş İstem", size=FS_SMALL, bold=True)
    svg.mono(450, 278, "Aşağıdaki yasal hükümlere göre soruyu yanıtla:", size=FS_TINY)
    svg.mono(450, 298, "[Ceza Kanunu Madde 232...] S: Kasten adam öldürmenin cezası nedir?", size=FS_TINY)

    # Generated answer
    svg.rect(20, 345, 840, 80, fill='light', stroke='border')
    svg.text(w / 2, 363, "Üretilen yanıt", size=FS_SMALL, bold=True)
    svg.mono(30, 390, "Ceza Kanunu Madde 232'ye göre kasten adam öldürme suçu ölüm, ömür boyu hapis veya on yıldan az olmamak üzere hapis cezasıyla cezalandırılır;", size=FS_TINY)
    svg.mono(30, 412, "hafifletici durumlarda ceza üç yıldan az on yıldan fazla olmamak üzere hapis cezasıdır.", size=FS_TINY)

    svg.save(os.path.join(OUT, 'fig3-2.svg'))


# ──────────────────────── fig3-3 ────────────────────────

def fig3_3():
    """Evolution of dense embedding techniques"""
    w, h = 860, 340
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Yoğun gömme tekniklerinin evrimi", size=FS_TITLE, bold=True)

    items = [
        ("Word2Vec", "2013", "300D\nStatik kelime vektörleri", "Birlikte geçme\nTahminsel eğitim"),
        ("GloVe", "2014", "300D\nKüresel istatistikler", "Matris ayrıştırma\n+ Birlikte geçme"),
        ("BERT", "2018", "768D\nBağlam duyarlı", "Transformer\nMLM ön eğitimi"),
        ("Sentence-BERT", "2019", "768D\nCümle düzeyi gömme", "Siyam ağı\nZıtsal öğrenme"),
        ("BGE-M3", "2024", "1024D\nÇok dilli uzun metinler", "Çok aşamalı\nHibrit eğitim"),
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
             "Statik kelime vektörleri (kelime başına bir vektör)", size=FS_SMALL, fill='text_light')
    svg.text(pad_l + gap * 3.5, h - 18,
             "Bağlam duyarlı gömmeler (kelime başına çoklu vektör)", size=FS_SMALL, fill='text_light')

    svg.line(pad_l + gap * 1.5, 75, pad_l + gap * 1.5, h - 35, color='dark', dash=True)

    svg.save(os.path.join(OUT, 'fig3-3.svg'))


# ──────────────────────── fig3-4 ────────────────────────

def fig3_4():
    """HNSW index structure"""
    w, h = 750, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "HNSW indeks yapısı", size=FS_TITLE, bold=True)

    layers = [
        ("Katman 2 (seyrek · uzun mesafe bağlantılar)", 70, 3),
        ("Katman 1 (orta yoğunluk)", 185, 6),
        ("Katman 0 (yoğun · tüm düğümler)", 300, 10),
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
    svg.text(w / 2 + 80, 148, "Arama üst katmandan başlar", size=FS_SMALL, fill='text_light')
    svg.arrow(w / 2 - 50, 245, w / 2 - 80, 280, color='border')
    svg.text(w / 2 + 60, 263, "Katman katman aşağı doğru inceltilir", size=FS_SMALL, fill='text_light')

    # Key properties
    svg.rect(50, h - 45, 300, 32, fill='light')
    svg.text(200, h - 29, "Artımlı güncellemeleri destekler · Yüksek geri çağırma", size=FS_SMALL, bold=True)
    svg.rect(400, h - 45, 300, 32, fill='code_bg', stroke='dark', rx=4)
    svg.text(550, h - 29, "O(log N) sorgu karmaşıklığı", size=FS_SMALL)

    svg.save(os.path.join(OUT, 'fig3-4.svg'))


# ──────────────────────── fig3-5 ────────────────────────

def fig3_5():
    """BM25 scoring mechanism"""
    w, h = 800, 380
    svg = SVG(w, h)
    svg.text(w / 2, 30, "BM25 puanlama mekanizması", size=FS_TITLE, bold=True)

    # Formula
    svg.rect(40, 50, w - 80, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(60, 75,
             "Score(Q,D) = Σ IDF(qi) × TF(qi,D)×(k1+1) / (TF + k1×(1-b+b×|D|/avgdl))",
             size=FS_SMALL)

    # Three components
    boxes = [
        ("Terim frekansı doygunluğu (TF)", 40, 'light', [
            "k₁ doygunluk hızını kontrol eder",
            "TF ↑ ama katkı azalır",
            "Örnek: 5→10 tekrar",
            "Skor sadece ~%20 artar",
        ]),
        ("Ters belge frekansı (IDF)", 290, 'light', [
            "Kelime nadirliğini ölçer",
            "\"the\" → IDF ≈ 0",
            "\"cezalandırma\" → IDF ≈ 5.2",
            "Nadir kelime ağırlığı >> yaygın kelime",
        ]),
        ("Uzunluk normalizasyonu (b)", 540, 'light', [
            "b ∈ [0,1] normalizasyon gücü",
            "b=0: uzunluğu yok say",
            "b=1: tam normalizasyon",
            "Uzun belgelere yanlılığı önle",
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
    svg.text(w / 2, 339, "Nihai skor = Σ (TF doygunluğu × IDF ağırlığı × uzunluk normalizasyonu)", size=FS_BODY, bold=True)

    svg.save(os.path.join(OUT, 'fig3-5.svg'))


# ──────────────────────── fig3-6 ────────────────────────

def fig3_6():
    """Hybrid retrieval and re-ranking pipeline (with score examples)"""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Hibrit erişim ve yeniden sıralama boru hattı", size=FS_TITLE, bold=True)

    # Query
    svg.rect(30, 55, 160, 50, fill='medium')
    svg.text(110, 73, "Kullanıcı sorgusu", size=FS_BODY, bold=True)
    svg.mono(110, 93, '"kedicik davranışı"', size=FS_TINY, anchor='middle')

    # Dense retrieval
    svg.arrow(190, 68, 238, 68)
    svg.box(240, 50, 180, 50, "Yoğun erişim", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 118, "Anlamsal eşleşme: kedicik ≈ kedi", size=FS_SMALL, fill='text_light')

    dense_results = [
        ("doc3: \"kedigil alışkanlıklar ve kedi oyunu...\"", "cos=0.87"),
        ("doc7: \"kedi tımarlama örüntüleri...\"", "cos=0.82"),
        ("doc1: \"evcil hayvan bakım temelleri...\"", "cos=0.71"),
    ]
    for i, (doc, score) in enumerate(dense_results):
        y = 140 + i * 32
        svg.mono(250, y, doc, size=FS_TINY)
        svg.text(700, y, score, size=FS_TINY, fill='text_light', anchor='start')

    # Sparse retrieval
    svg.arrow(190, 90, 238, 270)
    svg.box(240, 250, 180, 50, "Seyrek erişim (BM25)", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 318, "Tam eşleşme: \"kedicik\" anahtar kelimesi", size=FS_SMALL, fill='text_light')

    sparse_results = [
        ("doc5: \"kedicik kum eğitimi...\"", "BM25=8.4"),
        ("doc9: \"kedicik sahiplenme rehberi...\"", "BM25=6.1"),
        ("doc2: \"yavru kedi sağlık ipuçları...\"", "BM25=3.2"),
    ]
    for i, (doc, score) in enumerate(sparse_results):
        y = 340 + i * 32
        svg.mono(250, y, doc, size=FS_TINY)
        svg.text(700, y, score, size=FS_TINY, fill='text_light', anchor='start')

    # Merge + rerank
    svg.arrow(770, 180, 808, 220)
    svg.arrow(770, 370, 808, 330)

    svg.rect(790, 215, 70, 120, fill='medium')
    svg.text(825, 250, "Birleştir", size=FS_BODY, bold=True)
    svg.text(825, 275, "Tekilleştir", size=FS_BODY, bold=True)
    svg.text(825, 300, "6→5", size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-6.svg'))


# ──────────────────────── fig3-7 ────────────────────────

def fig3_7():
    """RAPTOR tree structure"""
    w, h = 800, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "RAPTOR ağaç hiyerarşik indeksi", size=FS_TITLE, bold=True)

    # Root
    svg.box(300, 55, 200, 50, "Genel özet", fill='dark', bold=True, font_size=FS_BODY)
    svg.text(300 + 200 + 15, 80, "← Kök düğüm", size=FS_SMALL, fill='text_light', anchor='start')

    # Mid-level
    mid_nodes = [("Küme özeti A", 80), ("Küme özeti B", 320), ("Küme özeti C", 560)]
    for label, x in mid_nodes:
        svg.box(x, 150, 160, 48, label, fill='medium', font_size=FS_BODY)
    svg.line(400, 105, 160, 150, color='border')
    svg.line(400, 105, 400, 150, color='border')
    svg.line(400, 105, 640, 150, color='border')
    svg.text(35, 230, "Orta katman ↑", size=FS_SMALL, fill='text_light', anchor='start')

    # Leaf nodes — 7 boxes evenly distributed, narrower to avoid overlap
    chunks = [
        [(40, "Metin parçası 1"), (140, "Metin parçası 2"), (240, "Metin parçası 3")],   # Cluster A → cluster center ~160
        [(360, "Metin parçası 4"), (460, "Metin parçası 5")],                    # Cluster B → cluster center ~410
        [(560, "Metin parçası 6"), (660, "Metin parçası 7")],                    # Cluster C → cluster center ~640
    ]
    leaf_w = 88
    mid_cxs = [160, 400, 640]
    for gi, group in enumerate(chunks):
        for cx, label in group:
            svg.box(cx, 250, leaf_w, 40, label, fill='light', font_size=FS_SMALL)
            svg.line(cx + leaf_w / 2, 250, mid_cxs[gi], 198, color='dark')
    svg.text(35, 295, "Yaprak katmanı ↑", size=FS_SMALL, fill='text_light', anchor='start')

    # Original document
    svg.rect(40, 320, 720, 55, fill='white', stroke='dark', dash=True)
    svg.text(400, 340, "Orijinal belge", size=FS_BODY, fill='text_light')
    for bx in range(60, 720, 110):
        svg.rect(bx, 350, 90, 16, fill='light')

    # Bottom label
    svg.text(w / 2, h - 20, "Aşağıdan yukarı özyinelemeli soyutlama: ayrıntılar → konular → genel bakış", size=FS_BODY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-7.svg'))


# ──────────────────────── fig3-8 ────────────────────────

def fig3_8():
    """GraphRAG relational network"""
    w, h = 750, 430
    svg = SVG(w, h)
    svg.text(w / 2, 28, "GraphRAG varlık-ilişki bilgi grafiği", size=FS_TITLE, bold=True)

    nodes = [
        ("Intel", 375, 100, 'medium'),
        ("SSE", 150, 190, 'light'),
        ("AVX", 550, 190, 'light'),
        ("XMM kaydı", 100, 320, 'light'),
        ("ADDPS", 280, 340, 'light'),
        ("YMM kaydı", 520, 320, 'light'),
        ("FP işlemleri", 375, 250, 'light'),
    ]
    node_r = 42

    # Community box (drawn first, as background layer, to avoid covering subsequent nodes and edges)
    svg.rect(50, 275, 300, 110, fill='none', stroke='border', dash=True)
    svg.text(200, 395, "Topluluk: SSE komut kümesi", size=FS_SMALL, fill='text_light')

    for label, x, y, fill in nodes:
        svg.circle(x, y, node_r, fill=fill, label=label, font_size=FS_SMALL)

    edges = [
        (0, 1, "Geliştirme"), (0, 2, "Geliştirme"),
        (1, 3, "Kullanım"), (1, 6, ""), (1, 4, "İçerir"),
        (2, 5, "Kullanım"), (2, 6, "Yürütme"),
        (6, 3, ""), (6, 5, "İşlem"),
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
    svg.text(lx + col_w / 2, 73, "Ajan Olmayan RAG", size=FS_BODY, bold=True)

    steps_l = [
        ("Sorgu: \"Alkollüyken ihmalle ağır yaralamanın cezası, \nsanığın daha önce hırsızlık sabıkası varsa?\"", 'light'),
        ("Tek erişim:\n\"İhmalle ağır yaralamanın cezalandırılması\"", 'light'),
        ("Erişim sonucu: Sadece ihmalle yaralama için\ntemel hükümler bulundu (eksik bağlam)", 'code_bg'),
        ("Doğrudan üretim: \"Alkollü\" ve\n\"önceki sabıka\" etkileyen faktörler eksik", 'light'),
    ]
    prev_y = 95
    for i, (s, fill) in enumerate(steps_l):
        y = 110 + i * 108
        svg.box(lx + 30, y, 340, 80, s, fill=fill, font_size=FS_SMALL)
        if i > 0:
            svg.arrow(lx + 200, prev_y + 80 + 2, lx + 200, y - 2)
        prev_y = y

    svg.text(lx + col_w / 2, h - 15, "Tek geçiş · Eksik bilgi", size=FS_BODY, fill='text_light')

    # --- Separator ---
    svg.line(440, 50, 440, h - 5, color='dark', dash=True)

    # --- Right: Agentic ---
    svg.rect(rx, 50, col_w, 45, fill='medium')
    svg.text(rx + col_w / 2, 73, "Agentic RAG (ReAct)", size=FS_BODY, bold=True)

    steps_r = [
        ("Düşünce: 3 alt soruya ayrıştırmak gerekiyor", 'light'),
        ("Arama ①: \"İhmalle ağır yaralamanın cezalandırılması\"\nArama ②: \"Alkollülük halinde cezai sorumluluk\"\nArama ③: \"Önceki hırsızlık sabıkasının etkisi\"", 'code_bg'),
        ("Gözlem: Temel hükümler bulundu ancak\n\"önceki sabıka\" ile \"ihmalle yaralama\" arası bağlantı eksik", 'light'),
        ("Arama ④: \"Farklı suç türlerinde tekerrür\nyargısal yorum\"", 'code_bg'),
        ("Sentez: Tüm yasal hükümleri ve ceza\nanalizini içeren tam yanıt", 'medium'),
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
    svg.text(loop_x + 4, (ys[1] + ys[2]) / 2 + 34, "Yineleme", size=FS_SMALL, fill='text_light',
             anchor='start')

    svg.text(rx + col_w / 2, h - 15, "Çok turlu yineleme · Eksiksiz bilgi", size=FS_BODY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-9.svg'))


# ──────────────────────── fig3-10 ────────────────────────

def fig3_10():
    """Agentic RAG System Architecture (Experiment 3.6)"""
    w, h = 880, 500
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Deney 3.6: Agentic RAG Sistem Mimarisi", size=FS_TITLE, bold=True)

    # Agent core
    svg.rect(220, 55, 440, 200, fill='white', stroke='border')
    svg.text(440, 78, "Ajan (ReAct Döngüsü)", size=FS_BODY, bold=True)

    # ReAct steps inside agent
    react_items = [
        ("① Düşünce", 240, 100, 180, 45, 'light'),
        ("② Eylem", 460, 100, 180, 45, 'medium'),
        ("③ Gözlem", 350, 180, 180, 45, 'light'),
    ]
    for label, bx, by, bw, bh, fill in react_items:
        svg.box(bx, by, bw, bh, label, fill=fill, font_size=FS_SMALL, bold=True)

    svg.arrow(420, 122, 458, 122)
    svg.arrow(640, 130, 530, 178, color='border')
    svg.arrow(350, 202, 280, 145, color='border')

    # Loop label
    svg.text(360, 165, "Bilgi yeterli olana kadar döngü", size=FS_TINY, fill='text_light')

    # User
    svg.box(20, 95, 160, 55, "Kullanıcı sorgusu", fill='medium', bold=True, font_size=FS_BODY)
    svg.arrow(180, 122, 218, 122)

    # Final answer
    svg.box(700, 95, 160, 55, "Nihai yanıt", fill='medium', bold=True, font_size=FS_BODY)
    svg.arrow(660, 122, 698, 122)

    # Tool layer
    svg.rect(100, 290, 680, 85, fill='white', stroke='border', dash=True)
    svg.text(440, 312, "Araç katmanı", size=FS_BODY, bold=True)
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
    svg.text(440, 420, "Bilgi tabanı arka ucu (değiştirilebilir)", size=FS_BODY, bold=True)
    backends = [
        ("retrieval-pipeline\nHibrit erişim", 120),
        ("structured-index\nRAPTOR/GraphRAG", 340),
        ("contextual-retrieval\nBağlam duyarlı", 560),
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
    svg.text(w / 2, 30, "Bağlam duyarlı erişim", size=FS_TITLE, bold=True)

    # Left: Traditional chunking
    svg.rect(20, 55, 400, 170, fill='white', stroke='border')
    svg.text(220, 78, "Geleneksel parçalama (bağlamsız)", size=FS_BODY, bold=True)

    svg.rect(40, 95, 360, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(50, 112, "Şirketin ikinci çeyrek geliri %3 arttı,", size=FS_TINY)
    svg.mono(50, 132, "esas olarak yeni ürün hatlarının katkısıyla.", size=FS_TINY)

    svg.text(220, 170, "Soru: \"Şirket\" kim? Hangi yıl?", size=FS_SMALL, fill='text_light')
    svg.text(220, 195, "→ Erişim, ilgisiz birçok şirketin gelir verisiyle eşleşir", size=FS_SMALL, fill='text_light')

    # Right: Contextual
    svg.rect(460, 55, 400, 170, fill='white', stroke='border')
    svg.text(660, 78, "Bağlam duyarlı parçalama", size=FS_BODY, bold=True)

    svg.rect(480, 95, 360, 35, fill='medium')
    svg.mono(490, 113, "[ACME Şirketi 2025 Ç2 Kazanç Raporu · Temel Performans Göstergeleri]", size=FS_TINY)

    svg.rect(480, 130, 360, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(490, 148, "Şirketin ikinci çeyrek geliri %3 arttı,", size=FS_TINY)
    svg.mono(490, 168, "esas olarak yeni ürün hatlarının katkısıyla.", size=FS_TINY)

    svg.text(660, 200, "→ Tam eşleşme ACME + Ç2 + gelir artışı", size=FS_SMALL, fill='text_light')

    # Arrow between
    svg.text(440, 140, "→", size=FS_TITLE, bold=True)

    # Process flow
    svg.line(20, 250, 860, 250, color='dark', dash=True)
    svg.text(w / 2, 275, "İndeksleme aşaması: LLM bağlam öneki üretir", size=FS_BODY, bold=True)

    flow_y = 300
    svg.box(30, flow_y, 180, 55, "Orijinal belge", fill='light', bold=True, font_size=FS_BODY)
    svg.arrow(210, flow_y + 27, 248, flow_y + 27)

    svg.box(250, flow_y, 180, 55, "Parçalama", fill='light', bold=True, font_size=FS_BODY)
    svg.arrow(430, flow_y + 27, 468, flow_y + 27)

    svg.box(470, flow_y, 180, 55, "LLM önek üretir\n(istem önbellekleme)", fill='medium',
            font_size=FS_SMALL, bold=True)
    svg.arrow(650, flow_y + 27, 688, flow_y + 27)

    svg.box(690, flow_y, 170, 55, "Önek + orijinal metin\n→ İndeks", fill='light', font_size=FS_SMALL, bold=True)

    # Stats
    svg.text(w / 2, h - 20,
             "Etki: Erişim başarısızlık oranı ↓%49 (+BM25), ↓%67 (+yeniden sıralama) — Anthropic verisi",
             size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-11.svg'))


# ──────────────────────── fig3-12 ────────────────────────

def fig3_12():
    """Structured knowledge extraction pipeline (Experiment 3.10)"""
    w, h = 880, 510
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Deney 3.10: Yapılandırılmış bilgi çıkarımı (yargısal emsaller)", size=FS_TITLE, bold=True)

    # Phase 1 header
    svg.rect(20, 55, 840, 200, fill='white', stroke='border')
    svg.text(440, 78, "Aşama 1: Bilgi çıkarımı ve yapılandırma", size=FS_BODY, bold=True)

    # Raw cases
    svg.rect(40, 95, 180, 65, fill='code_bg', stroke='dark', rx=4)
    svg.text(130, 113, "Orijinal karar belgeleri", size=FS_SMALL, bold=True)
    svg.mono(50, 138, "CAIL2018 veri kümesi", size=FS_TINY)

    svg.arrow(220, 127, 258, 127)

    # LLM extraction
    svg.rect(260, 95, 180, 65, fill='medium')
    svg.text(350, 113, "LLM faktör keşfi", size=FS_SMALL, bold=True)
    svg.text(350, 138, "Aşağıdan yukarı Şema", size=FS_SMALL, fill='text_light')

    svg.arrow(440, 127, 478, 127)

    # Structured JSON
    svg.rect(480, 95, 200, 65, fill='code_bg', stroke='dark', rx=4)
    svg.text(580, 113, "Yapılandırılmış JSON", size=FS_SMALL, bold=True)
    svg.mono(490, 138, "{voluntary_surrender:true, compensation:500000,", size=FS_TINY)
    svg.mono(490, 155, " injury_level:severe_second_degree}", size=FS_TINY)

    # Schema detail
    svg.rect(40, 170, 400, 70, fill='light')
    svg.text(240, 188, "Modüler veri şeması", size=FS_SMALL, bold=True)
    svg.text(240, 212, "Temel şema (gönüllü teslim/tazminat/sabıka) + suç türü genişleme şeması", size=FS_SMALL, fill='text_light')
    svg.text(240, 232, "(hırsızlık→ilgili tutar, yaralama→yaralanma derecesi)", size=FS_SMALL, fill='text_light')

    # Phase 2 header
    svg.rect(20, 270, 840, 200, fill='white', stroke='border')
    svg.text(440, 293, "Aşama 2: Faktör analizi ve bilgi modelleme", size=FS_BODY, bold=True)

    # Vectorization
    svg.rect(40, 310, 200, 65, fill='light')
    svg.text(140, 328, "Özellik vektörleştirme", size=FS_SMALL, bold=True)
    svg.text(140, 350, "One-hot kodlama + multi-hot kodlama", size=FS_SMALL, fill='text_light')
    svg.text(140, 370, "+ log dönüşümü + standartlaştırma", size=FS_SMALL, fill='text_light')

    svg.arrow(240, 342, 278, 342)

    # Clustering
    svg.rect(280, 310, 200, 65, fill='medium')
    svg.text(380, 328, "HDBSCAN kümeleme", size=FS_SMALL, bold=True)
    svg.text(380, 350, "\"dava prototipi\" keşfi", size=FS_SMALL, fill='text_light')
    svg.text(380, 370, "örn., küçük kavga → hafif yaralanma", size=FS_SMALL, fill='text_light')

    svg.arrow(480, 342, 518, 342)

    # Factor importance
    svg.rect(520, 310, 200, 65, fill='light')
    svg.text(620, 328, "faktör önem modeli", size=FS_SMALL, bold=True)
    svg.text(620, 350, "her faktörün ağırlığını nicelleştir", size=FS_SMALL, fill='text_light')
    svg.text(620, 370, "ceza karar mantığını oluştur", size=FS_SMALL, fill='text_light')

    # Application
    svg.arrow(620, 375, 620, 400)
    svg.rect(40, 400, 720, 60, fill='light')
    svg.text(400, 420, "Uygulama: konuşma tabanlı hukuki danışma Ajanı", size=FS_BODY, bold=True)
    svg.text(400, 445, "faktör önemine göre sorular yönlendir → benzer dava prototiplerini getir → veri odaklı ceza analizi",
             size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-12.svg'))


# ──────────────────────── fig3-13 ────────────────────────

def fig3_13():
    """Externalized learning loop (concrete example)"""
    w, h = 880, 490
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Dışsallaştırılmış öğrenme: deneyimden yeteneğe kapalı döngü", size=FS_TITLE, bold=True)

    # Central Agent
    cx, cy = 440, 210
    svg.circle(cx, cy, 55, fill='medium', label="Ajan", font_size=FS_BODY)

    # 5 steps around the loop
    steps = [
        ("① Görevi yürüt", 120, 100, "iade talebini işle\nmüşteri hizmetleri API'sini çağır"),
        ("② Geri bildirim al", 680, 100, "45$ başarıyla iade edildi\nson dört haneyi doğrulamak gerekiyor"),
        ("③ Yansıt ve özümse", 680, 310, "LLM deneyimi özetler:\n\"A Şirketi iadesi doğrulama gerektirir\""),
        ("④ Bilgi tabanına kaydet", 340, 380, "deneyim → vektörleştirilmiş indeks\nsüreç → araç koduna dönüştür"),
        ("⑤ Gelecekte erişim ve yeniden kullanım", 120, 310, "benzer görev → deneyimi getir\nbaşarılı stratejiyi doğrudan kullan"),
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
    svg.text(120, 409, "Bilgi: özet/ağaç özeti", size=FS_SMALL, fill='white')
    svg.rect(670, 395, 180, 28, fill='dark')
    svg.text(760, 409, "Araç: süreç → kod", size=FS_SMALL, fill='white')

    svg.save(os.path.join(OUT, 'fig3-13.svg'))


# ──────────────────────── fig3-14 ────────────────────────

def fig3_14():
    """GAIA experience learning system (Experiment 3.11)"""
    w, h = 880, 510
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Deney 3.11: GAIA deneyim öğrenme sistemi", size=FS_TITLE, bold=True)

    box_h = 60
    step_gap = 75
    base_y = 100

    # --- Left: Learning Mode ---
    lx = 20
    svg.rect(lx, 55, 400, 420, fill='white', stroke='border')
    svg.text(lx + 200, 80, "Öğrenme Modu", size=FS_BODY, bold=True)

    learn_steps = [
        ("GAIA görevi", 'medium', "karmaşık çok adımlı problem"),
        ("Ajan yürütmesi", 'light', "tarayıcı + dosya + kod yorumlayıcı"),
        ("Görev başarılı mı?", 'light', "Otomatik Değerlendirme (AWorld)"),
        ("LLM Yansıtma ve Özetleme", 'medium', "Strateji Özeti Çıkar"),
        ("Deneyim → Vektörleştirme", 'light', "Deneyim Bilgi Tabanına Kaydet"),
    ]
    for i, (label, fill, sub) in enumerate(learn_steps):
        y = base_y + i * step_gap
        svg.box(lx + 50, y, 300, box_h, label, sublabel=sub, fill=fill, bold=True, font_size=FS_BODY)
        if i > 0:
            svg.arrow(lx + 200, base_y + (i - 1) * step_gap + box_h + 2, lx + 200, y - 2)

    # --- Right: Apply Mode ---
    rx = 460
    svg.rect(rx, 55, 400, 420, fill='white', stroke='border')
    svg.text(rx + 200, 80, "Uygulama Modu", size=FS_BODY, bold=True)

    apply_steps = [
        ("Yeni GAIA Görevi", 'medium', "Yeni Soru Al"),
        ("Deneyimin Anlamsal Erişimi", 'light', "Deneyim Tabanında Benzer Görev Ara"),
        ("Sistem İstemine Enjekte Et", 'medium', "Geçmiş Başarılı Stratejiler Örnek Olarak"),
        ("Ajan yürütmesi", 'light', "Deneyimden Yararlanarak Daha Verimli Problem Çözme"),
        ("Başarı Oranı ↑ Verimlilik ↑", 'dark', "Kendi Kendine Evrim: Zamanla Güçlenme"),
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
    svg.text((kb_x1 + kb_x2) / 2, kb_cy - 8, "Deneyim Bilgi Tabanı", size=FS_SMALL, fill='white', bold=True)
    svg.text((kb_x1 + kb_x2) / 2, kb_cy + 12, "(Vektör İndeksi)", size=FS_TINY, fill='white')

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
