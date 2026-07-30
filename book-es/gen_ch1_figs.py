"""Generate all Chapter 1 figures in Spanish."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import *

OUT = os.path.join(os.path.dirname(__file__), 'images')


def fig1_4():
    """Kimi K3 / GPT-5.6 native agent architecture — caption Figure 1-4"""
    s = SVG(820, 520)

    # Title
    s.text(410, 30, 'Arquitectura "El Modelo como Agente": llamadas nativas a herramientas', size=FS_TITLE, bold=True)

    # Central model box
    s.rect(260, 70, 300, 100, fill='medium')
    s.text(410, 100, 'LLM (Kimi K3 / GPT-5.6)', size=FS_BODY, bold=True)
    s.text(410, 130, 'Capacidades agénticas nativas tras entrenamiento con RL', size=FS_SMALL, fill='text_light')

    # Built-in tools on the right
    s.group_box(620, 70, 180, 210, 'Herramientas nativas')
    s.box(635, 105, 150, 50, '$web_search', fill='light', font_size=FS_SMALL)
    s.box(635, 170, 150, 50, 'code_interpreter', fill='light', font_size=FS_SMALL)
    s.box(635, 235, 150, 50, 'Más herramientas...', fill='white', font_size=FS_SMALL)

    s.arrow(560, 120, 633, 130)
    s.arrow(633, 195, 560, 145)

    # ReAct loop below
    s.group_box(100, 210, 460, 280, 'Bucle ReAct (ejecución autónoma dentro del modelo)')

    # Step 1: User input
    s.box(120, 250, 200, 55, 'Usuario: Buscar la tendencia de Bitcoin del último mes', fill='light', font_size=FS_SMALL)

    # Step 2: Think
    s.box(120, 325, 200, 55, 'Pensamiento: Se deben buscar datos en tiempo real y analizarlos con código', fill='#e8e8e8', font_size=FS_SMALL)
    s.arrow(220, 307, 220, 323)

    # Step 3: Tool call
    s.box(340, 250, 200, 55, 'Llamando a $web_search\n"Precio BTC último mes"', fill='light', font_size=FS_SMALL)
    s.arrow(322, 277, 338, 277)

    # Step 4: Tool result
    s.box(340, 325, 200, 55, 'Resultado: [datos de precio]\n$67,230 → $71,450', fill='#e8e8e8', font_size=FS_SMALL)
    s.arrow(440, 307, 440, 323)

    # Step 5: Code
    s.box(120, 400, 200, 55, 'Llamando a code_interpreter\nCódigo de cálculo RSI, MACD', fill='light', font_size=FS_SMALL)
    s.arrow(340, 377, 220, 398, color='dark')

    # Step 6: Final
    s.box(340, 400, 200, 55, 'Resultado final: Informe de análisis técnico + gráfico de visualización', fill='medium', font_size=FS_SMALL)
    s.arrow(322, 427, 338, 427)

    # RL training signal
    s.arrow_curved(565, 480, 410, 172, curve=40, dash=True, color='dark')
    s.text(605, 330, 'Señal de entrenamiento RL', size=FS_TINY, fill='text_light', bold=True, anchor='start')

    # Left side: what's different from traditional
    s.group_box(15, 70, 230, 120, 'Diferencias con marcos tradicionales')
    s.text(130, 110, '✗ Sin código de orquestación externo', size=FS_SMALL, anchor='middle')
    s.text(130, 135, '✗ Sin necesidad de escribir ReAct manual', size=FS_SMALL, anchor='middle')
    s.text(130, 160, '✓ El modelo decide todo autónomamente', size=FS_SMALL, anchor='middle')

    s.save(f'{OUT}/fig1-3.svg')  # ReAct execution process → Figure 1-3


def fig1_1():
    """Three learning paradigms — caption Figure 1-1."""
    s = SVG(820, 480)

    s.text(410, 30, 'Tres paradigmas de aprendizaje para Agentes', size=FS_TITLE, bold=True)

    col_w = 240
    gap = 20
    x_start = (820 - 3 * col_w - 2 * gap) / 2

    for i, (title, time_label, items, example) in enumerate([
        ('Posentrenamiento', 'Entrenamiento', [
            'Modifica los pesos del modelo',
            'Persistente · general',
            'Alto costo · actualización lenta',
        ], 'ej. aprender cuándo llamar a una herramienta'),
        ('Aprendizaje en contexto', 'Inferencia', [
            'Actualización suave por atención',
            'Temporal · adaptación instantánea',
            'Limitado por la ventana de contexto',
        ], 'ej. aprender un formato desde 3 ejemplos'),
        ('Aprendizaje externalizado', 'Ejecución', [
            'Base de conocimiento + herramientas',
            'Persistente · actualizable',
            'Confiable · verificable',
        ], 'ej. convertir flujo de trabajo en herramienta'),
    ]):
        x = x_start + i * (col_w + gap)

        # Header
        s.box(x, 65, col_w, 65, title, fill='medium', bold=True, font_size=FS_BODY)

        # Time badge
        s.badge(x + col_w / 2 - 40, 140, 80, 28, time_label, fill='darker')

        # Items
        for j, item in enumerate(items):
            y = 185 + j * 45
            s.box(x, y, col_w, 38, item, fill='light', font_size=FS_SMALL)

        # Example
        s.rect(x, 330, col_w, 45, fill='code_bg', stroke='dark', rx=4)
        s.text(x + col_w / 2, 352, example, size=FS_SMALL, fill='text_light')

    # Timeline arrow at bottom
    s.arrow(60, 430, 760, 430, color='dark')
    s.text(60, 455, 'Lento (Semanas)', size=FS_SMALL, fill='text_light', anchor='start')
    s.text(410, 455, 'Velocidad de aprendizaje', size=FS_SMALL, fill='text_light')
    s.text(760, 455, 'Rápido (Milisegundos)', size=FS_SMALL, fill='text_light', anchor='end')

    s.save(f'{OUT}/fig1-4.svg')  # Three Learning Paradigms → Figure 1-4


def fig1_2():
    """Context ablation experiment design — caption Figure 1-2."""
    W = 1000
    s = SVG(W, 470)

    s.text(W / 2, 30, 'Diseño del experimento de ablación de contexto', size=FS_TITLE, bold=True)

    components = [
        ('Prompt del', 'sistema'),
        ('Definición de', 'herramientas'),
        ('Resultados de', 'herramientas'),
        ('Proceso de', 'pensamiento'),
        ('Historial de', 'mensajes'),
    ]
    comp_w = 108
    comp_gap = 10
    label_x = 168
    comp_x = 182

    for i, (l1, l2) in enumerate(components):
        x = comp_x + i * (comp_w + comp_gap)
        s.text(x + comp_w / 2, 56, l1, size=FS_SMALL, bold=True)
        s.text(x + comp_w / 2, 76, l2, size=FS_SMALL, bold=True)

    result_x = comp_x + len(components) * (comp_w + comp_gap) + 12
    s.text(result_x + 90, 66, 'Resultado', size=FS_SMALL, bold=True)

    conditions = [
        ('Referencia completa', [True, True, True, True, True], '✓ Funciona normalmente'),
        ('Sin def. herramientas', [True, False, True, True, True], '✗ No puede llamar herramientas'),
        ('Sin res. herramientas', [True, True, False, True, True], '✗ Bucle ciego'),
        ('Sin razonamiento', [True, True, True, False, True], '△ Decisiones inconsistentes'),
        ('Sin historial', [True, True, True, True, False], '△ Operaciones repetidas'),
    ]

    for j, (label, flags, result) in enumerate(conditions):
        y = 100 + j * 68

        s.text(label_x, y + 28, label, size=FS_SMALL, bold=True, anchor='end')

        for i, present in enumerate(flags):
            x = comp_x + i * (comp_w + comp_gap)
            fill = 'light' if present else 'white'
            stroke = 'border' if present else 'dark'
            s.rect(x, y, comp_w, 55, fill=fill, stroke=stroke, dash=not present)
            if present:
                s.text(x + comp_w / 2, y + 28, '✓', size=FS_BODY)
            else:
                s.text(x + comp_w / 2, y + 28, '✗', size=FS_BODY, fill='dark')

        s.text(result_x + 90, y + 28, result, size=FS_SMALL, anchor='middle',
               fill='text' if '✓' in result else ('text_light' if '△' in result else 'dark'))

    s.save(f'{OUT}/fig1-1.svg')  # Context ablation experiment → Figure 1-1


def fig1_3():
    """Agent trajectory — caption Figure 1-3."""
    s = SVG(820, 680)

    s.text(410, 30, 'Trayectoria del Agente: Bucle ReAct para agregación multimoneda', size=FS_TITLE, bold=True)

    lx = 40
    rw = 480

    y = 60

    # Round 1
    s.badge(lx, y, 80, 26, 'Ronda 1', fill='darker')
    y += 36

    # User message
    s.rect(lx, y, rw, 50, fill='light')
    s.text(lx + 10, y + 14, 'user', size=FS_SMALL, bold=True, anchor='start')
    s.text(lx + 10, y + 36, '"Calcular el ingreso anual total: Q1 $2.5M, Q2 €2.1M, Q3 £1.8M"', size=FS_TINY, anchor='start')
    y += 60

    # Assistant reasoning
    s.rect(lx, y, rw, 45, fill='#e8e8e8')
    s.text(lx + 10, y + 14, 'assistant.reasoning', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.text(lx + 10, y + 34, '"Convertir EUR y GBP a USD y luego sumar"', size=FS_TINY, anchor='start')
    y += 55

    # Tool calls
    s.rect(lx, y, rw, 70, fill='code_bg', stroke='dark', rx=4)
    s.text(lx + 10, y + 14, 'assistant.tool_calls', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.mono(lx + 10, y + 36, 'convert_currency(2100000, "EUR", "USD")', size=FS_TINY)
    s.mono(lx + 10, y + 54, 'convert_currency(1800000, "GBP", "USD")', size=FS_TINY)
    y += 80

    # Tool results
    s.rect(lx, y, rw, 55, fill='light')
    s.text(lx + 10, y + 14, 'tool (resultado)', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.mono(lx + 10, y + 36, 'EUR→USD: 2,282,608.70', size=FS_TINY)
    s.mono(lx + 250, y + 36, 'GBP→USD: 2,278,481.01', size=FS_TINY)
    y += 65

    # Round 2
    s.badge(lx, y, 80, 26, 'Ronda 2', fill='darker')
    y += 36

    # Assistant reasoning 2
    s.rect(lx, y, rw, 45, fill='#e8e8e8')
    s.text(lx + 10, y + 14, 'assistant.reasoning', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.text(lx + 10, y + 34, '"Tipos de cambio obtenidos, llamando al intérprete de código"', size=FS_TINY, anchor='start')
    y += 55

    # Code interpreter call
    s.rect(lx, y, rw, 50, fill='code_bg', stroke='dark', rx=4)
    s.text(lx + 10, y + 14, 'assistant.tool_calls', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.mono(lx + 10, y + 36, 'code_interpreter("total = 2.5M + 2.28M + 2.28M")', size=FS_TINY)
    y += 60

    # Round 3
    s.badge(lx, y, 80, 26, 'Ronda 3', fill='darker')
    y += 36

    # Final answer
    s.rect(lx, y, rw, 45, fill='medium')
    s.text(lx + 10, y + 14, 'assistant.content (respuesta final)', size=FS_SMALL, bold=True, anchor='start')
    s.text(lx + 10, y + 36, '"Ingreso anual total $7.061.089,71, promedio trimestral $2.353.696,57"', size=FS_TINY, anchor='start')
    y += 55

    # Right side: brace + annotation
    bx = 540
    s.brace_right(bx, 60, y - 10, '')
    s.text(600, 250, 'Trayectoria', size=FS_BODY, bold=True, anchor='start')
    s.text(600, 280, '=', size=FS_BODY, anchor='start')
    s.text(600, 310, 'Entrada completa', size=FS_BODY, anchor='start')
    s.text(600, 340, 'que ve el LLM', size=FS_BODY, anchor='start')
    s.text(600, 370, 'en cada llamada', size=FS_BODY, anchor='start')

    # Key insight box on right
    s.group_box(570, 410, 230, 140, 'Características clave')
    s.text(685, 445, 'Acumulación de contexto', size=FS_SMALL, bold=True)
    s.text(685, 470, 'Se ve todo el historial en cada ronda', size=FS_TINY, fill='text_light')
    s.text(685, 500, 'Trayectoria estructurada', size=FS_SMALL, bold=True)
    s.text(685, 525, 'user / assistant / tool', size=FS_TINY, fill='text_light')

    s.save(f'{OUT}/fig1-2.svg')  # Agent trajectory → Figure 1-2


def fig1_wf_chaining():
    """Prompt chaining — workflow pattern."""
    s = SVG(820, 300)

    s.text(410, 28, 'Patrón de cadena de prompts: generación multietapa', size=FS_TITLE, bold=True)

    nodes = [
        ('Documento de requisitos', 'light', FS_SMALL),
        ('LLM: Crear borrador', '#e8e8e8', FS_SMALL),
        ('LLM: Escribir texto', '#e8e8e8', FS_SMALL),
        ('LLM: Traducción', '#e8e8e8', FS_SMALL),
        ('Doc. multilingüe', 'medium', FS_SMALL),
    ]

    node_w = 130
    node_h = 55
    gap = 15
    total = len(nodes) * node_w + (len(nodes) - 1) * gap
    x_start = (820 - total) / 2
    y = 65

    for i, (label, fill, fs) in enumerate(nodes):
        x = x_start + i * (node_w + gap)
        s.box(x, y, node_w, node_h, label, fill=fill, font_size=fs)
        if i > 0:
            px = x_start + (i - 1) * (node_w + gap) + node_w
            s.arrow(px + 2, y + node_h / 2, x - 2, y + node_h / 2)

    gate_y = y + node_h + 15
    for i in [1, 2]:
        gx = x_start + i * (node_w + gap) + node_w / 2
        s.diamond(gx, gate_y + 22, 60, 40, fill='white', label='Control', font_size=FS_TINY)
        s.line(gx, y + node_h, gx, gate_y + 2, dash=True, color='dark')

    snippet_y = gate_y + 60
    snippets = [
        (x_start + 15, '"Notas de versión"'),
        (x_start + node_w + gap + 15, '→ Borrador 5 secciones'),
        (x_start + 2 * (node_w + gap) + 15, '→ Doc 3000 palabras'),
        (x_start + 3 * (node_w + gap) + 15, '→ EN / JP / KR'),
    ]
    for sx, txt in snippets:
        s.text(sx, snippet_y, txt, size=FS_TINY, fill='text_light', anchor='start')

    s.save(f'{OUT}/fig1-5.svg')


def fig1_wf_routing():
    """Routing — workflow pattern."""
    s = SVG(820, 440)

    s.text(410, 28, 'Patrón de enrutamiento: clasificación de soporte al cliente', size=FS_TITLE, bold=True)

    s.box(30, 130, 150, 55, 'Consulta del usuario', fill='medium', font_size=FS_BODY)

    s.diamond(300, 157, 140, 80, fill='#e8e8e8', label='Clasificador', font_size=FS_SMALL)
    s.arrow(182, 157, 230, 157)

    branches = [
        (55, 'Solicitud de devolución', 'Prompt devolución\n+ API pedidos', 'light'),
        (155, 'Soporte técnico', 'Prompt diagnóstico\n+ Herramientas log', 'light'),
        (255, 'Preguntas frecuentes', 'Prompt FAQ\n+ Base conocimiento', 'light'),
        (355, 'Otro', 'Haiku (Bajo costo)\n+ Prompt general', 'white'),
    ]

    bx = 490
    bw = 160
    for i, (by_offset, label, desc, fill) in enumerate(branches):
        by = by_offset
        s.box(bx, by, bw, 50, label, fill=fill, bold=True, font_size=FS_SMALL)
        s.box(bx + bw + 10, by, 140, 50, desc, fill='code_bg', font_size=FS_TINY)
        s.arrow(370, 157, bx - 2, by + 25)

    s.text(410, 425, 'Nota: La clasificación puede usarse con LLM o un clasificador tradicional; consultas simples se enrutan a modelos pequeños', size=FS_SMALL, fill='text_light')

    s.save(f'{OUT}/fig1-6.svg')


def fig1_wf_parallel():
    """Parallelization — workflow pattern."""
    s = SVG(820, 360)

    s.text(410, 28, 'Patrón de paralelización: revisión de código multidimensional', size=FS_TITLE, bold=True)

    s.box(30, 130, 150, 55, 'Commit de código\nPull Request', fill='medium', font_size=FS_SMALL)

    s.text(220, 157, 'División', size=FS_SMALL, bold=True)

    workers = [
        (70, 'LLM₁ Revisión seguridad', 'Inyección SQL\nXSS\nFuga de permisos'),
        (155, 'LLM₂ Revisión estilo', 'Convenciones de nombres\nDuplicación de código\nComplejidad'),
        (240, 'LLM₃ Revisión lógica', 'Condiciones límite\nPunteros nulos\nConcurrencia'),
    ]

    wx = 290
    ww = 155
    for i, (wy, title, items) in enumerate(workers):
        s.box(wx, wy, ww, 55, title, fill='light', bold=True, font_size=FS_SMALL)
        s.box(wx + ww + 5, wy, 130, 55, items, fill='code_bg', font_size=FS_TINY)
        s.arrow(180, 157, wx - 2, wy + 28)

    s.box(640, 130, 150, 55, 'Combinar resultados\nInforme de revisión', fill='medium', font_size=FS_SMALL)
    for i, (wy, _, _) in enumerate(workers):
        s.arrow(wx + ww + 135 + 2, wy + 28, 638, 157)

    s.save(f'{OUT}/fig1-7.svg')


def fig1_wf_orchestrator():
    """Orchestrator-workers — workflow pattern."""
    s = SVG(820, 440)

    s.text(410, 28, 'Patrón orquestador-trabajador: modificación multiarchivo', size=FS_TITLE, bold=True)

    s.rect(260, 60, 300, 95, fill='medium')
    s.text(410, 82, 'Orquestador LLM', size=FS_BODY, bold=True)
    s.rect(270, 105, 280, 38, fill='#e8e8e8', rx=4)
    s.text(410, 124, '"Analizar problema → Buscar archivos → Asignar tareas"', size=FS_TINY)

    workers = [
        (40, 'Trabajador 1', 'Modificar auth.py\nAñadir soporte OAuth2', 'Lectura/Edición\nHerramienta archivo'),
        (290, 'Trabajador 2', 'Modificar api.py\nAñadir nuevo endpoint', 'Lectura/Edición\nHerramienta archivo'),
        (540, 'Trabajador 3', 'Escribir test_auth.py\nCasos de prueba', 'Ejecutar pruebas\nHerramienta'),
    ]

    wy = 220
    ww = 230
    wh = 55
    for wx, title, task, tools in workers:
        s.box(wx, wy, ww, wh, f'{title}: {task}', fill='light', font_size=FS_SMALL)
        s.box(wx + 20, wy + wh + 10, ww - 40, 40, tools, fill='code_bg', font_size=FS_TINY)
        s.arrow(410, 157, wx + ww / 2, wy - 2)

    s.box(260, 370, 300, 55, 'Orquestador: combinar resultados → verificar consistencia', fill='medium', font_size=FS_SMALL)
    for wx, _, _, _ in workers:
        s.arrow(wx + ww / 2, wy + wh + 52, 410, 368)

    s.save(f'{OUT}/fig1-8.svg')


def fig1_wf_evaluator():
    """Evaluator-optimizer — workflow pattern."""
    s = SVG(820, 380)

    s.text(410, 28, 'Patrón evaluador-optimizador: traducción literaria iterativa', size=FS_TITLE, bold=True)

    s.box(50, 100, 200, 65, 'Generador LLM\nCrear primera traducción', fill='light', font_size=FS_SMALL)

    s.rect(50, 185, 200, 45, fill='code_bg', stroke='dark', rx=4)
    s.text(150, 208, '"Bahar uykusu..." → traducción v1', size=FS_TINY)
    s.arrow(150, 167, 150, 183)

    s.box(330, 100, 200, 65, 'Evaluador LLM\nEvaluación multidimensional', fill='#e8e8e8', font_size=FS_SMALL)
    s.arrow(252, 207, 330, 160)

    s.rect(330, 185, 200, 80, fill='code_bg', stroke='dark', rx=4)
    s.text(340, 205, 'Precisión: 4/5', size=FS_TINY, anchor='start')
    s.text(340, 225, 'Fluidez: 3/5 ← debe mejorarse', size=FS_TINY, anchor='start')
    s.text(340, 245, 'Adecuación cultural: 4/5', size=FS_TINY, anchor='start')
    s.arrow(430, 167, 430, 183)

    s.arrow_curved(430, 267, 150, 98, curve=80, dash=True, color='dark')
    s.text(290, 90, 'Retroalimentación + sugerencias de mejora', size=FS_TINY, fill='text_light', bold=True)

    s.box(610, 100, 170, 55, 'Número de iteraciones: n', fill='white', font_size=FS_SMALL)
    s.text(695, 170, 'Condiciones de salida:', size=FS_SMALL, bold=True, anchor='start')
    s.text(695, 195, '① Todas las dimensiones ≥ 4/5', size=FS_TINY, anchor='start', fill='text_light')
    s.text(695, 218, '② Máximo de rondas alcanzado', size=FS_TINY, anchor='start', fill='text_light')

    s.box(220, 310, 380, 55, 'Resultado final: traducción de alta calidad tras 3 iteraciones', fill='medium', font_size=FS_SMALL)

    s.save(f'{OUT}/fig1-9.svg')


def fig1_5():
    """Autonomous Agent loop — caption Figure 1-5."""
    s = SVG(820, 500)

    s.text(410, 28, 'Bucle de ejecución del Agente autónomo', size=FS_TITLE, bold=True)

    s.rect(80, 60, 500, 380, fill='white', stroke='border', rx=8, dash=True)
    s.text(330, 82, 'while not done:', size=FS_BODY, bold=True)

    s.rect(120, 100, 420, 60, fill='#e8e8e8')
    s.text(130, 115, '① Pensar (Razonamiento)', size=FS_SMALL, bold=True, anchor='start')
    s.rect(130, 125, 400, 28, fill='code_bg', rx=4)
    s.mono(140, 140, '"Resultados insuficientes, se requieren más búsquedas"', size=FS_TINY)

    s.rect(120, 175, 420, 60, fill='light')
    s.text(130, 190, '② Actuar', size=FS_SMALL, bold=True, anchor='start')
    s.rect(130, 200, 400, 28, fill='code_bg', rx=4)
    s.mono(140, 215, 'web_search("Técnicas de entrenamiento RL Agentes 2025")', size=FS_TINY)
    s.arrow(330, 162, 330, 173)

    s.rect(120, 250, 420, 60, fill='light')
    s.text(130, 265, '③ Observar', size=FS_SMALL, bold=True, anchor='start')
    s.rect(130, 275, 400, 28, fill='code_bg', rx=4)
    s.mono(140, 290, 'tool_result: "Encontrados 3 artículos relevantes..."', size=FS_TINY)
    s.arrow(330, 237, 330, 248)

    s.arrow_curved(540, 280, 540, 120, curve=-40, label='Continuar bucle', color='dark')

    s.group_box(610, 60, 190, 190, 'Condiciones de salida')
    exits = [
        '① Tarea completada',
        '② final_answer invocado',
        '③ Sin respuesta de herramienta',
        '④ Máximo de rondas alcanzado',
        '⑤ Límite de errores superado',
    ]
    for i, ex in enumerate(exits):
        s.text(620, 100 + i * 32, ex, size=FS_SMALL, anchor='start')

    s.rect(80, 360, 500, 70, fill='medium', rx=6)
    s.text(330, 380, 'Ejemplo de ejecución práctica: corrección SWE-bench', size=FS_SMALL, bold=True)
    s.text(330, 405, 'Buscar código → Hallar error → Editar → Probar → Fallo → Editar → Éxito', size=FS_TINY)
    s.text(330, 425, '(5 rondas de iteración, 12 llamadas a herramientas)', size=FS_TINY, fill='text_light')

    s.arrow(330, 312, 330, 358, label='done = True')

    s.save(f'{OUT}/fig1-10.svg')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    fig1_1()
    fig1_2()
    fig1_3()
    fig1_4()
    fig1_5()
    fig1_wf_chaining()
    fig1_wf_routing()
    fig1_wf_parallel()
    fig1_wf_orchestrator()
    fig1_wf_evaluator()
    print("Chapter 1 figures generated.")
