"""Generate all SVG illustrations for Chapter 5 (Code Generation)."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    SVG, COLORS, FS_TITLE, FS_BODY, FS_SMALL, FS_TINY, FS_LABEL,
    CORNER_R,
)

OUT = os.path.join(os.path.dirname(__file__), 'images')


def _pill(svg, x, y, w, h, label, fill='light', font_size=FS_SMALL, bold=False):
    svg.rect(x, y, w, h, fill=fill, rx=h // 2)
    c = 'white' if fill in ('dark', 'darker') else 'text'
    svg.text(x + w / 2, y + h / 2, label, size=font_size, fill=c, bold=bold)


def fig5_1():
    """OpenClaw architecture — Figure 5-1."""
    w, h = 980, 600
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Arquitectura OpenClaw: el Agente de programación como núcleo del Agente general", size=FS_TITLE, bold=True)

    gw_y, gw_h = 58, 66
    svg.group_box(60, gw_y, w - 120, gw_h, "Pasarela de mensajería multiplataforma (capa de interacción del usuario)")
    channels = ["WhatsApp", "Telegram", "iMessage", "Slack", "CLI"]
    pill_w, pill_h = 130, 32
    total_pw = len(channels) * pill_w + (len(channels) - 1) * 18
    px_start = (w - total_pw) / 2
    for i, ch in enumerate(channels):
        px = px_start + i * (pill_w + 18)
        svg.rect(px, gw_y + 26, pill_w, pill_h, fill='medium', rx=pill_h // 2)
        svg.text(px + pill_w / 2, gw_y + 26 + pill_h / 2, ch, size=FS_SMALL)

    svg.arrow(w / 2, gw_y + gw_h + 2, w / 2, 158)
    svg.text(w / 2 + 12, 134, "Solicitud en lenguaje natural", size=FS_LABEL, fill='text_light', anchor='start')

    ca_x, ca_y, ca_w, ca_h = 200, 160, 580, 210
    svg.rect(ca_x, ca_y, ca_w, ca_h, fill='light')
    svg.rect(ca_x, ca_y, ca_w, 40, fill='darker', rx=6)
    svg.text(ca_x + ca_w / 2, ca_y + 20,
             "Entorno de ejecución del Agente de programación (inferencia + núcleo de ejecución)", size=FS_BODY, bold=True, fill='white')

    tools = [
        ("Code Interpreter", "Ejecución de código"), ("Bash Shell", "Comandos de sistema"),
        ("Read File", "Leer archivo"), ("Write File", "Escribir archivo"),
        ("Edit File", "Editar archivo"), ("Glob", "Buscar archivos"), ("Grep", "Buscar contenido"),
    ]
    tw, th, tgap = 132, 60, 12
    for ri, row in enumerate([tools[:4], tools[4:]]):
        row_total_w = len(row) * tw + (len(row) - 1) * tgap
        rx_start = ca_x + (ca_w - row_total_w) / 2
        ry = ca_y + 56 + ri * (th + tgap)
        for ci, (name, desc) in enumerate(row):
            tx = rx_start + ci * (tw + tgap)
            svg.rect(tx, ry, tw, th, fill='white')
            svg.text(tx + tw / 2, ry + 22, name, size=FS_TINY, bold=True)
            svg.text(tx + tw / 2, ry + 42, desc, size=FS_TINY, fill='text_light')

    dr_x, dr_y, dr_w, dr_h = 22, 198, 158, 86
    svg.rect(dr_x, dr_y, dr_w, dr_h, fill='medium')
    svg.text(dr_x + dr_w / 2, dr_y + 22, "Módulo búsqueda web", size=FS_SMALL, bold=True)
    svg.text(dr_x + dr_w / 2, dr_y + 44, "Deep Research", size=FS_TINY, fill='text_light')
    svg.text(dr_x + dr_w / 2, dr_y + 66, "Peticiones web · parseo", size=FS_TINY, fill='text_light')
    svg.arrow(dr_x + dr_w + 2, dr_y + dr_h / 2, ca_x - 2, ca_y + ca_h / 2)

    cu_x, cu_y, cu_w, cu_h = 800, 198, 158, 86
    svg.rect(cu_x, cu_y, cu_w, cu_h, fill='medium')
    svg.text(cu_x + cu_w / 2, cu_y + 22, "Automatiz. navegador", size=FS_SMALL, bold=True)
    svg.text(cu_x + cu_w / 2, cu_y + 44, "Computer Use", size=FS_TINY, fill='text_light')
    svg.text(cu_x + cu_w / 2, cu_y + 66, "DOM de Playwright", size=FS_TINY, fill='text_light')
    svg.arrow(ca_x + ca_w + 2, ca_y + ca_h / 2, cu_x - 2, cu_y + cu_h / 2)

    fs_y, fs_h = 410, 140
    svg.arrow(w / 2, ca_y + ca_h + 2, w / 2, fs_y - 2)
    svg.text(w / 2 + 12, 390, "Leer / escribir archivo", size=FS_LABEL, fill='text_light', anchor='start')
    svg.group_box(60, fs_y, w - 120, fs_h, "Sistema de archivos (memoria · conocimiento · centro de habilidades)")

    mem_items = [
        ("MEMORY.md", "Hechos de alto nivel / pref. usuario"),
        ("daily/AAAA-MM-DD.md", "Archivo diario / reg. interacción"),
        ("SOUL.md", "Identidad y reglas del Agente"),
        ("Archivos de conocimiento", "Experiencia de tarea / autoevolución"),
        ("Control de versión Git", "Reversión memoria / auditoría historial"),
    ]
    item_w, item_h, item_gap = 162, 76, 16
    total_iw = len(mem_items) * item_w + (len(mem_items) - 1) * item_gap
    ix_start = (w - total_iw) / 2
    for i, (title, desc) in enumerate(mem_items):
        ix = ix_start + i * (item_w + item_gap)
        iy = fs_y + 34
        svg.rect(ix, iy, item_w, item_h, fill='white')
        svg.text(ix + item_w / 2, iy + 26, title, size=FS_TINY, bold=True)
        svg.text(ix + item_w / 2, iy + 52, desc, size=FS_TINY, fill='text_light')

    os_y = fs_y + fs_h + 16
    svg.rect(60, os_y, w - 120, 38, fill='darker', rx=6)
    svg.text(w / 2, os_y + 19,
             "LLM = el nuevo sistema operativo: oculta la complejidad y ofrece abstracción unificada", size=FS_SMALL, bold=True, fill='white')

    svg.save(os.path.join(OUT, 'fig5-1.svg'))


def fig5_2():
    """Coding Agent multi-phase workflow — Figure 5-2."""
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Flujo de trabajo por capas del Agente de programación", size=FS_TITLE, bold=True)

    phases = [
        ("① Documentación proyecto", 'medium', [
            ("read_file", "README.md, ARCHITECTURE.md"),
            ("glob", "**/*.py, **/*.ts"),
            ("write_file", "→ Generar guía CLAUDE.md"),
        ]),
        ("② Comprensión requisitos", 'light', [
            ("ask_user", '"¿Objetivo es latencia o rendimiento?"'),
            ("grep", '"latency|throughput" src/'),
            ("read_file", "src/config.py (parámetros actuales)"),
        ]),
        ("③ Documento diseño", 'light', [
            ("write_file", "design.md (Comparación esquemas)"),
            ("ask_user", "Enviar diseño → Esperar aprobación"),
            ("—", "Tras revisión humana → Continuar"),
        ]),
        ("④ Codificación y pruebas", 'medium', [
            ("edit_file", "old_str→new_str cambiar código"),
            ("bash", "pytest tests/ -v"),
            ("edit_file", "Corregir pruebas fallidas → Reejecutar"),
        ]),
        ("⑤ Revisión y entrega", 'light', [
            ("bash", "ruff check src/ (linter)"),
            ("read_file", "Autorrevisión: legibilidad/seguridad/rendimiento"),
            ("edit_file", "Actualizar ARCHITECTURE.md"),
        ]),
    ]

    phase_w = 155
    phase_gap = 12
    total_w = len(phases) * phase_w + (len(phases) - 1) * phase_gap
    sx = (w - total_w) / 2

    for i, (title, fill, steps) in enumerate(phases):
        x = sx + i * (phase_w + phase_gap)
        ph = 240
        svg.rect(x, 55, phase_w, ph, fill=fill)
        svg.text(x + phase_w / 2, 78, title, size=FS_SMALL, bold=True)
        svg.line(x + 8, 92, x + phase_w - 8, 92, color='dark')

        for j, (tool, desc) in enumerate(steps):
            ty = 110 + j * 70
            _pill(svg, x + 8, ty, phase_w - 16, 22, tool, fill='dark', font_size=11, bold=True)
            svg.text_block(x + 10, ty + 26, phase_w - 20, desc.split('\n'),
                           size=10, min_size=7, anchor='start', mono=True, line_gap=1.45)

        if i < len(phases) - 1:
            ax = x + phase_w + 2
            svg.arrow(ax, 55 + ph / 2, ax + phase_gap - 4, 55 + ph / 2)

    svg.line(30, 320, w - 30, 320, color='dark', dash=True)
    svg.text(w / 2, 340, "Mecanismo de retroalimentación de bucle cerrado", size=FS_BODY, bold=True)

    loops = [
        ("Fallo en prueba → Editar código → Reejecutar pruebas", "④ Bucle interno: converge en 2-3 rondas promedio"),
        ("Error de linter → Corregir de inmediato → Recomprobar", "⑤ Bucle interno: se activa automático tras edición"),
        ("Problema en revisión → Volver a ④ y corregir", "⑤→④ retorno: garantiza la calidad de entrega"),
    ]
    ly = 365
    for label, note in loops:
        svg.rect(80, ly, 500, 46, fill='light')
        svg.text(330, ly + 15, label, size=FS_SMALL, bold=True)
        svg.text(330, ly + 34, note, size=FS_TINY, fill='text_light')
        ly += 50

    annots = [
        "Barra de estado: cwd, rama git",
        "Barra de estado: cambios no preparados",
        "Salida herramientas: recorte head/tail",
        "Sesión de terminal persistente",
    ]
    for i, ann in enumerate(annots):
        svg.rect(610, 365 + i * 50, 250, 38, fill='code_bg', stroke='dark', rx=4)
        svg.text(735, 384 + i * 50, ann, size=FS_TINY, fill='text_light')

    svg.text(w / 2, 565, "Planificar antes de actuar · Verificación de extremo a extremo · Código y docs evolucionan juntos", size=FS_BODY, bold=True, fill='darker')

    svg.save(os.path.join(OUT, 'fig5-2.svg'))


def fig5_3():
    """Search tool comparison — Figure 5-3."""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Comparación de cuatro herramientas de búsqueda", size=FS_TITLE, bold=True)

    tools = [
        ("Coincidencia de contenido por regex (grep)", 'medium',
         "rg \"def handle_.*\" --type py",
         ["src/api.py:42:  def handle_request(..)",
          "src/api.py:89:  def handle_timeout(..)",
          "src/ws.py:15:   def handle_connect(..)"],
         "Texto completo → todas las ubicaciones"),
        ("Coincidencia de nombre de archivo (glob)", 'light',
         "glob: **/test_*.py",
         ["tests/test_api.py",
          "tests/test_auth.py",
          "tests/unit/test_parser.py"],
         "Patrón de ruta → no lee contenido"),
        ("Búsqueda semántica de código", 'light',
         '"Manejar validación de entrada de usuario"',
         ["[0.91] src/validators.py:validate_input()",
          "[0.87] src/forms.py:sanitize_fields()",
          "[0.82] src/api.py:check_params()"],
         "Lenguaje natural → Híbrido vector + BM25"),
        ("Definición / Referencia de símbolos", 'medium',
         "find_references: UserService",
         ["Definición: src/services/user.py:12",
          "Referencia: src/api/routes.py:34 (import)",
          "Referencia: src/api/routes.py:56 (llamada)",
          "Referencia: tests/test_user.py:8 (prueba)"],
         "Nivel AST → Distingue mismos nombres"),
    ]

    col_w = (w - 60) // 2
    col_gap = 20

    for i, (title, fill, query, results, note) in enumerate(tools):
        col = i % 2
        row = i // 2
        x = 20 + col * (col_w + col_gap)
        y = 55 + row * 260

        svg.rect(x, y, col_w, 240, fill='white', stroke='border')
        svg.rect(x, y, col_w, 36, fill=fill, rx=CORNER_R)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(x + col_w / 2, y + 18, title, size=FS_SMALL, bold=True, fill=tc)

        svg.text(x + 12, y + 54, "Consulta:", size=FS_TINY, bold=True, anchor='start', fill='text_light')
        svg.rect(x + 8, y + 64, col_w - 16, 24, fill='code_bg', stroke='dark', rx=3)
        svg.mono(x + 14, y + 76, query, size=11)

        svg.text(x + 12, y + 102, "Resultado:", size=FS_TINY, bold=True, anchor='start', fill='text_light')
        rh = len(results) * 20 + 12
        svg.rect(x + 8, y + 112, col_w - 16, rh, fill='code_bg', stroke='dark', rx=3)
        for j, r in enumerate(results):
            svg.mono(x + 14, y + 128 + j * 20, r, size=10)

        svg.text(x + col_w / 2, y + 226, note, size=FS_TINY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig5-3.svg'))


def fig5_4():
    """File Editing Scheme Comparison — Figure 5-4."""
    w, h = 900, 700
    svg = SVG(w, h)
    svg.text(w / 2, 28, "Comparación de cinco esquemas de edición de archivos", size=FS_TITLE, bold=True)

    approaches = [
        ("Modelo Diff + Apply", "dark",
         ["El LLM genera explicación Diff:",
          "- def foo(x):",
          "    return x",
          "+ def foo(x, y=0):",
          "+   return x + y",
          "→ Modelo pequeño ubica y aplica"],
         "Ventajas: Separación de responsabilidades",
         "Contras: Pequeña desviación rompe alineación"),
        ("Cadena antigua → Cadena nueva", "medium",
         ['old: "def foo(x):\\n',
          '       return x"',
          'new: "def foo(x, y=0):\\n',
          '       return x + y"',
          "→ Reemplazo por coincidencia exacta"],
         "Ventajas: Predecible, sin ambigüedad",
         "Contras: Grandes eliminaciones requieren salida completa"),
        ("Ubicación por num. línea", "light",
         ["Eliminar líneas 42-43, agregar:",
          "  def foo(x, y=0):",
          "    return x + y",
          "",
          "→ El núm. de línea especifica el rango exacto"],
         "Ventajas: Eficiente para operaciones grandes",
         "Contras: Propensa a errores en archivos largos"),
        ("Comandos estilo Vim", "light",
         ["42G  (ir a línea 42)",
          "cw   (cambiar palabra)",
          "dd   (eliminar línea)",
          "yy/p (copiar/pegar)",
          "→ Semántica de edición rica"],
         "Ventajas: Mover/reorganizar eficientemente",
         "Contras: Modelos débiles generan más errores"),
        ("Coincidencia inicio-fin", "medium",
         ['start: "def foo(x):"',
          'end:   "    return x"',
          'new: "def foo(x, y=0):',
          '       return x + y"',
          "→ Bastan los límites para ubicar"],
         "Ventajas: Gran eliminación sin salida completa",
         "Contras: La combinación de límites debe ser única"),
    ]

    col_w = 168
    col_gap = 10
    total_cw = len(approaches) * col_w + (len(approaches) - 1) * col_gap
    sx = (w - total_cw) / 2

    max_code_h = max(len(a[2]) for a in approaches) * 17 + 14
    py = 101 + max_code_h + 12
    box_h = 80
    for i, (title, fill, code_lines, pro, con) in enumerate(approaches):
        x = sx + i * (col_w + col_gap)

        svg.rect(x, 55, col_w, 38, fill=fill, rx=CORNER_R)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(x + col_w / 2, 74, title, size=FS_TINY, bold=True, fill=tc)

        code_h = len(code_lines) * 17 + 14
        svg.rect(x, 101, col_w, code_h, fill='code_bg', stroke='dark', rx=3)
        for j, line in enumerate(code_lines):
            svg.mono(x + 6, 117 + j * 17, line, size=11)

        svg.rect(x + 4, py, col_w - 8, box_h, fill='white', stroke='dark', rx=3)
        svg.text_block(x + col_w / 2, py + 5, col_w - 18,
                       [(pro, 'text'), (con, 'text_light')], size=FS_TINY - 2,
                       min_size=9, line_gap=1.18)

    chart_y = py + box_h + 22
    svg.line(30, chart_y, w - 30, chart_y, color='dark', dash=True)
    svg.text(w / 2, chart_y + 24, "Tasa real de adopción", size=FS_BODY, bold=True)

    adoptions = [
        ("Cadena ant.→nueva", "Claude Code", 0.85, 'dark'),
        ("Ubicación por núm. línea", "Escenarios integración profunda IDE", 0.50, 'medium'),
        ("Diff + Apply", "Cursor", 0.40, 'light'),
        ("Coincidencia inicio-fin", "Algunas soluciones personalizadas", 0.30, 'light'),
        ("Comandos Vim", "Soluciones experimentales", 0.15, 'code_bg'),
    ]
    bar_x, bar_w_max = 250, 480
    by = chart_y + 48
    for label, products, ratio, fill in adoptions:
        svg.text(bar_x - 10, by + 14, label, size=FS_TINY, anchor='end', bold=True)
        bw = bar_w_max * ratio
        svg.rect(bar_x, by, bw, 28, fill=fill, rx=3)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(bar_x + bw / 2, by + 14, products, size=FS_TINY, fill=tc)
        by += 38

    svg.save(os.path.join(OUT, 'fig5-4.svg'))


def fig5_5():
    """PPT generation pipeline — Figure 5-5."""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Generación de PPT: colaboración Proposer-Reviewer", size=FS_TITLE, bold=True)

    svg.rect(20, 60, 350, 280, fill='white', stroke='border', dash=True)
    svg.text(195, 82, "Agente Proponente (Proposer)", size=FS_BODY, bold=True)

    svg.text(40, 110, "Entrada: Artículo / contenido", size=FS_SMALL, anchor='start', bold=True)
    svg.rect(30, 125, 330, 24, fill='code_bg', stroke='dark', rx=3)
    svg.mono(38, 137, "paper.pdf → Extraer secciones/argumentos/imgs", size=11)

    svg.text(40, 168, "Salida: Markdown Slidev", size=FS_SMALL, anchor='start', bold=True)
    code_lines = [
        "---",
        "layout: two-cols",
        "---",
        "# Arquitectura Transformer",
        "::left::",
        "- Mecanismo self-attention",
        "- Atención multicabeza",
        "::right::",
        "<img src=\"fig3.png\" />",
    ]
    ch = svg.code_block(30, 182, 330, code_lines, font_size=10, line_h=14)

    svg.rect(510, 60, 350, 280, fill='white', stroke='border', dash=True)
    svg.text(685, 82, "Agente Revisor (Reviewer)", size=FS_BODY, bold=True)

    svg.text(520, 110, "Paso 1: Renderizar capturas de pantalla", size=FS_SMALL, anchor='start', bold=True)
    svg.rect(520, 125, 330, 50, fill='light')
    svg.text(685, 142, "slidev export --per-slide", size=FS_TINY, fill='text_light')
    svg.text(685, 160, "→ slide-01.png, slide-02.png ...", size=FS_TINY, fill='text_light')

    svg.text(520, 192, "Paso 2: Revisión con LLM visual", size=FS_SMALL, anchor='start', bold=True)
    critique_lines = [
        "Dimensiones de revisión:",
        "  ✓ Límite de desborde de texto",
        "  ✓ Distribución muy ajustada",
        "  ✓ Tamaño de imagen adecuado",
        "  ✗ Diap. 3: El texto desborda la col. derecha",
        "  ✗ Diap. 7: Contenido demasiado denso",
    ]
    svg.rect(520, 208, 330, len(critique_lines) * 16 + 12, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(critique_lines):
        svg.mono(528, 222 + j * 16, line, size=10)

    svg.arrow(370, 200, 508, 150, label="Código Slidev")
    svg.arrow(508, 300, 370, 260, label="Sugerencias de cambio", dash=True)

    _pill(svg, 395, 220, 100, 24, "Iterar 2-3 rondas", fill='dark', font_size=11, bold=True)

    svg.line(30, 365, w - 30, 365, color='dark', dash=True)
    svg.text(w / 2, 388, "¿Por qué separar en Agentes Proponente y Revisor?", size=FS_BODY, bold=True)

    reasons = [
        ("Problema Agente único", [
            "Decenas de capturas → desborde de contexto",
            "Mezcla código + imágenes → distracción",
        ]),
        ("Ventajas de separación", [
            "Revisor con contexto indep. → solo imagen + código",
            "Proponente enfocado → solo recibe sugerencias",
        ]),
        ("Impacto real", [
            "Reduce significativamente el uso de contexto",
            "Aumenta notablemente la precisión de corrección",
        ]),
    ]
    rx = 30
    for title, items in reasons:
        svg.rect(rx, 405, 270, 130, fill='light')
        svg.text(rx + 135, 425, title, size=FS_SMALL, bold=True)
        for j, item in enumerate(items):
            svg.text(rx + 135, 450 + j * 24, item, size=FS_TINY, fill='text_light')
        rx += 290

    svg.save(os.path.join(OUT, 'fig5-5.svg'))


def fig5_6():
    """Experiment 5.6+5.7 — Figure 5-6."""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experimento 5.6+5.7: Artículo → PPT → Video de clase", size=FS_TITLE, bold=True)

    stages_top = [
        ("Entrada PDF", 'medium', [
            "paper.pdf",
            "Parsear estructura doc.",
            "Extraer ref. imágenes",
        ]),
        ("Planificación contenido", 'light', [
            "Estructura 10-20 págs",
            "Extraer arg. principales",
            "Asignar imágenes",
        ]),
        ("Generación Slidev", 'light', [
            "Generar pág. por pág.",
            "layout: two-cols",
            "Código + disposición img",
        ]),
        ("Control de renderizado", 'medium', [
            "export --per-slide",
            "Revisión LLM visual",
            "Detección desborde",
        ]),
        ("Corrección iterativa", 'light', [
            "Revisor→Proponente",
            "Modificar código Slidev",
            "Rerenderizar y verificar",
        ]),
    ]

    sw = 155
    sgap = 10
    total = len(stages_top) * sw + (len(stages_top) - 1) * sgap
    sx = (w - total) / 2

    svg.text(w / 2, 60, "Fase 1: Generación de PPT (Proponente-Revisor)", size=FS_SMALL, bold=True, fill='text_light')
    for i, (title, fill, details) in enumerate(stages_top):
        x = sx + i * (sw + sgap)
        svg.rect(x, 72, sw, 130, fill=fill)
        svg.text(x + sw / 2, 92, title, size=FS_SMALL, bold=True)
        svg.line(x + 8, 104, x + sw - 8, 104, color='dark')
        for j, line in enumerate(details):
            svg.mono(x + 8, 120 + j * 20, line, size=10)
        if i < len(stages_top) - 1:
            svg.arrow(x + sw + 2, 72 + 65, x + sw + sgap - 2, 72 + 65)

    svg.arrow(w / 2, 202, w / 2, 240)
    svg.text(w / 2 + 60, 222, "PPT completado", size=FS_SMALL, fill='text_light')

    svg.text(w / 2, 255, "Fase 2: Síntesis de video", size=FS_SMALL, bold=True, fill='text_light')

    stages_bot = [
        ("Captura por página", 'medium', [
            "slide-01.png",
            "slide-02.png",
            "...",
        ]),
        ("Generación guion", 'light', [
            "Guion en lenguaje natural",
            "Narración por página",
            "Narrativa de guiado",
        ]),
        ("Síntesis TTS", 'light', [
            "Texto → audio",
            "speech-01.mp3",
            "speech-02.mp3",
        ]),
        ("Sincronía audio-video", 'medium', [
            "Síntesis ffmpeg",
            "Coincidir dur. audio",
            "Efectos de transición",
        ]),
        ("Video final", 'dark', [
            "output.mp4",
            "5-15 minutos",
            "Salida audio + imagen",
        ]),
    ]

    for i, (title, fill, details) in enumerate(stages_bot):
        x = sx + i * (sw + sgap)
        svg.rect(x, 268, sw, 130, fill=fill)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(x + sw / 2, 288, title, size=FS_SMALL, bold=True, fill=tc)
        svg.line(x + 8, 300, x + sw - 8, 300, color='dark')
        for j, line in enumerate(details):
            fc = 'white' if fill in ('dark', 'darker') else 'text'
            svg.mono(x + 8, 316 + j * 20, line, size=10, fill=fc)
        if i < len(stages_bot) - 1:
            svg.arrow(x + sw + 2, 268 + 65, x + sw + sgap - 2, 268 + 65)

    svg.line(30, 420, w - 30, 420, color='dark', dash=True)
    svg.text(w / 2, 440, "Criterios de aceptación", size=FS_BODY, bold=True)

    criteria = [
        ("PPT", "10-20 págs · Cubre contribuciones principales · ≥3 gráficos originales"),
        ("Render", "Cero desborde de texto · Disposición adecuada · Armonía texto-imagen"),
        ("Video", "5-15 minutos · Sincronía audio-video · Narrativa coherente"),
    ]
    cy = 462
    for label, desc in criteria:
        _pill(svg, 180, cy, 92, 26, label, fill='dark', font_size=12, bold=True)
        svg.text(285, cy + 13, desc, size=FS_TINY, fill='text_light', anchor='start')
        cy += 30

    svg.save(os.path.join(OUT, 'fig5-6.svg'))


def fig5_7():
    """Experiment 5.10 — Figure 5-7."""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experimento 5.10: Diagnóstico inteligente de registros de producción", size=FS_TITLE, bold=True)

    svg.rect(20, 60, 250, 160, fill='white', stroke='border', dash=True)
    svg.text(145, 82, "① Recolección de registros", size=FS_BODY, bold=True)
    log_lines = [
        "trajectory_001.json:",
        '  {"role":"user","content":',
        '   "cancelar pedido 12345"}',
        '  {"role":"assistant",',
        '   "tool_call":"cancel_order"}',
        '  {"role":"tool","result":',
        '   "ERROR: sin seguro"}',
        '  → Agente no informó la razón al usuario',
    ]
    svg.rect(30, 98, 230, len(log_lines) * 14 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(log_lines):
        svg.mono(38, 112 + j * 14, line, size=9)

    svg.arrow(270, 140, 310, 140)

    svg.rect(310, 60, 260, 160, fill='white', stroke='border', dash=True)
    svg.text(440, 82, "② Análisis de LLM", size=FS_BODY, bold=True)
    analysis = [
        "Entrada: traza + doc. arquit. + PRD",
        "",
        "Dimensiones de análisis:",
        "  - ¿Flujo de ejec. cumple lo esperado?",
        "  - ¿Llamadas a herramientas correctas?",
        "  - ¿Manejo de errores adecuado?",
        "  - ¿Experiencia de usuario satisfactoria?",
        "",
        "→ Identificar paso y módulo con desviación",
    ]
    for j, line in enumerate(analysis):
        svg.mono(320, 100 + j * 14, line, size=10)

    svg.arrow(570, 140, 610, 140)

    svg.rect(610, 60, 250, 160, fill='white', stroke='border', dash=True)
    svg.text(735, 82, "③ Informe estructurado", size=FS_BODY, bold=True)
    report = [
        "Informe de problema:",
        "  Prioridad: P1 (Riesgo pérdida usuario)",
        "  Módulo: cancellation_handler",
        "  Descripción: Tras fallo en cancelación,",
        "    no se explica motivo ni alternativas",
        "  Recomendación: Agregar explicación",
        "    y guía para compra de seguro",
    ]
    svg.rect(620, 98, 230, len(report) * 14 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(report):
        svg.mono(628, 112 + j * 14, line, size=9)

    svg.arrow(w / 2, 220, w / 2, 260)

    svg.rect(60, 260, 370, 160, fill='white', stroke='border', dash=True)
    svg.text(245, 282, "④ Generación caso de prueba de regresión", size=FS_BODY, bold=True)
    test_code = [
        "def test_cancel_no_insurance():",
        '  """Traza #001, Rondas 3-5"""',
        "  # Replay: El usuario pide cancelar vuelo",
        "  resp = agent.run(",
        '    "cancelar pedido 12345")',
        "  # Verificar: Debe explicarse el motivo",
        '  assert "seguro" in resp.text',
        '  assert "alternativa" in resp.text',
        "  # Verificar: No debe devolver error directo",
        '  assert "ERROR" not in resp.text',
    ]
    svg.rect(70, 298, 350, len(test_code) * 14 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(test_code):
        svg.mono(78, 312 + j * 14, line, size=10)

    svg.arrow(430, 340, 470, 340)

    svg.rect(470, 260, 380, 160, fill='white', stroke='border', dash=True)
    svg.text(660, 282, "⑤ Creación automática de Issue en GitHub", size=FS_BODY, bold=True)
    issue = [
        "gh issue create \\",
        '  --title "P1: Falta guía al usuario',
        '    en cancelación" \\',
        '  --body "**Problema**: El Agente devuelve',
        '    error directo sin explicar motivo...',
        '    **Traza**: #001 Rondas 3-5',
        '    **Prueba**: test_cancel_..." \\',
        '  --assignee @backend-team',
    ]
    svg.rect(480, 298, 360, len(issue) * 14 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(issue):
        svg.mono(488, 312 + j * 14, line, size=10)

    svg.rect(100, 445, w - 200, 44, fill='dark')
    svg.text(w / 2, 460, "Automatización de extremo a extremo: Registro → Análisis → Informe → Prueba → Issue", size=FS_BODY, fill='white', bold=True)
    svg.text(w / 2, 480, "Integración GitHub con MCP · Verificación de replay automático en marco de pruebas", size=FS_TINY, fill='white')

    svg.text(w / 2, 530, "Reduce el costo de diagnóstico manual de horas a minutos", size=FS_SMALL, fill='darker', bold=True)

    svg.save(os.path.join(OUT, 'fig5-7.svg'))


def fig5_8():
    """Dynamic form generation flow — Figure 5-8."""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Generación dinámica de formularios: aclaración estructurada de intención", size=FS_TITLE, bold=True)

    svg.rect(20, 60, 200, 60, fill='medium')
    svg.text(120, 82, "Entrada del usuario", size=FS_SMALL, bold=True)
    svg.text(120, 100, '"Quiero reservar un vuelo a Pekín"', size=FS_TINY, fill='text_light')

    svg.arrow(220, 90, 260, 90)

    svg.rect(260, 55, 260, 140, fill='white', stroke='border', dash=True)
    svg.text(390, 75, "Análisis LLM → Generar código de formulario", size=FS_SMALL, bold=True)
    form_code = [
        '<form id="clarify">',
        ' <input type="text"',
        '  name="from" label="Ciudad origen"/>',
        ' <input type="date"',
        '  name="depart" label="Fecha salida"/>',
        ' <select name="type">',
        '  <option>Solo ida</option>',
        '  <option>Ida y vuelta</option>',
        ' </select>',
        '</form>',
    ]
    svg.rect(270, 90, 240, len(form_code) * 13 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(form_code):
        svg.mono(276, 103 + j * 13, line, size=9)

    svg.arrow(520, 130, 560, 130)

    svg.rect(560, 55, 300, 200, fill='white', stroke='border')
    svg.text(710, 75, "Interfaz de formulario renderizada", size=FS_SMALL, bold=True)

    fields = [
        ("Ciudad Origen", "Shanghái", 95),
        ("Fecha Salida", "2025-08-15", 135),
        ("Tipo de Viaje", "Ida y vuelta ▾", 175),
        ("Fecha Regreso", "2025-08-22", 215),
    ]
    for label, value, fy in fields:
        svg.text(580, fy, label, size=FS_TINY, anchor='start', bold=True)
        svg.rect(660, fy - 12, 180, 24, fill='code_bg', stroke='dark', rx=3)
        svg.mono(668, fy, value, size=11)

    _pill(svg, 660, 238, 80, 26, "Enviar", fill='dark', font_size=FS_SMALL, bold=True)

    svg.arrow(710, 268, 710, 300)
    svg.rect(560, 300, 300, 110, fill='white', stroke='border', dash=True)
    svg.text(710, 318, "Respuesta JSON estructurada", size=FS_SMALL, bold=True)
    json_lines = [
        '{"from": "Shanghái",',
        ' "depart": "2025-08-15",',
        ' "type": "Ida y vuelta",',
        ' "return": "2025-08-22"}',
    ]
    svg.rect(570, 330, 280, len(json_lines) * 16 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(json_lines):
        svg.mono(578, 344 + j * 16, line, size=11)

    svg.arrow(560, 390, 400, 440)

    svg.rect(100, 430, 500, 50, fill='medium')
    svg.text(350, 448, "El Agente continúa la ejecución con parámetros completos", size=FS_BODY, bold=True)
    svg.text(350, 468, "search_flights(from='Shanghái', to='Pekín', depart='2025-08-15', ...)", size=FS_TINY, fill='text_light')

    svg.rect(20, 280, 250, 140, fill='light')
    svg.text(145, 300, "Comparación: Texto vs Formulario", size=FS_SMALL, bold=True)
    comp = [
        "Preguntas en texto: 10 rondas",
        "  P1: ¿Origen? R: Shanghái",
        "  P2: ¿Fecha? R: 15 de agosto",
        "  P3: ¿Ida o vuelta? ...",
        "",
        "Formulario dinámico: 1 envío",
        "  Toda la info se junta a la vez",
        "  Lógica en cascada automática",
    ]
    for j, line in enumerate(comp):
        svg.mono(30, 318 + j * 13, line, size=10)

    svg.text(w / 2, 510, "El código del formulario se genera dinámicamente por el LLM → Lógica en cascada: al elegir \"Ida y vuelta\", la fecha de regreso se muestra automáticamente", size=FS_SMALL, fill='darker')

    svg.save(os.path.join(OUT, 'fig5-8.svg'))


def fig5_9():
    """SQL Query Agent — Figure 5-9."""
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Agente de consultas SQL: Modo Artefacto vs Modo Tradicional", size=FS_TITLE, bold=True)

    svg.rect(20, 55, w - 40, 200, fill='white', stroke='border', dash=True)
    svg.text(60, 78, "Modo tradicional: los datos pasan por el LLM (ineficiente)", size=FS_BODY, bold=True, anchor='start')
    _pill(svg, w - 110, 65, 80, 24, "✗ Ineficiente", fill='dark', font_size=12, bold=True)

    trad_steps = [
        ("Usuario", 'medium', '"¿Personal por departamento?"'),
        ("LLM", 'light', "Generar SQL"),
        ("DB", 'medium', "Ejecutar\\nconsulta"),
        ("LLM", 'light', "Leer 5000\\nlíneas"),
        ("Usuario", 'medium', "Explicación\\nen texto"),
    ]
    tsx = 60
    for i, (name, fill, desc) in enumerate(trad_steps):
        svg.rect(tsx, 100, 130, 60, fill=fill)
        svg.text(tsx + 65, 118, name, size=FS_SMALL, bold=True)
        for j, line in enumerate(desc.split('\\n')):
            svg.text(tsx + 65, 138 + j * 16, line, size=FS_TINY, fill='text_light')
        if i < len(trad_steps) - 1:
            svg.arrow(tsx + 130, 130, tsx + 150, 130)
        tsx += 155

    svg.rect(60, 175, w - 120, 30, fill='code_bg', stroke='dark', rx=3)
    svg.mono(70, 190, "Problema: Copiar datos en el LLM es propenso a errores · consume muchos tokens · alta latencia", size=12)

    svg.line(30, 265, w - 30, 265, color='dark', dash=True)

    svg.rect(20, 275, w - 40, 280, fill='white', stroke='border', dash=True)
    svg.text(60, 298, "Modo Artefacto: los datos van directamente al frontend (eficiente)", size=FS_BODY, bold=True, anchor='start')
    _pill(svg, w - 110, 285, 80, 24, "✓ Eficiente", fill='medium', font_size=12, bold=True)

    svg.rect(40, 315, 250, 120, fill='light')
    svg.text(165, 335, "El LLM solo genera código", size=FS_SMALL, bold=True)
    sql_code = [
        "build_artifact(",
        '  type="sql",',
        '  code="SELECT dept,',
        '    COUNT(*) as cnt',
        '    FROM employees',
        '    GROUP BY dept")',
    ]
    svg.rect(50, 345, 230, len(sql_code) * 14 + 8, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(sql_code):
        svg.mono(58, 358 + j * 14, line, size=10)

    svg.arrow(290, 380, 340, 380)

    svg.rect(340, 315, 250, 120, fill='medium')
    svg.text(465, 335, "El frontend ejecuta directo", size=FS_SMALL, bold=True)
    svg.rect(350, 348, 230, 75, fill='code_bg', stroke='dark', rx=3)
    table = [
        "┌────────┬──────┐",
        "│ dept   │ cnt  │",
        "├────────┼──────┤",
        "│ Dpto. I+D │  42  │",
        "│ Dpto. Mkt │  28  │",
        "└────────┴──────┘",
    ]
    for j, line in enumerate(table):
        svg.mono(358, 360 + j * 12, line, size=9)

    svg.arrow(590, 380, 640, 380)

    svg.rect(640, 315, 210, 120, fill='light')
    svg.text(745, 335, "Artefacto de visualización", size=FS_SMALL, bold=True)
    svg.text(745, 355, "Segundo artefacto:", size=FS_TINY, fill='text_light')
    svg.rect(650, 365, 190, 60, fill='code_bg', stroke='dark', rx=3)
    svg.mono(658, 380, "build_artifact(", size=10)
    svg.mono(658, 394, '  type="chart",', size=10)
    svg.mono(658, 408, '  code="bar(data)")', size=10)

    svg.rect(180, 450, 520, 45, fill='dark')
    svg.text(440, 465, "Flujo de datos: DB → Frontend → Visualización (omite por completo el LLM)", size=FS_BODY, fill='white', bold=True)
    svg.text(440, 483, "El LLM solo se encarga de generar código, no de transferir datos", size=FS_TINY, fill='white')

    svg.arrow_curved(465, 435, 745, 435, curve=25, dash=True, color='dark')

    svg.save(os.path.join(OUT, 'fig5-9.svg'))


def fig5_10():
    """Agent Bootstrap Loop — Figure 5-10."""
    w, h = 880, 555
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Bootstrap del Agente: del código a la autorreplicación", size=FS_TITLE, bold=True)

    stages = [
        ("Polvo → Estrella", "Leyes de la física"),
        ("Estrella → Planeta", "Acumulación gravitacional"),
        ("Planeta → Vida", "Autorreplicación del ADN"),
        ("Vida → Agente", "Bootstrap por código"),
    ]
    sx = 60
    for i, (stage, mechanism) in enumerate(stages):
        fill = 'dark' if i == 3 else ('medium' if i == 2 else 'light')
        svg.rect(sx, 55, 180, 50, fill=fill)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(sx + 90, 72, stage, size=FS_SMALL, bold=True, fill=tc)
        svg.text(sx + 90, 92, mechanism, size=FS_TINY, fill='white' if fill == 'dark' else 'text_light')
        if i < len(stages) - 1:
            svg.arrow(sx + 180, 80, sx + 195, 80)
        sx += 200

    svg.line(30, 120, w - 30, 120, color='dark', dash=True)

    svg.rect(30, 135, 400, 70, fill='light')
    svg.text(230, 155, "Autorreplicación del ADN: mutación aleatoria + selección natural", size=FS_SMALL, bold=True)
    svg.text(230, 177, "No se entiende a sí mismo · Sin cambio dirigido · 3.7 mil millones de años de ensayo y error", size=FS_TINY, fill='text_light')

    svg.rect(450, 135, 400, 70, fill='dark')
    svg.text(650, 155, "Bootstrap del Agente: comprensión de código + diseño dirigido", size=FS_SMALL, bold=True, fill='white')
    svg.text(650, 177, "Entiende su mecanismo · Crea con propósito · Hereda las mejores prácticas", size=FS_TINY, fill='white')

    svg.rect(20, 225, 390, 295, fill='white', stroke='border', dash=True)
    svg.text(215, 248, "Agente original (su propio código)", size=FS_BODY, bold=True)

    svg.rect(30, 265, 175, 124, fill='light')
    svg.text(118, 285, "Prompt del sistema", size=FS_SMALL, bold=True)
    svg.text(40, 308, "Eres un agente de at. cliente de aerolínea", size=12, anchor='start')
    svg.text(40, 326, "Reglas de cancelación: ...", size=12, anchor='start')
    svg.text(40, 344, "Reglas de transferencia: ...", size=12, anchor='start')
    svg.text(40, 362, "Herramienta: cancel_order", size=12, anchor='start')

    svg.rect(215, 265, 185, 124, fill='light')
    svg.text(308, 285, "Código del marco", size=FS_SMALL, bold=True)
    svg.mono(225, 308, "loop:", size=12)
    svg.mono(225, 326, "  msg = llm(ctx)", size=12)
    svg.mono(225, 344, "  if tool_call:", size=12)
    svg.mono(225, 362, "    exec(tool)", size=12)

    svg.rect(30, 400, 370, 54, fill='code_bg', stroke='dark', rx=4)
    svg.text(215, 419, "Def. herramienta + integración MCP + formato mensaje", size=FS_SMALL)
    svg.text(215, 438, "Implementación de alta calidad verificada", size=FS_TINY, fill='text_light')

    svg.text(440, 215, "Copiar + modificar", size=FS_TINY, fill='text_light', bold=True)
    svg.arrow(410, 375, 470, 375)

    svg.rect(470, 225, 390, 295, fill='white', stroke='border', dash=True)
    svg.text(665, 248, "Nuevo Agente (tras modificaciones dirigidas)", size=FS_BODY, bold=True)

    svg.rect(480, 265, 180, 124, fill='medium')
    svg.text(570, 285, "Nuevo prompt del sistema", size=FS_SMALL, bold=True)
    svg.text(490, 308, "Eres un agente de at. cliente de e-commerce", size=12, anchor='start')
    svg.text(490, 326, "Reglas de devolución: ...", size=12, anchor='start')
    svg.text(490, 344, "Consulta de envío: ...", size=12, anchor='start')
    svg.text(490, 362, "Herramienta: refund_order", size=12, anchor='start')

    svg.rect(670, 265, 180, 124, fill='light')
    svg.text(760, 285, "Código de marco heredado", size=FS_SMALL, bold=True)
    svg.mono(680, 308, "loop:", size=12)
    svg.mono(680, 326, "  msg = llm(ctx)", size=12)
    svg.mono(680, 344, "  if tool_call:", size=12)
    svg.mono(680, 362, "    exec(tool)", size=12)

    svg.rect(480, 400, 370, 54, fill='code_bg', stroke='dark', rx=4)
    svg.text(665, 419, "Nuevas herramientas + nueva lógica de negocio", size=FS_SMALL)
    svg.text(665, 438, "El marco arquitectónico se hereda totalmente → calidad garantizada", size=FS_TINY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig5-10.svg'))


def fig5_11():
    """Experiment 5.14 — Figure 5-11."""
    w, h = 880, 610
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experimento 5.14: Un Agente capaz de crear Agentes", size=FS_TITLE, bold=True)

    svg.rect(30, 60, 280, 55, fill='medium')
    svg.text(170, 80, "Requisito del usuario", size=FS_SMALL, bold=True)
    svg.text(170, 98, '"Crear un Agente de at. cliente para devoluciones"', size=FS_TINY, fill='text_light')

    svg.arrow(170, 115, 170, 145)

    svg.rect(20, 145, 840, 230, fill='white', stroke='border', dash=True)
    svg.text(440, 168, "Meta-Agente (Agente de programación)", size=FS_BODY, bold=True)

    svg.rect(35, 185, 190, 170, fill='light')
    svg.text(130, 205, "① Leer código referencia", size=FS_SMALL, bold=True)
    svg.mono(45, 228, "read_file:", size=12)
    svg.mono(45, 248, "  agent.py", size=12)
    svg.mono(45, 268, "  tools/*.py", size=12)
    svg.mono(45, 288, "  system_prompt.md", size=12)
    svg.mono(45, 308, "  config.yaml", size=12)
    svg.text(45, 332, "→ Entender patrones arquit.", size=12, anchor='start', fill='text_light')

    svg.arrow(225, 270, 248, 270)

    svg.rect(248, 185, 190, 170, fill='light')
    svg.text(343, 205, "② Copiar esqueleto", size=FS_SMALL, bold=True)
    svg.mono(258, 228, "cp -r reference/", size=12)
    svg.mono(258, 248, "  → new_agent/", size=12)
    svg.text(258, 278, "Conservar:", size=12, anchor='start', fill='text_light')
    svg.text(258, 298, "  Marco del bucle del Agente", size=12, anchor='start', fill='text_light')
    svg.text(258, 318, "  Formato mens. / opt. KV", size=12, anchor='start', fill='text_light')

    svg.arrow(438, 270, 461, 270)

    svg.rect(461, 185, 190, 170, fill='medium')
    svg.text(556, 205, "③ Cambios dirigidos", size=FS_SMALL, bold=True)
    svg.mono(471, 228, "edit_file:", size=12)
    svg.mono(471, 248, "  system_prompt.md", size=12)
    svg.text(471, 268, "  → Reglas devolución e-comm.", size=12, anchor='start', fill='text_light')
    svg.mono(471, 290, "  tools/refund.py", size=12)
    svg.text(471, 310, "  → Agregar herramienta", size=12, anchor='start', fill='text_light')
    svg.mono(471, 332, "  config.yaml", size=12)

    svg.arrow(651, 270, 674, 270)

    svg.rect(674, 185, 175, 170, fill='light')
    svg.text(761, 205, "④ Prueba de validación", size=FS_SMALL, bold=True)
    svg.mono(684, 228, "bash:", size=12)
    svg.mono(684, 248, "  python agent.py", size=12)
    svg.text(684, 270, "  → Iniciar nuevo Agente", size=12, anchor='start', fill='text_light')
    svg.text(684, 290, "  → Enviar mensajes prueba", size=12, anchor='start', fill='text_light')
    svg.text(684, 310, "  → Revisar llamadas herram.", size=12, anchor='start', fill='text_light')
    svg.text(684, 330, "  → Validar flujo chat", size=12, anchor='start', fill='text_light')

    svg.arrow(w / 2, 375, w / 2, 410)

    svg.rect(115, 410, 700, 90, fill='white', stroke='border', dash=True)
    svg.text(465, 432, "Nuevo Agente producido", size=FS_BODY, bold=True)

    outputs = [
        ("system_prompt.md", "Reglas devolución e-commerce"),
        ("tools/refund.py", "Herramientas devolución/consulta"),
        ("agent.py", "Código de marco heredado"),
        ("config.yaml", "Configuración modelo/parámetros"),
    ]
    ox = 135
    for fname, desc in outputs:
        svg.rect(ox, 448, 170, 42, fill='light')
        svg.mono(ox + 85, 462, fname, size=10, anchor='middle')
        svg.text(ox + 85, 480, desc, size=FS_TINY, fill='text_light')
        ox += 178

    svg.line(30, 515, w - 30, 515, color='dark', dash=True)
    svg.rect(60, 530, 350, 54, fill='light')
    svg.text(235, 549, "Generación desde cero: faltan mejores prácticas", size=FS_SMALL, bold=True)
    svg.text(235, 571, "Gestión azarosa de contexto · Diseño no estándar · API obsoleta", size=FS_TINY, fill='text_light')

    svg.rect(470, 530, 350, 54, fill='dark')
    svg.text(645, 549, "Adaptación desde ejemplo: hereda las mejores prácticas", size=FS_SMALL, bold=True, fill='white')
    svg.text(645, 571, "Formato estándar · Diseño herramientas estándar · API moderna", size=FS_TINY, fill='white')

    svg.save(os.path.join(OUT, 'fig5-11.svg'))


def main():
    os.makedirs(OUT, exist_ok=True)
    figs = [
        fig5_1, fig5_2, fig5_3, fig5_4, fig5_5, fig5_6,
        fig5_7, fig5_8, fig5_9, fig5_10, fig5_11,
    ]
    for fn in figs:
        fn()
        print(f"  ✓ {fn.__name__}: {fn.__doc__}")
    print(f"\nGenerated {len(figs)} figures in {OUT}/")


if __name__ == '__main__':
    main()
