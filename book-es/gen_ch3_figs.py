"""Generate all Chapter 3 figures in Spanish (Knowledge Base & RAG)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    SVG, COLORS, FS_TITLE, FS_BODY, FS_SMALL, FS_TINY, STROKE_W,
)

OUT = os.path.join(os.path.dirname(__file__), 'images')


def fig3_1():
    """Knowledge map of this chapter — Figure 3-1."""
    w, h = 860, 580
    svg = SVG(w, h)

    svg.text(w / 2, 32, "Capítulo 3: Base de Conocimiento y RAG — Mapa de Conocimiento", size=FS_TITLE, bold=True)

    r1_y = 70
    svg.rect(30, r1_y, 800, 130, fill='white', stroke='border', dash=True)
    svg.text(80, r1_y + 20, "Fundamentos de RAG", size=FS_BODY, bold=True, anchor='start')

    boxes_r1 = [
        ("Incrustación densa", 50, "Word2Vec → BGE-M3"),
        ("Incrustación dispersa", 230, "TF-IDF / BM25"),
        ("Búsqueda híbrida + Reclasificación", 410, "Dos torres + Cross-Encoder"),
        ("Inferencia multimodal", 650, "Nativo / Texto / Herramienta"),
    ]
    for label, bx, sub in boxes_r1:
        svg.box(bx, r1_y + 38, 160, 50, label, fill='light', bold=True, font_size=FS_SMALL)
        svg.text(bx + 80, r1_y + 38 + 50 + 18, sub, size=FS_TINY, fill='text_light')

    svg.arrow(w / 2, r1_y + 130, w / 2, r1_y + 160)

    r2_y = 230
    svg.rect(30, r2_y, 800, 100, fill='white', stroke='border', dash=True)
    svg.text(80, r2_y + 20, "Aprendizaje desde Conocimiento Existente", size=FS_BODY, bold=True, anchor='start')

    boxes_r2 = [
        ("RAPTOR\n Ín. Jerárquico Árbol", 50),
        ("GraphRAG\n Grafo Entidad-Relación", 230),
        ("RAG agéntico\n Búsqueda como Herramienta", 410),
        ("Búsqueda Consciente de Ctx\n Enriquecimiento por Prefijo", 590),
    ]
    for label, bx in boxes_r2:
        svg.box(bx, r2_y + 35, 160, 55, label, fill='medium', font_size=FS_SMALL)

    svg.arrow(w / 2, r2_y + 100, w / 2, r2_y + 130)

    r3_y = 360
    svg.rect(30, r3_y, 800, 100, fill='white', stroke='border', dash=True)
    svg.text(80, r3_y + 20, "Aprendizaje por Exploración Autónoma", size=FS_BODY, bold=True, anchor='start')

    boxes_r3 = [
        ("Posentrenamiento\n RL → Memoria Muscular", 100),
        ("Aprendizaje en Contexto\n Inferencia Suave", 330),
        ("Aprendizaje Externalizado\n Base Conocimiento + Herramientas", 560),
    ]
    for label, bx in boxes_r3:
        svg.box(bx, r3_y + 35, 200, 55, label, fill='light', font_size=FS_SMALL)

    svg.rect(180, 490, 500, 44, fill='dark')
    svg.text(w / 2, 512, "Lección Clave: Búsqueda + Aprendizaje = Método General", size=FS_BODY, fill='white', bold=True)
    svg.arrow(w / 2, r3_y + 100, w / 2, 488)

    svg.save(os.path.join(OUT, 'fig3-1.svg'))


def fig3_2():
    """RAG End-to-End Pipeline — Figure 3-2."""
    w, h = 880, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Canalización RAG de extremo a extremo", size=FS_TITLE, bold=True)

    svg.box(20, 65, 180, 55, "① Consulta Usuario", fill='medium', bold=True, font_size=FS_BODY)
    svg.text(110, 145, '"¿Pena por homicidio intencional?"', size=FS_SMALL, fill='text_light')

    svg.arrow(200, 92, 238, 92)

    svg.box(240, 65, 180, 55, "② Búsqueda", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 140, "Búsqueda densa + BM25", size=FS_SMALL, fill='text_light')
    svg.text(330, 160, "→ Top K fragmentos", size=FS_SMALL, fill='text_light')

    svg.arrow(420, 92, 458, 92)

    svg.box(460, 65, 180, 55, "③ Aumentación", fill='light', bold=True, font_size=FS_BODY)
    svg.text(550, 140, "Consulta + Resultados", size=FS_SMALL, fill='text_light')
    svg.text(550, 160, "→ Construir prompt final", size=FS_SMALL, fill='text_light')

    svg.arrow(640, 92, 678, 92)

    svg.box(680, 65, 180, 55, "④ Generación", fill='medium', bold=True, font_size=FS_BODY)
    svg.text(770, 140, "LLM sintetiza contexto", size=FS_SMALL, fill='text_light')
    svg.text(770, 160, "→ Generar respuesta", size=FS_SMALL, fill='text_light')

    svg.line(20, 195, 860, 195, color='dark', dash=True)
    svg.text(w / 2, 215, "Ejemplo de flujo de datos", size=FS_BODY, bold=True)

    svg.rect(20, 235, 400, 90, fill='code_bg', stroke='dark', rx=4)
    svg.text(220, 253, "Fragmentos recuperados", size=FS_SMALL, bold=True)
    svg.mono(30, 278, "Código Penal Art 232: El que intencionalmente matare a otro,", size=FS_TINY)
    svg.mono(30, 298, "será castigado con pena de prisión de 10 a 25 años...", size=FS_TINY)

    svg.rect(440, 235, 420, 90, fill='code_bg', stroke='dark', rx=4)
    svg.text(650, 253, "Prompt aumentante", size=FS_SMALL, bold=True)
    svg.mono(450, 278, "Responde la pregunta basándote en el código penal:", size=FS_TINY)
    svg.mono(450, 298, "[Código Penal Art 232...] P: ¿Pena por homicidio intencional?", size=FS_TINY)

    svg.rect(20, 345, 840, 80, fill='light', stroke='border')
    svg.text(w / 2, 363, "Respuesta generada", size=FS_SMALL, bold=True)
    svg.mono(30, 390, "Según el Código Penal Art 232, el homicidio intencional se castiga con prisión de 10 a 25 años;", size=FS_TINY)
    svg.mono(30, 412, "en circunstancias atenuantes, la pena puede reducirse de 3 a 10 años.", size=FS_TINY)

    svg.save(os.path.join(OUT, 'fig3-2.svg'))


def fig3_3():
    """Evolution of dense embedding techniques — Figure 3-3."""
    w, h = 860, 340
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Evolución de las técnicas de incrustación densa", size=FS_TITLE, bold=True)

    items = [
        ("Word2Vec", "2013", "300D\nVectores de palabra estáticos", "Coocurrencia\nEntrenamiento predictivo"),
        ("GloVe", "2014", "300D\nEstadísticas globales", "Factorización matriz\n+ Coocurrencia"),
        ("BERT", "2018", "768D\nConsciente del contexto", "Transformer\nPreentrenamiento MLM"),
        ("Sentence-BERT", "2019", "768D\nIncrustación de oraciones", "Red siamesa\nAprendizaje contrastivo"),
        ("BGE-M3", "2024", "1024D\nTextos largos multilingües", "Multietapa\nEntrenamiento híbrido"),
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

    svg.text(pad_l + gap * 0.5, h - 18,
             "Vectores de palabra estáticos (un vector por palabra)", size=FS_SMALL, fill='text_light')
    svg.text(pad_l + gap * 3.5, h - 18,
             "Incrustaciones conscientes del contexto (múltiples vectores por palabra)", size=FS_SMALL, fill='text_light')

    svg.line(pad_l + gap * 1.5, 75, pad_l + gap * 1.5, h - 35, color='dark', dash=True)

    svg.save(os.path.join(OUT, 'fig3-3.svg'))


def fig3_4():
    """HNSW index structure — Figure 3-4."""
    w, h = 750, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Estructura del índice HNSW", size=FS_TITLE, bold=True)

    layers = [
        ("Capa 2 (dispersa · conexiones de larga distancia)", 70, 3),
        ("Capa 1 (densidad media)", 185, 6),
        ("Capa 0 (densa · todos los nodos)", 300, 10),
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

    svg.arrow(w / 2, 130, w / 2 - 50, 165, color='border')
    svg.text(w / 2 + 80, 148, "La búsqueda comienza en capa superior", size=FS_SMALL, fill='text_light')
    svg.arrow(w / 2 - 50, 245, w / 2 - 80, 280, color='border')
    svg.text(w / 2 + 60, 263, "Se refina capa por capa hacia abajo", size=FS_SMALL, fill='text_light')

    svg.rect(50, h - 45, 300, 32, fill='light')
    svg.text(200, h - 29, "Admite actualizaciones incrementales · Alto recall", size=FS_SMALL, bold=True)
    svg.rect(400, h - 45, 300, 32, fill='code_bg', stroke='dark', rx=4)
    svg.text(550, h - 29, "Complejidad de consulta O(log N)", size=FS_SMALL)

    svg.save(os.path.join(OUT, 'fig3-4.svg'))


def fig3_5():
    """BM25 scoring mechanism — Figure 3-5."""
    w, h = 800, 380
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Mecanismo de puntuación BM25", size=FS_TITLE, bold=True)

    svg.rect(40, 50, w - 80, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(60, 75,
             "Score(Q,D) = Σ IDF(qi) × TF(qi,D)×(k1+1) / (TF + k1×(1-b+b×|D|/avgdl))",
             size=FS_SMALL)

    boxes = [
        ("Saturación frec. término (TF)", 40, 'light', [
            "k₁ controla velocidad saturación",
            "TF ↑ pero contribución decae",
            "Ejemplo: 5→10 repeticiones",
            "Puntaje solo sube ~20%",
        ]),
        ("Frec. inversa doc. (IDF)", 290, 'light', [
            "Mide rareza de palabra",
            "\"el\" → IDF ≈ 0",
            "\"sanción\" → IDF ≈ 5.2",
            "Palabra rara peso >> común",
        ]),
        ("Normalización longitud (b)", 540, 'light', [
            "b ∈ [0,1] fuerza normalización",
            "b=0: ignorar longitud",
            "b=1: normalización total",
            "Evita sesgo a docs largos",
        ]),
    ]
    for title, bx, fill, details in boxes:
        svg.rect(bx, 120, 220, 170, fill=fill)
        svg.text(bx + 110, 148, title, size=FS_BODY, bold=True)
        svg.line(bx + 20, 163, bx + 200, 163, color='dark')
        for k, line in enumerate(details):
            svg.text(bx + 110, 190 + k * 28, line, size=FS_SMALL, fill='text_light')

    for bx in [150, 400, 650]:
        svg.line(bx, 290, bx, 315, color='dark')
    svg.rect(40, 315, w - 80, 48, fill='medium')
    svg.text(w / 2, 339, "Puntaje final = Σ (Saturación TF × Peso IDF × Normalización longitud)", size=FS_BODY, bold=True)

    svg.save(os.path.join(OUT, 'fig3-5.svg'))


def fig3_6():
    """Hybrid retrieval and re-ranking pipeline — Figure 3-6."""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Canalización de búsqueda híbrida y reclasificación", size=FS_TITLE, bold=True)

    svg.rect(30, 55, 160, 50, fill='medium')
    svg.text(110, 73, "Consulta del usuario", size=FS_BODY, bold=True)
    svg.mono(110, 93, '"conducta de gatitos"', size=FS_TINY, anchor='middle')

    svg.arrow(190, 68, 238, 68)
    svg.box(240, 50, 180, 50, "Búsqueda densa", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 118, "Coincidencia semántica: gatito ≈ gato", size=FS_SMALL, fill='text_light')

    dense_results = [
        ("doc3: \"hábitos felinos y juego de gatos...\"", "cos=0.87"),
        ("doc7: \"patrones de aseo en gatos...\"", "cos=0.82"),
        ("doc1: \"conceptos básicos de mascotas...\"", "cos=0.71"),
    ]
    for i, (doc, score) in enumerate(dense_results):
        y = 140 + i * 32
        svg.mono(250, y, doc, size=FS_TINY)
        svg.text(700, y, score, size=FS_TINY, fill='text_light', anchor='start')

    svg.arrow(190, 90, 238, 270)
    svg.box(240, 250, 180, 50, "Búsqueda dispersa (BM25)", fill='light', bold=True, font_size=FS_BODY)
    svg.text(330, 318, "Coincidencia exacta: clave \"gatitos\"", size=FS_SMALL, fill='text_light')

    sparse_results = [
        ("doc5: \"entrenamiento de gatitos...\"", "BM25=8.4"),
        ("doc9: \"guía de adopción de gatitos...\"", "BM25=6.1"),
        ("doc2: \"consejos de salud gatitos...\"", "BM25=3.2"),
    ]
    for i, (doc, score) in enumerate(sparse_results):
        y = 340 + i * 32
        svg.mono(250, y, doc, size=FS_TINY)
        svg.text(700, y, score, size=FS_TINY, fill='text_light', anchor='start')

    svg.arrow(770, 180, 808, 220)
    svg.arrow(770, 370, 808, 330)

    svg.rect(790, 215, 70, 120, fill='medium')
    svg.text(825, 250, "Fusionar", size=FS_BODY, bold=True)
    svg.text(825, 275, "Deduplicar", size=FS_BODY, bold=True)
    svg.text(825, 300, "6→5", size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-6.svg'))


def fig3_7():
    """RAPTOR tree structure — Figure 3-7."""
    w, h = 800, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Índice jerárquico de árbol RAPTOR", size=FS_TITLE, bold=True)

    svg.box(300, 55, 200, 50, "Resumen general", fill='dark', bold=True, font_size=FS_BODY)
    svg.text(300 + 200 + 15, 80, "← Nodo raíz", size=FS_SMALL, fill='text_light', anchor='start')

    mid_nodes = [("Resumen clúster A", 80), ("Resumen clúster B", 320), ("Resumen clúster C", 560)]
    for label, x in mid_nodes:
        svg.box(x, 150, 160, 48, label, fill='medium', font_size=FS_BODY)
    svg.line(400, 105, 160, 150, color='border')
    svg.line(400, 105, 400, 150, color='border')
    svg.line(400, 105, 640, 150, color='border')
    svg.text(35, 230, "Capa media ↑", size=FS_SMALL, fill='text_light', anchor='start')

    chunks = [
        [(40, "Fragmento 1"), (140, "Fragmento 2"), (240, "Fragmento 3")],
        [(360, "Fragmento 4"), (460, "Fragmento 5")],
        [(560, "Fragmento 6"), (660, "Fragmento 7")],
    ]
    leaf_w = 88
    mid_cxs = [160, 400, 640]
    for gi, group in enumerate(chunks):
        for cx, label in group:
            svg.box(cx, 250, leaf_w, 40, label, fill='light', font_size=FS_SMALL)
            svg.line(cx + leaf_w / 2, 250, mid_cxs[gi], 198, color='dark')
    svg.text(35, 295, "Capa hoja ↑", size=FS_SMALL, fill='text_light', anchor='start')

    svg.rect(40, 320, 720, 55, fill='white', stroke='dark', dash=True)
    svg.text(400, 340, "Documento original", size=FS_BODY, fill='text_light')
    for bx in range(60, 720, 110):
        svg.rect(bx, 350, 90, 16, fill='light')

    svg.text(w / 2, h - 20, "Abstracción recursiva de abajo a arriba: detalles → temas → vista general", size=FS_BODY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-7.svg'))


def fig3_8():
    """GraphRAG relational network — Figure 3-8."""
    w, h = 750, 430
    svg = SVG(w, h)
    svg.text(w / 2, 28, "Grafo de conocimiento entidad-relación GraphRAG", size=FS_TITLE, bold=True)

    nodes = [
        ("Intel", 375, 100, 'medium'),
        ("SSE", 150, 190, 'light'),
        ("AVX", 550, 190, 'light'),
        ("Reg. XMM", 100, 320, 'light'),
        ("ADDPS", 280, 340, 'light'),
        ("Reg. YMM", 520, 320, 'light'),
        ("Ops FP", 375, 250, 'light'),
    ]
    node_r = 42

    svg.rect(50, 275, 300, 110, fill='none', stroke='border', dash=True)
    svg.text(200, 395, "Comunidad: Conjunto instrucciones SSE", size=FS_SMALL, fill='text_light')

    for label, x, y, fill in nodes:
        svg.circle(x, y, node_r, fill=fill, label=label, font_size=FS_SMALL)

    edges = [
        (0, 1, "Desarrollo"), (0, 2, "Desarrollo"),
        (1, 3, "Uso"), (1, 6, ""), (1, 4, "Incluye"),
        (2, 5, "Uso"), (2, 6, "Ejecución"),
        (6, 3, ""), (6, 5, "Operación"),
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


def fig3_9():
    """Agentic RAG vs Non-Agentic RAG — Figure 3-9."""
    w, h = 880, 560
    svg = SVG(w, h)
    col_w = 400
    lx, rx = 20, 460

    svg.rect(lx, 50, col_w, 45, fill='medium')
    svg.text(lx + col_w / 2, 73, "RAG No Agéntico", size=FS_BODY, bold=True)

    steps_l = [
        ("Consulta: \"¿Pena por lesiones graves negligentes \nsi el acusado tiene antecedentes de robo?\"", 'light'),
        ("Búsqueda única:\n\"Sanción por lesiones graves negligentes\"", 'light'),
        ("Resultado: Solo artículos básicos hallados\n(falta contexto relevante)", 'code_bg'),
        ("Generación directa: Faltan factores de\n\"alcohol\" y \"antecedentes\"", 'light'),
    ]
    prev_y = 95
    for i, (s, fill) in enumerate(steps_l):
        y = 110 + i * 108
        svg.box(lx + 30, y, 340, 80, s, fill=fill, font_size=FS_SMALL)
        if i > 0:
            svg.arrow(lx + 200, prev_y + 80 + 2, lx + 200, y - 2)
        prev_y = y

    svg.text(lx + col_w / 2, h - 15, "Paso único · Información incompleta", size=FS_BODY, fill='text_light')

    svg.line(440, 50, 440, h - 5, color='dark', dash=True)

    svg.rect(rx, 50, col_w, 45, fill='medium')
    svg.text(rx + col_w / 2, 73, "RAG Agéntico (ReAct)", size=FS_BODY, bold=True)

    steps_r = [
        ("Pensamiento: Descomponer en 3 subpreguntas", 'light'),
        ("Búsqueda ①: \"Sanción lesiones graves negligentes\"\nBúsqueda ②: \"Responsabilidad penal por embriaguez\"\nBúsqueda ③: \"Efecto de antecedentes por robo\"", 'code_bg'),
        ("Observación: Normas básicas halladas pero falta\nconexión entre \"antecedentes\" y \"lesiones\"", 'light'),
        ("Búsqueda ④: \"Interpretación judicial de\nreincidencia en distintos delitos\"", 'code_bg'),
        ("Síntesis: Respuesta completa con todas las\nnormas aplicables y análisis penal", 'medium'),
    ]
    ys = []
    for i, (s, fill) in enumerate(steps_r):
        y = 105 + i * 86
        hh = 68
        svg.box(rx + 30, y, 340, hh, s, fill=fill, font_size=FS_SMALL)
        ys.append(y)
        if i > 0:
            svg.arrow(rx + 200, ys[i - 1] + hh + 2, rx + 200, y - 2)

    loop_x = rx + 370 + 10
    svg.elems.append(
        f'<path d="M {loop_x},{ys[2] + 34} C {loop_x + 28},{ys[2] + 34} '
        f'{loop_x + 28},{ys[1] + 34} {loop_x},{ys[1] + 34}" '
        f'fill="none" stroke="{COLORS["border"]}" stroke-width="{STROKE_W}" '
        f'stroke-dasharray="6,3" marker-end="url(#ah)"/>'
    )
    svg.text(loop_x + 4, (ys[1] + ys[2]) / 2 + 34, "Iteración", size=FS_SMALL, fill='text_light',
             anchor='start')

    svg.text(rx + col_w / 2, h - 15, "Iteración multirronda · Información completa", size=FS_BODY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-9.svg'))


def fig3_10():
    """Agentic RAG System Architecture — Figure 3-10."""
    w, h = 880, 500
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experimento 3.6: Arquitectura del sistema RAG agéntico", size=FS_TITLE, bold=True)

    svg.rect(220, 55, 440, 200, fill='white', stroke='border')
    svg.text(440, 78, "Agente (Bucle ReAct)", size=FS_BODY, bold=True)

    react_items = [
        ("① Pensamiento", 240, 100, 180, 45, 'light'),
        ("② Acción", 460, 100, 180, 45, 'medium'),
        ("③ Observación", 350, 180, 180, 45, 'light'),
    ]
    for label, bx, by, bw, bh, fill in react_items:
        svg.box(bx, by, bw, bh, label, fill=fill, font_size=FS_SMALL, bold=True)

    svg.arrow(420, 122, 458, 122)
    svg.arrow(640, 130, 530, 178, color='border')
    svg.arrow(350, 202, 280, 145, color='border')

    svg.text(360, 165, "Bucle hasta que la información sea suficiente", size=FS_TINY, fill='text_light')

    svg.box(20, 95, 160, 55, "Consulta usuario", fill='medium', bold=True, font_size=FS_BODY)
    svg.arrow(180, 122, 218, 122)

    svg.box(700, 95, 160, 55, "Respuesta final", fill='medium', bold=True, font_size=FS_BODY)
    svg.arrow(660, 122, 698, 122)

    svg.rect(100, 290, 680, 85, fill='white', stroke='border', dash=True)
    svg.text(440, 312, "Capa de herramientas", size=FS_BODY, bold=True)
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

    svg.rect(100, 400, 680, 85, fill='white', stroke='dark', dash=True)
    svg.text(440, 420, "Backend de base de conocimiento (intercambiable)", size=FS_BODY, bold=True)
    backends = [
        ("retrieval-pipeline\nBúsqueda híbrida", 120),
        ("structured-index\nRAPTOR/GraphRAG", 340),
        ("contextual-retrieval\nConsciente del contexto", 560),
    ]
    for label, bx in backends:
        svg.box(bx, 435, 180, 45, label, fill='light', font_size=FS_SMALL)

    svg.arrow(230, 365, 230, 398)
    svg.arrow(440, 375, 440, 398)

    svg.save(os.path.join(OUT, 'fig3-10.svg'))


def fig3_11():
    """Context-aware retrieval — Figure 3-11."""
    w, h = 880, 430
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Búsqueda consciente del contexto", size=FS_TITLE, bold=True)

    svg.rect(20, 55, 400, 170, fill='white', stroke='border')
    svg.text(220, 78, "Fragmentado tradicional (sin contexto)", size=FS_BODY, bold=True)

    svg.rect(40, 95, 360, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(50, 112, "Los ingresos del segundo trimestre subieron 3%,", size=FS_TINY)
    svg.mono(50, 132, "debido principalmente a nuevas líneas de productos.", size=FS_TINY)

    svg.text(220, 170, "Pregunta: ¿Qué \"empresa\"? ¿Qué año?", size=FS_SMALL, fill='text_light')
    svg.text(220, 195, "→ Búsqueda coincide con datos de ingresos de empresas no relacionadas", size=FS_SMALL, fill='text_light')

    svg.rect(460, 55, 400, 170, fill='white', stroke='border')
    svg.text(660, 78, "Fragmentado consciente del contexto", size=FS_BODY, bold=True)

    svg.rect(480, 95, 360, 35, fill='medium')
    svg.mono(490, 113, "[Informe Financiero ACME Q2 2025 · Indicadores Clave]", size=FS_TINY)

    svg.rect(480, 130, 360, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(490, 148, "Los ingresos del segundo trimestre subieron 3%,", size=FS_TINY)
    svg.mono(490, 168, "debido principalmente a nuevas líneas de productos.", size=FS_TINY)

    svg.text(660, 200, "→ Coincidencia exacta ACME + Q2 + aumento ingresos", size=FS_SMALL, fill='text_light')

    svg.text(440, 140, "→", size=FS_TITLE, bold=True)

    svg.line(20, 250, 860, 250, color='dark', dash=True)
    svg.text(w / 2, 275, "Fase de indexación: el LLM genera el prefijo de contexto", size=FS_BODY, bold=True)

    flow_y = 300
    svg.box(30, flow_y, 180, 55, "Documento original", fill='light', bold=True, font_size=FS_BODY)
    svg.arrow(210, flow_y + 27, 248, flow_y + 27)

    svg.box(250, flow_y, 180, 55, "Fragmentación", fill='light', bold=True, font_size=FS_BODY)
    svg.arrow(430, flow_y + 27, 468, flow_y + 27)

    svg.box(470, flow_y, 180, 55, "LLM genera prefijo\n(caché de prompt)", fill='medium',
            font_size=FS_SMALL, bold=True)
    svg.arrow(650, flow_y + 27, 688, flow_y + 27)

    svg.box(690, flow_y, 170, 55, "Prefijo + texto orig.\n→ Índice", fill='light', font_size=FS_SMALL, bold=True)

    svg.text(w / 2, h - 20,
             "Impacto: Tasa de fallos ↓49% (+BM25), ↓67% (+reclasificación) — datos de Anthropic",
             size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-11.svg'))


def fig3_12():
    """Structured knowledge extraction pipeline — Figure 3-12."""
    w, h = 880, 510
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experimento 3.10: Extracción de conocimiento estructurado (precedentes)", size=FS_TITLE, bold=True)

    svg.rect(20, 55, 840, 200, fill='white', stroke='border')
    svg.text(440, 78, "Fase 1: Extracción y estructuración de conocimiento", size=FS_BODY, bold=True)

    svg.rect(40, 95, 180, 65, fill='code_bg', stroke='dark', rx=4)
    svg.text(130, 113, "Sentencias originales", size=FS_SMALL, bold=True)
    svg.mono(50, 138, "Conjunto datos CAIL2018", size=FS_TINY)

    svg.arrow(220, 127, 258, 127)

    svg.rect(260, 95, 180, 65, fill='medium')
    svg.text(350, 113, "Descubrimiento factores LLM", size=FS_SMALL, bold=True)
    svg.text(350, 138, "Esquema de abajo a arriba", size=FS_SMALL, fill='text_light')

    svg.arrow(440, 127, 478, 127)

    svg.rect(480, 95, 200, 65, fill='code_bg', stroke='dark', rx=4)
    svg.text(580, 113, "JSON estructurado", size=FS_SMALL, bold=True)
    svg.mono(490, 138, "{voluntary_surrender:true, compensation:500000,", size=FS_TINY)
    svg.mono(490, 155, " injury_level:severe_second_degree}", size=FS_TINY)

    svg.rect(40, 170, 400, 70, fill='light')
    svg.text(240, 188, "Esquema de datos modular", size=FS_SMALL, bold=True)
    svg.text(240, 212, "Esquema básico (entrega voluntaria/indemnización/antecedentes) + esquema por delito", size=FS_SMALL, fill='text_light')
    svg.text(240, 232, "(robo→monto involucrado, lesiones→nivel de lesión)", size=FS_SMALL, fill='text_light')

    svg.rect(20, 270, 840, 200, fill='white', stroke='border')
    svg.text(440, 293, "Fase 2: Análisis de factores y modelado de conocimiento", size=FS_BODY, bold=True)

    svg.rect(40, 310, 200, 65, fill='light')
    svg.text(140, 328, "Vectorización de características", size=FS_SMALL, bold=True)
    svg.text(140, 350, "Codificación one-hot + multi-hot", size=FS_SMALL, fill='text_light')
    svg.text(140, 370, "+ transf. logarítmica + estandariz.", size=FS_SMALL, fill='text_light')

    svg.arrow(240, 342, 278, 342)

    svg.rect(280, 310, 200, 65, fill='medium')
    svg.text(380, 328, "Agrupamiento HDBSCAN", size=FS_SMALL, bold=True)
    svg.text(380, 350, "Descubrimiento \"prototipos de caso\"", size=FS_SMALL, fill='text_light')
    svg.text(380, 370, "ej. riña menor → lesión leve", size=FS_SMALL, fill='text_light')

    svg.arrow(480, 342, 518, 342)

    svg.rect(520, 310, 200, 65, fill='light')
    svg.text(620, 328, "Modelo importancia factores", size=FS_SMALL, bold=True)
    svg.text(620, 350, "Cuantificar peso de cada factor", size=FS_SMALL, fill='text_light')
    svg.text(620, 370, "Construir lógica de sentencia", size=FS_SMALL, fill='text_light')

    svg.arrow(620, 375, 620, 400)
    svg.rect(40, 400, 720, 60, fill='light')
    svg.text(400, 420, "Aplicación: Agente de consulta legal conversacional", size=FS_BODY, bold=True)
    svg.text(400, 445, "Preguntar según importancia → recuperar prototipos similares → análisis penal basado en datos",
             size=FS_SMALL, fill='text_light')

    svg.save(os.path.join(OUT, 'fig3-12.svg'))


def fig3_13():
    """Externalized learning loop — Figure 3-13."""
    w, h = 880, 490
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Aprendizaje externalizado: bucle cerrado de experiencia a capacidad", size=FS_TITLE, bold=True)

    cx, cy = 440, 210
    svg.circle(cx, cy, 55, fill='medium', label="Agente", font_size=FS_BODY)

    steps = [
        ("① Ejecutar tarea", 120, 100, "Procesar reembolso\nLlamar a API de servicio"),
        ("② Recibir retroalim.", 680, 100, "$45 reembolsados con éxito\nSe requiere verificar últimos 4 dígitos"),
        ("③ Reflexionar y resumir", 680, 310, "El LLM resume la experiencia:\n\"Reembolso Comp. A requiere verificación\""),
        ("④ Guardar en base conoc.", 340, 380, "Experiencia → índice vectorizado\nProceso → código de herramienta"),
        ("⑤ Recuperar y reutilizar", 120, 310, "Tarea similar → recuperar experiencia\nUsar estrategia exitosa directamente"),
    ]

    positions = []
    for label, x, y, detail in steps:
        svg.box(x, y, 200, 80, label + "\n" + detail,
                fill='light', font_size=FS_SMALL)
        positions.append((x + 100, y + 40))

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

    svg.rect(30, 395, 180, 28, fill='dark')
    svg.text(120, 409, "Conocimiento: resumen", size=FS_SMALL, fill='white')
    svg.rect(670, 395, 180, 28, fill='dark')
    svg.text(760, 409, "Herramienta: proceso→código", size=FS_SMALL, fill='white')

    svg.save(os.path.join(OUT, 'fig3-13.svg'))


def fig3_14():
    """GAIA experience learning system — Figure 3-14."""
    w, h = 880, 510
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experimento 3.11: Sistema de aprendizaje de experiencia GAIA", size=FS_TITLE, bold=True)

    box_h = 60
    step_gap = 75
    base_y = 100

    lx = 20
    svg.rect(lx, 55, 400, 420, fill='white', stroke='border')
    svg.text(lx + 200, 80, "Modo de aprendizaje", size=FS_BODY, bold=True)

    learn_steps = [
        ("Tarea GAIA", 'medium', "Problema complejo multipaso"),
        ("Ejecución del Agente", 'light', "Navegador + archivo + intérprete código"),
        ("¿Éxito en tarea?", 'light', "Evaluación automática (AWorld)"),
        ("Reflexión y resumen LLM", 'medium', "Extraer resumen de estrategia"),
        ("Experiencia → Vectorización", 'light', "Guardar en base de experiencia"),
    ]
    for i, (label, fill, sub) in enumerate(learn_steps):
        y = base_y + i * step_gap
        svg.box(lx + 50, y, 300, box_h, label, sublabel=sub, fill=fill, bold=True, font_size=FS_BODY)
        if i > 0:
            svg.arrow(lx + 200, base_y + (i - 1) * step_gap + box_h + 2, lx + 200, y - 2)

    rx = 460
    svg.rect(rx, 55, 400, 420, fill='white', stroke='border')
    svg.text(rx + 200, 80, "Modo de aplicación", size=FS_BODY, bold=True)

    apply_steps = [
        ("Nueva Tarea GAIA", 'medium', "Recibir nueva pregunta"),
        ("Búsqueda semántica de exp.", 'light', "Buscar tarea similar en base de exp."),
        ("Inyectar en prompt del sist.", 'medium', "Estrategias pasadas como ejemplos"),
        ("Ejecución del Agente", 'light', "Resolución más eficiente basada en exp."),
        ("Éxito ↑ Eficiencia ↑", 'dark', "Autoevolución: fortalece con el tiempo"),
    ]
    for i, (label, fill, sub) in enumerate(apply_steps):
        y = base_y + i * step_gap
        svg.box(rx + 50, y, 300, box_h, label, sublabel=sub, fill=fill, bold=True, font_size=FS_BODY)
        if i > 0:
            svg.arrow(rx + 200, base_y + (i - 1) * step_gap + box_h + 2, rx + 200, y - 2)

    kb_cy = base_y + 2 * step_gap + box_h / 2
    kb_x1, kb_x2 = 375, 505
    svg.rect(kb_x1, kb_cy - 25, kb_x2 - kb_x1, 50, fill='dark')
    svg.text((kb_x1 + kb_x2) / 2, kb_cy - 8, "Base de Experiencia", size=FS_SMALL, fill='white', bold=True)
    svg.text((kb_x1 + kb_x2) / 2, kb_cy + 12, "(Índice Vectorial)", size=FS_TINY, fill='white')

    last_y = base_y + 4 * step_gap + box_h / 2
    svg.arrow(lx + 350, last_y, kb_x1 - 2, kb_cy + 10)
    apply2_y = base_y + 1 * step_gap + box_h / 2
    svg.arrow(kb_x2 + 2, kb_cy - 10, rx + 50, apply2_y)

    svg.save(os.path.join(OUT, 'fig3-14.svg'))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    fig3_1()
    fig3_2()
    fig3_3()
    fig3_4()
    fig3_5()
    fig3_6()
    fig3_7()
    fig3_8()
    fig3_9()
    fig3_10()
    fig3_11()
    fig3_12()
    fig3_13()
    fig3_14()
    print("Chapter 3 figures generated.")
