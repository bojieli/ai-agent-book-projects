"""Generate all Chapter 2 figures in Spanish."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    SVG, FS_TITLE, FS_BODY, FS_SMALL, FS_TINY,
)

OUT = os.path.join(os.path.dirname(__file__), 'images')


def fig2_1():
    """Context window composition — caption Figure 2-1."""
    W, H = 820, 620
    s = SVG(W, H)

    s.text(410, 30, 'Vista general de los componentes de la ventana de contexto', size=FS_TITLE, bold=True)

    lx, lw = 40, 700
    layers = [
        ('Prompt del sistema', 'medium', [
            '"Eres un asistente útil. Tus respuestas deben ser CONCISAS."',
            '"Usa herramientas cuando el usuario solicite información en tiempo real."',
        ]),
        ('Definiciones de herramientas', 'light', [
            '{"name": "web_search", "description": "Buscar en la web",',
            ' "parameters": {"query": {"type": "string"}}}',
        ]),
        ('Historial de conversación', 'light', [
            'user: "¿Cómo está el clima hoy en Pekín?"',
            'assistant: [tool_call] → get_weather("Pekín")',
            'tool: {"temp": "23°C", "conditions": "despejado"}',
        ]),
        ('Traza de razonamiento', '#e8e8e8', [
            '<think>El usuario pregunta por el clima. Ya tengo el resultado,',
            'puedo resumir y responder sin llamar de nuevo a la herramienta.</think>',
        ]),
        ('Posición actual de generación →', 'white', [
            'assistant: "Pekín está despejado hoy, temperatura 23°C..."  ← LLM generando',
        ]),
    ]

    y = 60
    for title, fill, snippets in layers:
        block_h = 30 + len(snippets) * 22 + 10
        s.rect(lx, y, lw, block_h, fill=fill)
        s.text(lx + 15, y + 20, title, size=FS_BODY, bold=True, anchor='start')
        for i, line in enumerate(snippets):
            s.mono(lx + 25, y + 42 + i * 22, line, size=FS_TINY)
        y += block_h + 8

    brace_top = 60
    brace_bot = y - 8
    s.brace_right(lx + lw + 8, brace_top, brace_bot)
    s.text(lx + lw + 15, (brace_top + brace_bot) / 2 - 12, 'Ventana de', size=FS_BODY, bold=True, anchor='start')
    s.text(lx + lw + 15, (brace_top + brace_bot) / 2 + 12, 'Contexto', size=FS_BODY, bold=True, anchor='start')

    s.rect(100, y + 15, 620, 50, fill='code_bg', stroke='dark', rx=4)
    s.text(410, y + 32, 'Tamaño de ventana: Qwen3 = 32K tokens | Claude = 200K | Gemini = 2M', size=FS_SMALL)
    s.text(410, y + 52, 'Todo el contenido se serializa en el flujo de tokens → procesado por la atención Transformer', size=FS_SMALL, fill='text_light')

    s.save(f'{OUT}/fig2-1.svg')


def fig2_2():
    """Local LLM Tool Calling Architecture — Figure 2-2."""
    W, H = 820, 540
    s = SVG(W, H)

    s.text(410, 30, 'Experimento 2.1: Arquitectura de llamada a herramientas con LLM local', size=FS_TITLE, bold=True)

    # Hardware box (left)
    s.group_box(30, 65, 220, 130, 'Hardware local')
    s.box(50, 100, 180, 35, 'Apple M2 / 16GB', fill='light', font_size=FS_SMALL)
    s.box(50, 145, 180, 35, 'Motor de inferencia MLX', fill='light', font_size=FS_SMALL)

    # Model box (center)
    s.rect(290, 65, 240, 130, fill='medium')
    s.text(410, 95, 'Qwen3-0.6B', size=FS_BODY, bold=True)
    s.text(410, 120, '0.6B parámetros · cuantización Q4', size=FS_SMALL, fill='text_light')
    s.text(410, 145, '> 100 tokens/seg', size=FS_SMALL, fill='text_light')
    s.text(410, 170, 'ReAct + Llamada a herramientas', size=FS_SMALL)

    # Tool registry (right)
    s.group_box(570, 65, 220, 130, 'Registro de herramientas')
    s.box(590, 100, 180, 35, 'get_current_time', fill='code_bg', font_size=FS_SMALL)
    s.box(590, 145, 180, 35, 'get_temperature', fill='code_bg', font_size=FS_SMALL)

    s.arrow(252, 130, 288, 130)
    s.arrow(532, 122, 568, 122)
    s.arrow(568, 138, 532, 138)

    # ReAct loop (below)
    s.group_box(50, 220, 720, 290, 'Bucle ReAct')

    s.rect(80, 260, 300, 40, fill='light')
    s.text(90, 280, 'user: "¿Qué hora es en Vancouver y qué clima hace?"', size=FS_TINY, anchor='start')

    s.rect(80, 310, 300, 55, fill='#e8e8e8')
    s.text(90, 328, '<think>', size=FS_TINY, anchor='start', bold=True)
    s.text(90, 348, 'Se deben llamar a get_current_time', size=FS_TINY, anchor='start')
    s.text(90, 363, 'y get_temperature', size=FS_TINY, anchor='start')
    s.arrow(230, 302, 230, 308)

    s.rect(80, 375, 300, 50, fill='code_bg', stroke='dark', rx=4)
    s.mono(90, 393, '<tool_call>', size=FS_TINY)
    s.mono(90, 411, '{"name":"get_current_time",...}', size=FS_TINY)
    s.arrow(230, 367, 230, 373)

    s.rect(80, 435, 300, 40, fill='light')
    s.text(90, 455, '<tool_response> {"time":"05:18","temp":"13.2°C"}', size=FS_TINY, anchor='start')
    s.arrow(230, 427, 230, 433)

    s.arrow_curved(80, 455, 80, 280, curve=-40, color='dark')
    s.text(30, 367, 'Continuar bucle', size=FS_TINY, fill='text_light', bold=True)

    s.rect(430, 280, 320, 55, fill='medium')
    s.text(440, 298, 'Resultado final:', size=FS_SMALL, bold=True, anchor='start')
    s.text(440, 318, '"Vancouver: 05:18, 13.2°C,', size=FS_TINY, anchor='start')
    s.text(440, 335, '  despejado, humedad 93%"', size=FS_TINY, anchor='start')

    s.rect(430, 360, 320, 80, fill='code_bg', stroke='dark', rx=4)
    s.text(590, 378, 'Temporización de transmisión', size=FS_SMALL, bold=True)
    s.text(440, 400, '<think>... → oculto, no mostrado al usuario', size=FS_TINY, anchor='start')
    s.text(440, 418, 'texto plano → transmisión en tiempo real', size=FS_TINY, anchor='start')
    s.text(440, 436, '<tool_call> → parsear y ejecutar herramienta', size=FS_TINY, anchor='start')

    s.save(f'{OUT}/fig2-2.svg')


def fig2_3():
    """Chat template token structure — Figure 2-3."""
    W, H = 920, 580
    s = SVG(W, H)

    s.text(W / 2, 30, 'Estructura de tokens de la plantilla de chat', size=FS_TITLE, bold=True)

    lx = 40
    rw = 800

    y = 65
    segments = [
        ('<|im_start|>system', 'darker', 'white', [
            '# Herramientas',
            'Puedes llamar a una o más funciones...',
            '<tools>{"name":"get_weather",...}</tools>',
            '<tool_call>{"name":..., "arguments":...}</tool_call>',
        ]),
        ('<|im_end|>', 'dark', 'white', []),
        ('<|im_start|>user', 'darker', 'white', [
            '"¿Cómo está el clima hoy en Pekín?"',
        ]),
        ('<|im_end|>', 'dark', 'white', []),
        ('<|im_start|>assistant', 'darker', 'white', [
            '<think>Consultar clima, llamar a get_weather</think>',
            '<tool_call>{"name":"get_weather","args":{"city":"Pekín"}}</tool_call>',
        ]),
        ('<|im_end|>', 'dark', 'white', []),
        ('<|im_start|>user', 'darker', 'white', [
            '<tool_response>{"temp":"23°C","sky":"despejado"}</tool_response>',
        ]),
        ('<|im_end|>', 'dark', 'white', []),
        ('<|im_start|>assistant', 'darker', 'white', [
            '← El LLM comienza a generar nuevos tokens desde aquí',
        ]),
    ]

    for tag, tag_fill, _, content_lines in segments:
        if not content_lines:
            s.badge(lx, y, 140, 24, tag, fill=tag_fill, font_size=FS_TINY)
            y += 32
        else:
            total_h = 26 + len(content_lines) * 20 + 8
            s.rect(lx, y, rw, total_h, fill='light')
            s.badge(lx + 5, y + 4, 200, 22, tag, fill=tag_fill, font_size=FS_TINY)
            for i, line in enumerate(content_lines):
                s.mono(lx + 220, y + 8 + i * 20 + 12, line, size=FS_TINY)
            y += total_h + 4

    s.text(lx + rw + 5, 80, 'tokens', size=FS_SMALL, anchor='start', bold=True)
    s.text(lx + rw + 5, 100, 'especiales', size=FS_SMALL, anchor='start', bold=True)

    s.save(f'{OUT}/fig2-3.svg')


def fig2_4():
    """KV Cache Prefix Reuse — Figure 2-4."""
    W, H = 820, 480
    s = SVG(W, H)

    s.text(410, 30, 'Mecanismo de reutilización de prefijo en KV Cache', size=FS_TITLE, bold=True)

    lx = 40
    bw = 740

    s.text(lx, 70, 'Solicitud 1', size=FS_BODY, bold=True, anchor='start')
    s.rect(lx, 85, 380, 40, fill='medium')
    s.text(lx + 190, 105, 'Prompt del sistema + Herramientas (1200 tokens)', size=FS_SMALL)
    s.rect(lx + 385, 85, 180, 40, fill='light')
    s.text(lx + 475, 105, 'user: "¿Clima?"', size=FS_SMALL)
    s.rect(lx + 570, 85, 170, 40, fill='#e8e8e8')
    s.text(lx + 655, 105, '→ generar respuesta', size=FS_SMALL)

    s.text(lx, 155, 'Solicitud 2', size=FS_BODY, bold=True, anchor='start')
    s.rect(lx, 170, 380, 40, fill='medium')
    s.text(lx + 190, 190, 'Prompt sistema + Herramientas (acierto de caché ✓)', size=FS_SMALL)
    s.rect(lx + 385, 170, 180, 40, fill='light')
    s.text(lx + 475, 190, 'user: "¿Hora?"', size=FS_SMALL)
    s.rect(lx + 570, 170, 170, 40, fill='#e8e8e8')
    s.text(lx + 655, 190, '→ generar respuesta', size=FS_SMALL)

    s.arrow(lx + 190, 127, lx + 190, 168, label='Reutilización de KV', color='dark')

    s.text(lx, 245, 'Solicitud 3', size=FS_BODY, bold=True, anchor='start')
    s.text(lx + 85, 245, '(cambió el prompt del sistema)', size=FS_SMALL, anchor='start', fill='text_light')
    s.rect(lx, 260, 400, 40, fill='white', dash=True)
    s.text(lx + 200, 280, 'Sistema + Herramientas + "Hora: 10:30:45"', size=FS_SMALL)
    s.rect(lx + 405, 260, 160, 40, fill='light')
    s.text(lx + 485, 280, 'user: "¿Clima?"', size=FS_SMALL)
    s.rect(lx + 570, 260, 170, 40, fill='#e8e8e8')
    s.text(lx + 655, 280, '→ recálculo completo ✗', size=FS_SMALL)

    s.rect(80, 330, 660, 130, fill='code_bg', stroke='dark', rx=4)
    s.text(410, 355, 'Comparación de rendimiento (contexto de 3000 tokens)', size=FS_BODY, bold=True)

    s.line(100, 370, 720, 370, color='dark')
    s.text(230, 390, 'Acierto de caché (hit)', size=FS_SMALL, bold=True)
    s.text(490, 390, 'Fallo de caché (miss)', size=FS_SMALL, bold=True)
    s.line(100, 405, 720, 405, color='dark')

    s.text(130, 425, 'TTFT', size=FS_SMALL, anchor='start')
    s.text(230, 425, '~0.5 segundos', size=FS_SMALL)
    s.text(490, 425, '3 - 5 segundos', size=FS_SMALL)

    s.text(130, 450, 'Costo', size=FS_SMALL, anchor='start')
    s.text(230, 450, 'solo se cobran tokens nuevos', size=FS_SMALL)
    s.text(490, 450, 'se cobran todos los tokens', size=FS_SMALL)

    s.save(f'{OUT}/fig2-4.svg')


def fig2_5():
    """Agent Status Bar Injection Architecture — Figure 2-5."""
    W, H = 820, 580
    s = SVG(W, H)

    s.text(410, 30, 'Arquitectura de inyección de barra de estado', size=FS_TITLE, bold=True)

    col_w = 350
    col_gap = 70
    lx1 = 30
    lx2 = lx1 + col_w + col_gap

    s.text(lx1 + col_w / 2, 65, 'Sin barra de estado', size=FS_BODY, bold=True)
    s.text(lx2 + col_w / 2, 65, 'Con barra de estado', size=FS_BODY, bold=True)

    y = 90
    left_items = [
        ('system', 'Prompt del sistema + Herramientas', 'medium', 35),
        ('user', '"Contactar Xfinity para descuento"', 'light', 35),
        ('assistant', 'phone_call(Xfinity) → int. 1', '#e8e8e8', 35),
        ('tool', 'Res: 45 min en espera, no conectó', 'light', 35),
        ('assistant', 'web_search("Ofertas Xfinity")', '#e8e8e8', 35),
        ('tool', 'Res: [mucho contenido de búsqueda...]', 'light', 35),
        ('assistant', 'phone_call(Xfinity) → int. 2', '#e8e8e8', 35),
        ('tool', 'Res: conectó, ofrecieron $65/mes', 'light', 35),
        ('assistant', 'phone_call(Xfinity) → int. 3', '#e8e8e8', 35),
        ('tool', 'Res: descuento a $59/mes confirmado', 'light', 35),
        ('user', '"¿Puedes llamar de nuevo?"', 'light', 35),
    ]

    for role, content, fill, h in left_items:
        s.rect(lx1, y, col_w, h, fill=fill, rx=4)
        s.text(lx1 + 8, y + h / 2, f'{role}:', size=FS_TINY, anchor='start', bold=True)
        s.mono(lx1 + 65, y + h / 2, content, size=FS_TINY - 2)
        y += h + 3

    s.text(lx1 + col_w / 2, y + 15, '→ El modelo debe escanear todo el contexto para contar', size=FS_SMALL, fill='text_light')
    s.text(lx1 + col_w / 2, y + 35, 'puede contar mal el número de llamadas realizadas', size=FS_SMALL, fill='text_light')

    y = 90
    right_items = [
        ('system', 'Prompt del sistema + Herramientas', 'medium', 35),
        ('user', '"Contactar Xfinity para descuento"', 'light', 35),
        ('...', '[ Mismo contenido de trayectoria ]', '#e8e8e8', 90),
        ('user', '"¿Puedes llamar de nuevo?"', 'light', 35),
    ]
    for role, content, fill, h in right_items:
        s.rect(lx2, y, col_w, h, fill=fill, rx=4)
        s.text(lx2 + 8, y + h / 2, f'{role}:', size=FS_TINY, anchor='start', bold=True)
        s.mono(lx2 + 65, y + h / 2, content, size=FS_TINY - 2)
        y += h + 3

    hint_y = y
    hint_h = 130
    s.rect(lx2, hint_y, col_w, hint_h, fill='medium', stroke='border', rx=4)
    s.text(lx2 + 10, hint_y + 18, '<agent_status>', size=FS_SMALL, bold=True, anchor='start')
    hints = [
        'phone_call ejecutado 3 veces (Xfinity: 3)',
        'Control límite: límite alcanzado (3/3) ✗',
        'TODO: [✓]Llamar Xfinity [✓]Confirmar desc.',
        'Hora actual: 2025-09-14 10:30',
        'Estado actual: esperando confirmación usuario',
    ]
    for i, h in enumerate(hints):
        s.mono(lx2 + 15, hint_y + 40 + i * 20, h, size=FS_TINY - 2)
    s.text(lx2 + col_w - 10, hint_y + hint_h - 12, '</agent_status>', size=FS_SMALL, bold=True, anchor='end')

    s.text(lx2 + col_w / 2, hint_y + hint_h + 18, '→ El modelo lee directamente el estado procesado', size=FS_SMALL, fill='text_light')
    s.text(lx2 + col_w / 2, hint_y + hint_h + 38, 'Respeta restricciones, no hace llamadas de más', size=FS_SMALL, fill='text_light')

    s.text(lx1 + col_w + col_gap / 2, 300, 'VS', size=FS_BODY, bold=True)

    s.save(f'{OUT}/fig2-5.svg')


def fig2_6():
    """Context compression strategy comparison — Figure 2-6."""
    W, H = 820, 530
    s = SVG(W, H)

    s.text(410, 30, 'Comparación de estrategias de compresión de contexto', size=FS_TITLE, bold=True)

    tx = 30
    tw = 760

    header_y = 68
    headers = [
        (tx + 72, 'Estrategia'),
        (tx + 195, 'Tokens'),
        (tx + 282, 'Tasa'),
        (tx + 352, 'Rondas'),
        (tx + 432, 'Resultado'),
        (tx + 475 + 90, 'Uso de tokens'),
    ]
    for cx, label in headers:
        s.text(cx, header_y, label, size=FS_SMALL, bold=True)

    s.line(tx, header_y + 12, tx + tw, header_y + 12)

    strategies = [
        ('Sin compresión', '> 110K', '100%', '5 (Fallido)', False, 110000),
        ('Resumen individual', '123,205', '6.8%', '24', True, 123205),
        ('Resumen combinado', '55,462', '2.1%', '21', True, 55462),
        ('Consciente de contexto', '25,198', '0.9%', '15', True, 25198),
        ('Consciente + citas', '45,544', '1.4%', '17', True, 45544),
        ('Ventana adaptable', '181,372', '—', '8', True, 181372),
    ]

    max_tokens = 190000
    bar_x = tx + 475
    bar_max_w = 280

    for i, (name, tokens, ratio, iters, success, token_val) in enumerate(strategies):
        y = header_y + 30 + i * 62

        s.text(tx + 72, y + 15, name, size=FS_SMALL, anchor='middle',
               bold=(name == 'Consciente de contexto'))

        s.text(tx + 195, y + 15, tokens, size=FS_SMALL)
        s.text(tx + 282, y + 15, ratio, size=FS_SMALL)
        s.text(tx + 352, y + 15, iters, size=FS_SMALL)

        result_text = '✓ Éxito' if success else '✗ Fallo'
        result_color = 'text' if success else 'dark'
        s.text(tx + 432, y + 15, result_text, size=FS_SMALL, fill=result_color)

        bar_w = (token_val / max_tokens) * bar_max_w
        bar_fill = '#e8e8e8' if name != 'Consciente de contexto' else 'medium'
        if not success:
            bar_fill = 'white'
        s.rect(bar_x, y, bar_w, 30, fill=bar_fill, stroke='border', rx=3)

    best_y = header_y + 30 + 3 * 62 - 5
    s.rect(tx - 2, best_y, tw + 4, 42, fill='white', stroke='border', rx=4, dash=True)

    s.rect(100, H - 60, 620, 45, fill='code_bg', stroke='dark', rx=4)
    s.text(410, H - 45, 'Compresión consciente de contexto: 77% reducción de tokens, mayor tasa de éxito', size=FS_SMALL, bold=True)
    s.text(410, H - 25, 'Clave: incluir intención de consulta e información actual en decisiones de compresión', size=FS_SMALL, fill='text_light')

    s.save(f'{OUT}/fig2-6.svg')


def fig2_7():
    """Context Compression Pipeline Variants — Figure 2-7."""
    W, H = 820, 600
    s = SVG(W, H)

    s.text(410, 30, 'Experimento 2.7: Flujo de procesamiento de 6 estrategias de compresión', size=FS_TITLE, bold=True)
    s.text(410, 58, 'Cada búsqueda devuelve ~70K caracteres → cada estrategia procesa distinto', size=FS_SMALL, fill='text_light')

    strategies = [
        ('① Sin compresión', 'Guardar directo', 'Ingresa todo el texto original al contexto', '> 110K tok → desborde', False),
        ('② Resumen indiv.', 'Resumen indep.', 'Cada resultado produce 2-3 párrafos de resumen', '123K tok · 6.8%', True),
        ('③ Resumen comb.', 'Resumen unido', 'Todos los resultados se unen en un solo resumen', '55K tok · 2.1%', True),
        ('④ Consciente ctx.', 'Compresión intel.', 'Consulta + contexto → compresión dirigida', '25K tok · 0.9%', True),
        ('⑤ Consciente+citas', 'Intel. + trazabilidad', 'Contenido comprimido + marcas de cita URL', '45K tok · 1.4%', True),
        ('⑥ Ventana adapt.', 'Compresión diferida', 'Texto orig. al 80% ventana, luego compresión', '181K tok · Máx fidelidad', True),
    ]

    lx = 30
    row_h = 78
    start_y = 75

    for i, (name, method, desc, result, success) in enumerate(strategies):
        y = start_y + i * row_h

        fill = 'darker' if i == 3 else 'dark'
        s.badge(lx, y, 130, 26, name, fill=fill, font_size=FS_TINY)

        s.rect(lx, y + 30, 120, 40, fill='#e8e8e8', rx=4)
        s.text(lx + 60, y + 50, method, size=FS_SMALL)

        s.arrow(lx + 122, y + 50, lx + 135, y + 50)

        s.rect(lx + 138, y + 30, 330, 40, fill='code_bg', stroke='dark', rx=4)
        s.text(lx + 303, y + 50, desc, size=FS_TINY)

        s.arrow(lx + 470, y + 50, lx + 483, y + 50)

        res_fill = 'medium' if i == 3 else ('white' if not success else 'light')
        s.rect(lx + 486, y + 30, 275, 40, fill=res_fill, rx=4)
        s.text(lx + 623, y + 50, result, size=FS_TINY)

    s.save(f'{OUT}/fig2-7.svg')


def fig2_8():
    """Skills Progressive Disclosure — Figure 2-8."""
    W, H = 820, 540
    s = SVG(W, H)

    s.text(410, 30, 'Mecanismo de divulgación progresiva de Agent Skills (Ejemplo PPTX)', size=FS_TITLE, bold=True)

    y1 = 70
    s.rect(40, y1, 740, 90, fill='medium')
    s.text(60, y1 + 20, 'Capa 1: Metadatos (cargados al inicio, ~200 tokens)', size=FS_BODY, bold=True, anchor='start')
    s.rect(60, y1 + 40, 700, 40, fill='code_bg', rx=4)
    s.mono(70, y1 + 60, 'skills: [{name: "PPTX", desc: "Crear presentación PowerPoint desde contenido"}', size=FS_TINY)
    s.mono(70, y1 + 75, '        {name: "PDF",  desc: "Extraer y analizar documentos PDF"}, ...]', size=FS_TINY - 2)

    s.arrow(410, y1 + 92, 410, y1 + 115)
    s.text(430, y1 + 103, 'Gatillo de tarea: "Crear PPT desde artículo"', size=FS_SMALL, anchor='start', fill='text_light')

    y2 = y1 + 120
    s.rect(40, y2, 740, 130, fill='light')
    s.text(60, y2 + 20, 'Capa 2: Flujo principal SKILL.md (cargado bajo demanda, ~2K tokens)', size=FS_BODY, bold=True, anchor='start')
    s.rect(60, y2 + 40, 700, 80, fill='code_bg', rx=4)
    lines2 = [
        'Flujo principal PPTX Skill:',
        '1. markitdown extrae texto → 2. Abrir archivo PPTX para acceso XML',
        '3. Modificar contenido slide{N}.xml → 4. Reempaquetar como .pptx',
        'Referencias: → html2pptx.md | → reference.md | → scripts/',
    ]
    for i, line in enumerate(lines2):
        s.mono(70, y2 + 56 + i * 19, line, size=FS_TINY)

    s.arrow(410, y2 + 132, 410, y2 + 155)
    s.text(430, y2 + 143, 'Método detallado necesario: "Generar PPT con plantilla HTML"', size=FS_SMALL, anchor='start', fill='text_light')

    y3 = y2 + 160
    s.rect(40, y3, 740, 130, fill='white', dash=True)
    s.text(60, y3 + 20, 'Capa 3: Subdocumentos (profundización selectiva bajo demanda)', size=FS_BODY, bold=True, anchor='start')

    doc_w = 215
    docs = [
        ('html2pptx.md', 'Plantilla HTML → PPT\n flujo completo'),
        ('reference.md', 'Especificación de formato XML\n y detalles técnicos'),
        ('scripts/*.py', 'Herramientas ejecutables:\nthumbnail.py etc.'),
    ]
    for i, (name, desc) in enumerate(docs):
        dx = 60 + i * (doc_w + 20)
        s.rect(dx, y3 + 45, doc_w, 70, fill='code_bg', stroke='dark', rx=4)
        s.text(dx + doc_w / 2, y3 + 62, name, size=FS_SMALL, bold=True)
        desc_lines = desc.split('\n')
        for j, dl in enumerate(desc_lines):
            s.text(dx + doc_w / 2, y3 + 82 + j * 16, dl, size=FS_TINY, fill='text_light')

    s.rect(100, y3 + 140, 620, 35, fill='code_bg', stroke='dark', rx=4)
    s.text(410, y3 + 158, 'Metadatos estables → compatible KV Cache | Inserción dinámica → no rompe caché', size=FS_SMALL)

    s.save(f'{OUT}/fig2-8.svg')


def fig2_9_memory_comparison():
    """Memory Strategy Comparison — Figure 2-9."""
    W, H = 820, 620
    s = SVG(W, H)

    s.text(410, 30, 'Experimento 2.10: Comparación de cuatro estrategias de memoria', size=FS_TITLE, bold=True)

    s.rect(40, 60, 740, 55, fill='light')
    s.text(50, 78, 'Diálogo original:', size=FS_SMALL, bold=True, anchor='start')
    s.mono(50, 98, '"Soy ing. sénior en TechCorp, lidero equipo de 5 pers. en rec. sys, 3 años usando ML"', size=FS_TINY)

    strategies = [
        ('Notas simples', 'Hechos atómicos', [
            '"Empresa: TechCorp"',
            '"Cargo: Ing. Sénior"',
            '"Equipo: 5 personas"',
            '"Especialidad: Rec Sys"',
        ], 'Ventajas: O(1), muy bajo costo\nContras: Pierde contexto relacional'),
        ('Notas avanzadas', 'Párrafo completo', [
            '"Ingeniero sénior en',
            'TechCorp, lidera equipo de',
            '5 personas en rec sys,',
            '3 años en ML."',
        ], 'Ventajas: Integridad semántica\nContras: Redundancia + actualización compleja'),
        ('Fichas JSON', 'Estructura jerárquica', [
            'work:',
            '  company: "TechCorp"',
            '  title: "Ing. Sénior"',
            '  team_size: 5',
        ], 'Ventajas: Actualización parcial\nContras: Clasificación rígida'),
        ('Fichas JSON avanz.', 'Info contextualizada', [
            '{category: "work",',
            ' title: "Ing. Sénior",',
            ' backstory: "Autopresentación",',
            ' ts: "09-14"}',
        ], 'Ventajas: Desambiguación + trazabilidad\nContras: Alto costo de generación'),
    ]

    col_w = 185
    gap = 10
    total = len(strategies) * col_w + (len(strategies) - 1) * gap
    start_x = (W - total) / 2

    for i, (name, approach, storage, tradeoff) in enumerate(strategies):
        x = start_x + i * (col_w + gap)

        s.rect(x, 130, col_w, 50, fill='medium')
        s.text(x + col_w / 2, 148, name, size=FS_SMALL, bold=True)
        s.text(x + col_w / 2, 168, approach, size=FS_TINY, fill='text_light')

        s.arrow(x + col_w / 2, 117, x + col_w / 2, 128, color='dark')

        storage_h = len(storage) * 18 + 16
        s.rect(x, 190, col_w, storage_h, fill='code_bg', stroke='dark', rx=4)
        for j, line in enumerate(storage):
            s.mono(x + 8, 205 + j * 18, line, size=FS_TINY - 2)

        s.text_block(x + col_w / 2, 200 + storage_h + 6, col_w - 6,
                     tradeoff.split('\n'), size=FS_TINY, min_size=9, line_gap=1.25)

    eval_y = 420
    s.rect(40, eval_y, 740, 180, fill='light')
    s.text(60, eval_y + 22, 'Marco de evaluación de tres niveles', size=FS_BODY, bold=True, anchor='start')

    eval_levels = [
        ('Nivel 1: Recordatorio básico', 'Almacenar y recuperar información directa', '"Mi id es 12345" → Devuelve coincidencia exacta', 'light'),
        ('Nivel 2: Acceso multisesión', 'Inferencia relacional entre sesiones', '"Programa mantenimiento de mi auto" → Distingue entre 2 autos', '#e8e8e8'),
        ('Nivel 3: Servicio proactivo', 'Integrar múltiples memorias, ayuda predictiva', 'Reserva vuelo internacional → El pasaporte está por vencer', 'medium'),
    ]

    for i, (level, desc, example, fill) in enumerate(eval_levels):
        ey = eval_y + 45 + i * 45
        s.rect(60, ey, 180, 38, fill=fill, rx=4)
        s.text(150, ey + 19, level, size=FS_SMALL, bold=True)
        s.text(252, ey + 12, desc, size=FS_TINY, anchor='start')
        s.mono(252, ey + 29, example, size=FS_TINY - 2, anchor='start')

    s.save(f'{OUT}/fig2-9.svg')


def fig2_10():
    """Mem0 Architecture — Figure 2-10."""
    W, H = 820, 530
    s = SVG(W, H)

    s.text(410, 30, 'Arquitectura de gestión de memoria Mem0', size=FS_TITLE, bold=True)

    s.rect(30, 70, 250, 80, fill='light')
    s.text(40, 88, 'Nueva conversación:', size=FS_SMALL, bold=True, anchor='start')
    s.mono(40, 110, 'user: "Me mudé a Shenzhen,', size=FS_TINY)
    s.mono(40, 128, 'mi nueva dirección es Parque Nanshan"', size=FS_TINY)

    s.rect(310, 65, 200, 100, fill='medium')
    s.text(410, 85, 'MemoryBase', size=FS_BODY, bold=True)
    s.text(410, 108, 'Gestión del ciclo de vida de memoria', size=FS_SMALL, fill='text_light')
    s.text(410, 130, 'Analizar → Clasificar → Decidir', size=FS_SMALL, fill='text_light')
    s.arrow(282, 110, 308, 110)

    s.rect(330, 185, 160, 50, fill='#e8e8e8')
    s.text(410, 203, 'LLMBase', size=FS_SMALL, bold=True)
    s.text(410, 222, 'Análisis semántico + Evaluación relacional', size=FS_TINY)
    s.arrow(410, 167, 410, 183, color='dark')
    s.arrow(410, 183, 410, 167, color='dark')

    s.rect(310, 255, 200, 80, fill='code_bg', stroke='dark', rx=4)
    s.text(320, 273, 'Resultado de decisión:', size=FS_SMALL, bold=True, anchor='start')
    s.mono(320, 293, 'Antiguo: "Vive en Pekín"', size=FS_TINY)
    s.mono(320, 311, '→ UPDATE: "Vive en Shenzhen Nanshan"', size=FS_TINY)
    s.mono(320, 329, '→ ADD: "Se mudó a Shenzhen"', size=FS_TINY - 2)
    s.arrow(410, 237, 410, 253, color='dark')

    s.rect(560, 70, 220, 70, fill='light')
    s.text(670, 90, 'EmbeddingBase', size=FS_SMALL, bold=True)
    s.text(670, 112, 'Texto → Vector (cómputo intensivo)', size=FS_TINY, fill='text_light')
    s.arrow(512, 95, 558, 90)

    s.rect(560, 160, 220, 100, fill='light')
    s.text(670, 180, 'VectorStoreBase', size=FS_SMALL, bold=True)
    s.text(670, 200, 'Persistencia + Búsqueda (I/O intensivo)', size=FS_TINY, fill='text_light')
    s.text(670, 225, 'Chroma / Qdrant / Milvus', size=FS_TINY, fill='text_light')
    s.text(670, 248, '(Índice HNSW / LSH)', size=FS_TINY, fill='text_light')
    s.arrow(670, 142, 670, 158)

    s.rect(560, 290, 220, 120, fill='code_bg', stroke='dark', rx=4)
    s.text(570, 310, 'Memorias almacenadas:', size=FS_SMALL, bold=True, anchor='start')
    s.mono(570, 332, '"Vive en Parque Nanshan, Shenzhen"', size=FS_TINY)
    s.mono(570, 352, '"Email: john@x.com"', size=FS_TINY)
    s.mono(570, 372, '"Preferencia: idioma español"', size=FS_TINY)
    s.mono(570, 392, '"Profesión: Ing. ML"', size=FS_TINY)
    s.arrow(670, 262, 670, 288, color='dark')

    s.rect(30, 170, 250, 60, fill='code_bg', stroke='dark', rx=4)
    s.text(155, 192, 'Mecanismo de complementos', size=FS_SMALL, bold=True)
    s.text(155, 212, 'LLM / modelo embedding / almacenamiento intercambiables', size=FS_TINY, fill='text_light')

    s.rect(30, 390, 250, 80, fill='light')
    s.text(40, 408, 'Búsqueda de memoria:', size=FS_SMALL, bold=True, anchor='start')
    s.mono(40, 430, 'query: "¿Dónde vive el usuario?"', size=FS_TINY)
    s.mono(40, 450, '→ Coincidencia por similitud vectorial', size=FS_TINY)
    s.mono(40, 468, '→ "Vive en Parque Nanshan, Shenzhen"', size=FS_TINY)
    s.arrow_curved(282, 430, 558, 350, curve=-30, label='Búsqueda', color='dark')

    s.save(f'{OUT}/fig2-10.svg')


def fig2_11():
    """Memobase Multi-type Memory Architecture — Figure 2-11."""
    W, H = 820, 560
    s = SVG(W, H)

    s.text(410, 30, 'Arquitectura de memoria multitipo de Memobase', size=FS_TITLE, bold=True)

    types = [
        ('Memoria episódica', 'Episodic', [
            '2025-09-10 Vuelo Shanghái→Tokio reservado',
            '2025-09-12 Vuelo pospuesto al 20/9',
            '2025-09-13 Hotel cambiado a sucursal Shinjuku',
        ], 'Secuencia de eventos con marca de tiempo'),
        ('Memoria semántica', 'Semantic', [
            'Usuario → es → Ing. ML',
            'Usuario → tiene alergia a maní',
            'Usuario → prefiere → asiento de ventana',
        ], 'Red entidad-relación'),
        ('Memoria procedimental', 'Procedural', [
            'Patrón de planificación de viaje:',
            '  Destino→Presupuesto→Transporte→Hotel',
            '(Extraído de múltiples interacciones)',
        ], 'Patrón de estrategia reutilizable'),
        ('Memoria de trabajo', 'Working', [
            'Tarea actual: Reservar hotel en Tokio',
            'Completado: Vuelo reservado (ANA NH919)',
            'Pendiente: Seleccionar hotel + traslado',
        ], 'Estado actual de la tarea'),
    ]

    col_w = 185
    gap = 10
    total = len(types) * col_w + (len(types) - 1) * gap
    start_x = (W - total) / 2

    for i, (name, eng, examples, desc) in enumerate(types):
        x = start_x + i * (col_w + gap)

        s.rect(x, 65, col_w, 55, fill='medium')
        s.text(x + col_w / 2, 82, name, size=FS_SMALL, bold=True)
        s.text(x + col_w / 2, 105, eng, size=FS_TINY, fill='text_light')

        ex_h = len(examples) * 20 + 20
        s.rect(x, 130, col_w, ex_h, fill='code_bg', stroke='dark', rx=4)
        for j, ex in enumerate(examples):
            s.mono(x + 8, 148 + j * 20, ex, size=FS_TINY - 2)

        s.text(x + col_w / 2, 130 + ex_h + 18, desc, size=FS_TINY, fill='text_light')

    arrow_y = 280
    wm_x = start_x + 3 * (col_w + gap) + col_w / 2

    for i in range(3):
        lt_x = start_x + i * (col_w + gap) + col_w / 2
        s.arrow_curved(wm_x - 20, arrow_y, lt_x + 20, arrow_y, curve=-30, dash=True, color='dark')

    s.text(410, arrow_y - 10, 'Memoria de trabajo ↔ Memoria a largo plazo (interacción dinámica)', size=FS_SMALL, fill='text_light')

    comp_y = 310
    s.rect(40, comp_y, 740, 110, fill='light')
    s.text(60, comp_y + 22, 'Compresión y organización de memoria', size=FS_BODY, bold=True, anchor='start')

    comp_stages = [
        ('Puntuación importancia', ['Frec. acceso × Decaimiento tiempo', '× Intensidad emocional × Unicidad']),
        ('Compresión agrupadora', ['Agrupar memorias similares', '→ Generar resumen representativo']),
        ('Abstracción y generaliz.', ['Memoria episódica → Semántica', 'Eventos específicos → Reglas generales']),
    ]

    stage_w = 220
    stage_gap = 15
    sx = 60
    for j, (title, desc_lines) in enumerate(comp_stages):
        cx = sx + j * (stage_w + stage_gap)
        s.rect(cx, comp_y + 45, stage_w, 55, fill='code_bg', stroke='dark', rx=4)
        s.text(cx + stage_w / 2, comp_y + 62, title, size=FS_SMALL, bold=True)
        for k, dl in enumerate(desc_lines):
            s.text(cx + stage_w / 2, comp_y + 78 + k * 15, dl, size=FS_TINY, fill='text_light')
        if j > 0:
            s.arrow(cx - stage_gap + 2, comp_y + 72, cx - 2, comp_y + 72, color='dark')

    priv_y = comp_y + 125
    s.rect(40, priv_y, 740, 90, fill='#e8e8e8')
    s.text(60, priv_y + 20, 'Protección de privacidad: Almacenamiento de información en capas', size=FS_BODY, bold=True, anchor='start')

    levels = [
        ('L1 General', 'Nombre, email', 'Texto plano'),
        ('L2 Interno', 'Teléfono, dirección', 'Enmascaramiento parcial'),
        ('L3 Confidencial', 'DNI, contraseña', 'Reemplazo por marcador'),
    ]

    lev_w = 230
    for j, (level, info, strategy) in enumerate(levels):
        lx = 55 + j * (lev_w + 10)
        s.rect(lx, priv_y + 38, lev_w, 40, fill='code_bg', stroke='dark', rx=4)
        s.text(lx + 8, priv_y + 58, f'{level}: {info} → {strategy}', size=FS_TINY, anchor='start')

    s.save(f'{OUT}/fig2-11.svg')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    fig2_1()
    fig2_2()
    fig2_3()
    fig2_4()
    fig2_5()
    fig2_6()
    fig2_7()
    fig2_8()
    fig2_9_memory_comparison()
    fig2_10()
    fig2_11()
    print("Chapter 2 figures generated.")
