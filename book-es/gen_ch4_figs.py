"""Generate all SVG illustrations for Chapter 4 (Tools & MCP & Async)."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    SVG, COLORS, FS_TITLE, FS_BODY, FS_SMALL, FS_TINY,
)

OUT = os.path.join(os.path.dirname(__file__), 'images')


def _pill(svg, x, y, w, h, label, fill='light', font_size=FS_SMALL, bold=False):
    svg.rect(x, y, w, h, fill=fill, rx=h // 2)
    c = 'white' if fill in ('dark', 'darker') else 'text'
    svg.text(x + w / 2, y + h / 2, label, size=font_size, fill=c, bold=bold)


def fig4_1():
    """MCP protocol sequence diagram — Figure 4-1."""
    w, h = 880, 620
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Secuencia de interacción del protocolo MCP", size=FS_TITLE, bold=True)

    cl_x, sv_x = 200, 680
    svg.box(cl_x - 80, 50, 160, 44, "Cliente MCP", fill='medium', bold=True)
    svg.box(sv_x - 80, 50, 160, 44, "Servidor MCP", fill='medium', bold=True)
    svg.line(cl_x, 94, cl_x, 600, color='dark', dash=True)
    svg.line(sv_x, 94, sv_x, 600, color='dark', dash=True)

    y = 130
    svg.arrow(cl_x + 4, y, sv_x - 4, y)
    svg.text((cl_x + sv_x) / 2, y - 14, "initialize", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"method": "initialize",',
        ' "capabilities": {"tools": true}}',
    ], font_size=FS_TINY, line_h=18)

    y = 200
    svg.arrow(sv_x - 4, y, cl_x + 4, y, dash=True)
    svg.text((cl_x + sv_x) / 2, y - 14, "respuesta initialize", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"serverInfo": {"name": "weather-server"},',
        ' "capabilities": {"tools": {"listChanged":true}}}',
    ], font_size=FS_TINY, line_h=18)

    y = 280
    svg.arrow(cl_x + 4, y, sv_x - 4, y)
    svg.text((cl_x + sv_x) / 2, y - 14, "tools/list", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"method": "tools/list"}',
    ], font_size=FS_TINY, line_h=18)

    y = 340
    svg.arrow(sv_x - 4, y, cl_x + 4, y, dash=True)
    svg.text((cl_x + sv_x) / 2, y - 14, "respuesta tools/list", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 10, y + 6, 400, [
        '{"tools": [{"name": "get_weather",',
        '  "inputSchema": {"city": "string"}}]}',
    ], font_size=FS_TINY, line_h=18)

    y = 420
    svg.arrow(cl_x + 4, y, sv_x - 4, y)
    svg.text((cl_x + sv_x) / 2, y - 14, "tools/call", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"method": "tools/call",',
        ' "params": {"name": "get_weather",',
        '  "arguments": {"city": "Beijing"}}}',
    ], font_size=FS_TINY, line_h=18)

    y = 510
    svg.arrow(sv_x - 4, y, cl_x + 4, y, dash=True)
    svg.text((cl_x + sv_x) / 2, y - 14, "resultado tools/call", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"content": [{"type": "text",',
        '  "text": "Beijing: 22°C, despejado"}]}',
    ], font_size=FS_TINY, line_h=18)

    svg.text(50, 165, "① Negociación", size=FS_SMALL, bold=True, fill='text_light')
    svg.text(50, 310, "② Descubrimiento", size=FS_SMALL, bold=True, fill='text_light')
    svg.text(50, 465, "③ Invocación", size=FS_SMALL, bold=True, fill='text_light')

    svg.save(os.path.join(OUT, 'fig4-1.svg'))


def fig4_2():
    """Sub-Agent context preparation — Figure 4-2."""
    w, h = 880, 530
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Estrategias de transferencia de contexto para Subagentes", size=FS_TITLE, bold=True)

    strategies = [
        ("Transferencia mínima", "dark",
         '"Consultar estado de pedido 12345"',
         "Cero contexto → privacidad y seguridad"),
        ("Filtrado y trans. manual", "medium",
         '"Región: ES\\nResumen: Consulta reembolso"',
         "Selección explícita → controlable"),
        ("Recorte y trans. aut.", "light",
         '"Info usuario + últimas 3 rondas\\n+ res. herramientas"',
         "Basado en reglas → equilibrado"),
        ("Contexto generado por LLM", "code_bg",
         '"LLM analiza trayectoria\\n→ objeto contexto estructurado"',
         "Más inteligente → 1 llamada extra"),
    ]

    col_w = 190
    gap = 18
    start_x = (w - 4 * col_w - 3 * gap) / 2

    svg.box(w / 2 - 100, 55, 200, 44, "Agente principal", fill='medium', bold=True)
    svg.text(w / 2, 118, "¿Cómo preparar el contexto para el Subagente?", size=FS_SMALL, fill='text_light')

    for i, (title, fill, example, note) in enumerate(strategies):
        x = start_x + i * (col_w + gap)
        top_y = 145

        svg.arrow(w / 2, 99, x + col_w / 2, top_y - 2)

        svg.rect(x, top_y, col_w, 36, fill=fill)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(x + col_w / 2, top_y + 18, title, size=FS_SMALL, bold=True, fill=tc)

        svg.rect(x, top_y + 46, col_w, 80, fill='code_bg', stroke='dark', rx=4)
        for j, line in enumerate(example.split('\\n')):
            svg.mono(x + 8, top_y + 70 + j * 20, line, size=FS_TINY)

        svg.text(x + col_w / 2, top_y + 150, note, size=FS_TINY, fill='text_light')

        svg.box(x + 15, top_y + 175, col_w - 30, 36, "Subagente", fill='light', font_size=FS_SMALL)

    svg.line(30, 395, w - 30, 395, color='dark', dash=True)
    svg.text(w / 2, 418, "Guía de selección", size=FS_BODY, bold=True)

    guides = [
        ("Llamadas simples alta frec.", "Consulta clima, calculadora", "→ Mínima"),
        ("Complejidad media", "Consulta datos, proc. archivos", "→ Recorte automático"),
        ("Tareas complejas", "Generar informe, atención al cliente", "→ Generación LLM"),
    ]
    gx = 80
    for label, example, rec in guides:
        svg.rect(gx, 438, 230, 70, fill='light')
        svg.text(gx + 115, 458, label, size=FS_SMALL, bold=True)
        svg.text(gx + 115, 478, example, size=FS_TINY, fill='text_light')
        svg.text(gx + 115, 498, rec, size=FS_SMALL, bold=True, fill='darker')
        gx += 260

    svg.save(os.path.join(OUT, 'fig4-2.svg'))


def fig4_3():
    """Event-driven architecture — Figure 4-3."""
    w, h = 880, 540
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Arquitectura de Agente asíncrona orientada a eventos", size=FS_TITLE, bold=True)

    sources = [
        ("Email", 'on_email_reply', '{"from":"alice@...",\n "subject":"Re:reunión"}'),
        ("Temporizador", 'on_timer_expire', '{"task_id":"daily_report",\n "scheduled":"09:00"}'),
        ("Webhook", 'on_webhook', '{"repo":"agent-lib",\n "event":"pr_merged"}'),
        ("Usuario", 'on_user_message', '{"text":"Ver clima\nmañana"}'),
    ]

    src_x, src_w = 20, 155
    svg.text(src_x + src_w / 2, 65, "Fuente de eventos", size=FS_BODY, bold=True)
    for i, (name, event_type, payload) in enumerate(sources):
        y = 85 + i * 110
        svg.box(src_x, y, src_w, 40, name, fill='medium', bold=True, font_size=FS_SMALL)
        svg.mono(src_x + 5, y + 56, event_type, size=FS_TINY)
        for j, pl in enumerate(payload.split('\n')):
            svg.mono(src_x + 5, y + 74 + j * 16, pl, size=11)

    q_x, q_w = 215, 190
    svg.text(q_x + q_w / 2, 65, "Cola de eventos", size=FS_BODY, bold=True)
    svg.rect(q_x, 85, q_w, 390, fill='white', stroke='border', dash=True)

    queue_events = [
        ("user.input", "Prioridad: normal", 'light'),
        ("email.reply", "Prioridad: normal", 'light'),
        ("user.interrupt", "Prioridad: ¡urgente!", 'dark'),
        ("timer.trigger", "Prioridad: normal", 'light'),
    ]
    for i, (evt, pri, fill) in enumerate(queue_events):
        ey = 105 + i * 85
        svg.rect(q_x + 10, ey, q_w - 20, 60, fill=fill, rx=4)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(q_x + q_w / 2, ey + 22, evt, size=FS_SMALL, bold=True, fill=tc)
        svg.text(q_x + q_w / 2, ey + 44, pri, size=FS_TINY, fill='white' if fill == 'dark' else 'text_light')

    for i in range(4):
        sy = 105 + i * 110
        svg.arrow(src_x + src_w + 2, sy, q_x - 2, 120 + i * 85)

    ag_x = 450
    svg.text(ag_x + 200, 65, "Flujo de procesamiento del Agente", size=FS_BODY, bold=True)

    svg.arrow(q_x + q_w + 2, 280, ag_x - 2, 280, label="Obtener evento")

    steps = [
        ("Enrutador", "El LLM determina la urgencia", 'medium'),
        ("Añadir a trayectoria", "Formato de evento estructurado", 'light'),
        ("Inferencia LLM", "Observar → Pensar → Actuar", 'light'),
        ("Ejecutar herramienta", "Despacho async/sync", 'light'),
        ("Procesar resultado", "Notificar/responder/guardar", 'medium'),
    ]

    step_w, step_h = 360, 50
    for i, (title, desc, fill) in enumerate(steps):
        sy = 110 + i * 80
        svg.rect(ag_x, sy, step_w, step_h, fill=fill)
        svg.text(ag_x + 18, sy + step_h / 2, title, size=FS_SMALL, bold=True, anchor='start')
        svg.text(ag_x + step_w - 12, sy + step_h / 2, desc, size=FS_TINY, fill='text_light', anchor='end')
        if i < len(steps) - 1:
            svg.arrow(ag_x + step_w / 2, sy + step_h + 2, ag_x + step_w / 2, sy + 78)

    svg.arrow_curved(ag_x + step_w, 450, ag_x + step_w, 130, curve=45, label="Bucle", dash=True, color='dark')

    svg.save(os.path.join(OUT, 'fig4-3.svg'))


def fig4_4():
    """Async event handling — Figure 4-4."""
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Tres estrategias para el manejo de eventos", size=FS_TITLE, bold=True)

    lane_x = 130
    lane_w = 720
    tl_x0 = lane_x + 10
    tl_w = lane_w - 20

    def time_bar(y, x_start_pct, x_end_pct, fill, label, h_bar=28):
        xs = tl_x0 + tl_w * x_start_pct
        xe = tl_x0 + tl_w * x_end_pct
        svg.rect(xs, y, xe - xs, h_bar, fill=fill, rx=4)
        svg.text((xs + xe) / 2, y + h_bar / 2, label, size=FS_TINY,
                 fill='white' if fill in ('dark', 'darker') else 'text')

    svg.text(tl_x0 + tl_w * 0.25, 55, "t₁", size=FS_SMALL, fill='text_light')
    svg.text(tl_x0 + tl_w * 0.50, 55, "t₂", size=FS_SMALL, fill='text_light')
    svg.text(tl_x0 + tl_w * 0.75, 55, "t₃", size=FS_SMALL, fill='text_light')

    y1 = 80
    svg.rect(lane_x, y1, lane_w, 140, fill='white', stroke='border', dash=True)
    svg.text(lane_x / 2, y1 + 70, "Cancelación", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y1 + 95, "(Urgente)", size=FS_SMALL, fill='text_light')

    time_bar(y1 + 15, 0.0, 0.40, 'medium', 'Razonamiento LLM...')
    svg.line(tl_x0 + tl_w * 0.40, y1 + 10, tl_x0 + tl_w * 0.40, y1 + 130, color='border', dash=True)
    svg.text(tl_x0 + tl_w * 0.40, y1 + 10, "⚡ user.interrupt: \"¡Detener!\"", size=FS_TINY, bold=True)
    time_bar(y1 + 15, 0.40, 0.45, 'dark', '×', h_bar=28)

    time_bar(y1 + 55, 0.0, 0.35, 'light', 'Ejecutando herramienta...')
    time_bar(y1 + 55, 0.40, 0.45, 'dark', '×', h_bar=28)

    time_bar(y1 + 95, 0.47, 1.0, 'medium', 'Nuevo razonamiento LLM (evento interrupción + cola limpia)')

    y2 = 240
    svg.rect(lane_x, y2, lane_w, 140, fill='white', stroke='border', dash=True)
    svg.text(lane_x / 2, y2 + 70, "En encolamiento", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y2 + 95, "(Normal)", size=FS_SMALL, fill='text_light')

    time_bar(y2 + 15, 0.0, 0.15, 'medium', 'LLM', h_bar=24)
    time_bar(y2 + 15, 0.18, 0.60, 'light', 'Ejecución herramienta (search_web)')
    time_bar(y2 + 15, 0.63, 0.90, 'medium', 'Procesamiento exhaustivo LLM')

    svg.line(tl_x0 + tl_w * 0.35, y2 + 46, tl_x0 + tl_w * 0.35, y2 + 130, color='dark', dash=True)
    svg.text(tl_x0 + tl_w * 0.35, y2 + 58, "user: \"Solo mirar último mes\"", size=FS_TINY, fill='text_light')

    _pill(svg, tl_x0 + tl_w * 0.30, y2 + 65, 150, 24, "Encolado, esperando", fill='light', font_size=FS_TINY)

    time_bar(y2 + 100, 0.63, 0.68, 'dark', '', h_bar=20)
    svg.text(tl_x0 + tl_w * 0.61, y2 + 110, "Inyección por lotes: tool.result + entrada usuario", size=FS_TINY, fill='text_light', anchor='end')

    y3 = 400
    svg.rect(lane_x, y3, lane_w, 140, fill='white', stroke='border', dash=True)
    svg.text(lane_x / 2, y3 + 70, "Paralelo", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y3 + 95, "(Independiente)", size=FS_SMALL, fill='text_light')

    time_bar(y3 + 15, 0.0, 0.80, 'light', 'Tarea principal: Análisis de datos (ejecución larga)')

    svg.line(tl_x0 + tl_w * 0.30, y3 + 50, tl_x0 + tl_w * 0.30, y3 + 130, color='dark', dash=True)
    svg.text(tl_x0 + tl_w * 0.30, y3 + 58, "user: \"¿Clima hoy?\"", size=FS_TINY, fill='text_light')

    time_bar(y3 + 70, 0.32, 0.50, 'medium', 'LLM paralelo', h_bar=24)
    time_bar(y3 + 70, 0.52, 0.62, 'dark', 'Clima', h_bar=24)

    svg.text(tl_x0 + tl_w * 0.635, y3 + 82, "→ Responder al usuario de inmediato", size=FS_TINY, fill='text_light', anchor='start')
    svg.text(tl_x0 + tl_w * 0.50, y3 + 115, "Etiqueta: [En paralelo con tarea principal]", size=FS_TINY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig4-4.svg'))


def fig4_5():
    """Experiment 4.4 — Figure 4-5."""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experimento 4.4: Arquitectura de Agente orientada a eventos", size=FS_TITLE, bold=True)

    src_data = [
        ("on_user_message", "Web/App"),
        ("on_email_reply", "Sistema de email"),
        ("on_github_pr_update", "GitHub"),
        ("on_timer_expire", "Temporizador"),
        ("on_webhook_received", "Webhook"),
        ("on_resource_alert", "Alerta de sistema"),
    ]
    svg.text(85, 65, "Fuente de eventos externa", size=FS_BODY, bold=True)
    for i, (evt, src) in enumerate(src_data):
        y = 82 + i * 58
        svg.rect(10, y, 150, 44, fill='light')
        svg.text(85, y + 16, src, size=FS_SMALL, bold=True)
        svg.mono(15, y + 36, evt, size=11)

    svg.rect(200, 80, 200, 390, fill='white', stroke='border', dash=True)
    svg.text(300, 100, "Servidor FastAPI", size=FS_BODY, bold=True)

    svg.rect(215, 120, 170, 50, fill='medium')
    svg.text(300, 137, "Endpoint HTTP", size=FS_SMALL, bold=True)
    svg.text(300, 157, "POST /events/{type}", size=FS_TINY, fill='text_light')

    svg.rect(215, 190, 170, 50, fill='light')
    svg.text(300, 207, "Enrutador de eventos", size=FS_SMALL, bold=True)
    svg.text(300, 227, "LLM determina urgencia", size=FS_TINY, fill='text_light')

    svg.rect(215, 260, 170, 50, fill='light')
    svg.text(300, 277, "Cola de eventos", size=FS_SMALL, bold=True)
    svg.text(300, 297, "Orden por prioridad", size=FS_TINY, fill='text_light')

    svg.rect(215, 330, 170, 50, fill='light')
    svg.text(300, 347, "Bucle del Agente", size=FS_SMALL, bold=True)
    svg.text(300, 367, "Obtener → Razonar → Ejecutar", size=FS_TINY, fill='text_light')

    svg.rect(215, 400, 170, 50, fill='medium')
    svg.text(300, 417, "Gestión de sesiones", size=FS_SMALL, bold=True)
    svg.text(300, 437, "Contexto multihilo", size=FS_TINY, fill='text_light')

    for i in range(4):
        svg.arrow(300, 170 + i * 70, 300, 190 + i * 70)

    for i in range(6):
        svg.arrow(160, 104 + i * 58, 213, 145)

    svg.text(610, 65, "Servidor de herramientas MCP", size=FS_BODY, bold=True)

    tools = [
        ("Herramientas percepción", "search_web, read_file\nread_webpage, parse_image"),
        ("Herramienta ejecución", "code_interpreter\nvirtual_terminal, write_file"),
        ("Herramienta colaboración", "browser_use\nrequest_human_approval"),
        ("Herramienta notificación", "send_email, send_slack\nsend_im_notification"),
    ]
    for i, (name, desc) in enumerate(tools):
        y = 82 + i * 100
        svg.rect(460, y, 250, 80, fill='light')
        svg.text(585, y + 22, name, size=FS_SMALL, bold=True)
        for j, line in enumerate(desc.split('\n')):
            svg.mono(470, y + 48 + j * 18, line, size=12)

    svg.arrow(400, 355, 458, 180)
    svg.arrow(458, 260, 400, 355)

    svg.rect(740, 82, 130, 380, fill='code_bg', stroke='dark', rx=4)
    svg.text(805, 115, "Capa persistente", size=FS_SMALL, bold=True)
    items = ["historial chat", "registro eventos", "tarea progr.", "est. herram.", "trazabilidad"]
    for i, item in enumerate(items):
        svg.text(805, 160 + i * 55, item, size=FS_SMALL)

    svg.save(os.path.join(OUT, 'fig4-5.svg'))


def fig4_6():
    """sync-async model contradiction — Figure 4-6."""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Contradicción: paradigma síncrono vs realidad asíncrona", size=FS_TITLE, bold=True)

    svg.rect(20, 55, w - 40, 195, fill='white', stroke='border', dash=True)
    svg.text(60, 78, "Paradigma de entrenamiento (secuencia estrictamente síncrona)", size=FS_BODY, bold=True, anchor='start')
    _pill(svg, w - 200, 64, 160, 28, "Restricción API", fill='dark', font_size=FS_SMALL)

    steps_train = [
        ("Observación", 'medium', "Usuario: Verificar clima en Pekín"),
        ("Pensamiento", 'light', "Se requiere llamar a get_weather"),
        ("Acción", 'medium', "get_weather(Pekín)"),
        ("Observación", 'light', "22°C, despejado"),
    ]
    bw, bh, gap = 180, 55, 22
    sx = (w - (4 * bw + 3 * gap)) / 2
    for i, (phase, fill, content) in enumerate(steps_train):
        x = sx + i * (bw + gap)
        svg.rect(x, 100, bw, bh, fill=fill)
        svg.text(x + bw / 2, 120, phase, size=FS_SMALL, bold=True)
        svg.text(x + bw / 2, 142, content, size=FS_TINY, fill='text_light')
        if i < 3:
            svg.arrow(x + bw + 2, 128, x + bw + gap - 2, 128)

    svg.rect(sx, 170, 4 * bw + 3 * gap, 30, fill='code_bg', stroke='dark', rx=4)
    svg.mono(sx + 10, 185,
             "tool_call → debe ir seguido inmediatamente de tool_result, o error de API", size=FS_TINY)

    svg.line(20, 262, w - 20, 262, color='dark', dash=True)
    svg.text(w / 2, 280, "Contradicción", size=FS_BODY, bold=True, fill='darker')

    svg.rect(20, 295, w - 40, 210, fill='white', stroke='border', dash=True)
    svg.text(60, 318, "Realidad de despliegue (eventos asíncronos entrelazados)", size=FS_BODY, bold=True, anchor='start')
    _pill(svg, w - 200, 304, 160, 28, "¡Conflicto de formato!", fill='dark', font_size=FS_SMALL)

    items = [
        ("Asistente", 'medium', "tool_call:\nget_weather(Pekín)", 0.0, 0.20),
        ("Esperando...", 'code_bg', "Ejecución herramienta ~5s", 0.22, 0.50),
        ("Usuario interrumpe", 'dark', "\"No importa, \nmira Shanghái\"", 0.40, 0.55),
        ("???", 'code_bg', "¿Cuándo llega tool_result? \n¿Cómo preservar formato?", 0.57, 0.78),
        ("Marcador", 'light', "[Herramienta ejecutando, \nprioridad a interrupción]", 0.80, 1.0),
    ]

    tl_x0, tl_w = 50, w - 100
    for role, fill, txt, t0, t1 in items:
        x0 = tl_x0 + tl_w * t0
        x1 = tl_x0 + tl_w * t1
        svg.rect(x0, 340, x1 - x0, 50, fill=fill, rx=4)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text((x0 + x1) / 2, 355, role, size=FS_TINY, bold=True, fill=tc)
        for j, tl in enumerate(txt.split('\n')):
            svg.text((x0 + x1) / 2, 372 + j * 14, tl, size=11, fill=tc)

    svg.rect(50, 410, w - 100, 40, fill='code_bg', stroke='dark', rx=4)
    svg.mono(60, 430,
             "Solución: preservar formato con marcadores + encolar no urgentes + interrumpir solo si es urgente",
             size=FS_TINY)

    svg.rect(140, 465, w - 280, 40, fill='dark')
    svg.text(w / 2, 485,
             "Solución de fondo: los modelos futuros deben entrenarse con RL en entornos asíncronos",
             size=FS_SMALL, fill='white', bold=True)

    svg.save(os.path.join(OUT, 'fig4-6.svg'))


def fig4_7():
    """Experiment 4.5 — Figure 4-7."""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experimento 4.5: Interrupción y recuperación en Agente asíncrono", size=FS_TITLE, bold=True)

    tl_x0, tl_w = 120, 740

    lanes = [
        ("Agente", 80),
        ("Herramienta A", 180),
        ("Herramienta B", 260),
        ("Herramienta C", 340),
        ("Trayectoria", 420),
    ]
    for name, y in lanes:
        svg.text(55, y, name, size=FS_SMALL, bold=True)
        svg.line(tl_x0, y, tl_x0 + tl_w, y, color='dark', dash=True)

    def tbar(y, t0, t1, fill, label, h_bar=22):
        xs = tl_x0 + tl_w * t0
        xe = tl_x0 + tl_w * t1
        svg.rect(xs, y - h_bar / 2, xe - xs, h_bar, fill=fill, rx=3)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text((xs + xe) / 2, y, label, size=11, fill=tc)

    tbar(80, 0.0, 0.12, 'medium', 'LLM: Iniciar 3 herramientas')

    tbar(180, 0.13, 0.45, 'light', 'Script A: 3%/s → completa en 33s')
    tbar(260, 0.13, 0.70, 'light', 'Script B: 2%/s → 50s...')
    tbar(340, 0.13, 0.90, 'code_bg', 'Script C: 1%/s → 100s...')

    t_done = 0.45
    svg.line(tl_x0 + tl_w * t_done, 70, tl_x0 + tl_w * t_done, 450, color='border', dash=True)
    svg.text(tl_x0 + tl_w * t_done, 62, "A completado", size=FS_TINY, bold=True)

    tbar(80, 0.46, 0.58, 'medium', 'Consultar avance B, C')
    tbar(420, 0.46, 0.58, 'light', 'B≈66% C≈33%')

    t_cancel = 0.60
    svg.line(tl_x0 + tl_w * t_cancel, 70, tl_x0 + tl_w * t_cancel, 450, color='dark', dash=True)
    svg.text(tl_x0 + tl_w * t_cancel, 62, "Cancelar C", size=FS_TINY, bold=True, fill='darker')

    tbar(340, 0.60, 0.65, 'dark', '×')

    t_b_done = 0.70
    svg.line(tl_x0 + tl_w * t_b_done, 70, tl_x0 + tl_w * t_b_done, 450, color='border', dash=True)
    svg.text(tl_x0 + tl_w * t_b_done, 62, "B completado", size=FS_TINY, bold=True)

    tbar(80, 0.72, 0.95, 'medium', 'LLM: Combinar res. A+B y generar informe')
    tbar(420, 0.72, 0.95, 'light', 'Res. A + Res. B + Reg. cancelación C')

    svg.rect(tl_x0, 460, tl_w, 40, fill='code_bg', stroke='dark', rx=4)
    svg.mono(tl_x0 + 10, 480,
             "Clave: inyección marcadores + evento finalización async + API cancel_tool(task_id)",
             size=FS_TINY)

    svg.save(os.path.join(OUT, 'fig4-7.svg'))


def fig4_8():
    """Tool discovery hierarchy — Figure 4-8."""
    w, h = 880, 540
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Coincidencia jerárquica de herramientas", size=FS_TITLE, bold=True)

    svg.rect(250, 55, 380, 44, fill='medium')
    svg.text(440, 77, "Agente: \"Necesito consultar estadísticas de colaboradores en GitHub\"", size=FS_SMALL, bold=True)

    svg.arrow(440, 99, 440, 130)

    svg.rect(300, 132, 280, 44, fill='dark')
    svg.text(440, 154, "discover_tools(req_lenguaje_natural)", size=FS_SMALL, fill='white', bold=True)

    svg.arrow(440, 176, 440, 210)

    svg.rect(20, 210, w - 40, 110, fill='white', stroke='border', dash=True)
    svg.text(55, 233, "Capa 1: Coincidencia de servidor (similitud semántica)", size=FS_BODY, bold=True, anchor='start')

    servers = [
        ("GitHub", 0.92, 'dark'),
        ("Clima", 0.15, 'light'),
        ("Finanzas", 0.23, 'light'),
        ("ArXiv", 0.18, 'light'),
        ("Sistema arch.", 0.31, 'light'),
    ]
    sx = 50
    for name, score, fill in servers:
        svg.rect(sx, 255, 145, 50, fill=fill)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(sx + 72, 272, name, size=FS_SMALL, bold=True, fill=tc)
        svg.text(sx + 72, 292, f"Similitud: {score:.2f}", size=FS_TINY, fill='white' if fill == 'dark' else 'text_light')
        sx += 165

    svg.arrow(123, 305, 123, 345)
    svg.text(175, 330, "Top 1 servidor", size=FS_SMALL, fill='text_light')

    svg.rect(20, 345, w - 40, 160, fill='white', stroke='border', dash=True)
    svg.text(55, 368, "Capa 2: Coincidencia de herramientas (26 herramientas en servidor GitHub)", size=FS_BODY, bold=True, anchor='start')

    tools = [
        ("search_repositories", 0.41, "Buscar repos"),
        ("list_contributors", 0.89, "Lista colaboradores"),
        ("get_repo_stats", 0.85, "Estadísticas repo"),
        ("create_issue", 0.12, "Crear issue"),
        ("get_commit_history", 0.67, "Historial commits"),
    ]
    tx = 30
    for name, score, desc in tools:
        is_top = score > 0.80
        fill = 'dark' if is_top else 'light'
        svg.rect(tx, 388, 155, 55, fill=fill)
        tc = 'white' if is_top else 'text'
        svg.mono(tx + 5, 406, name, size=11, fill=tc)
        svg.text(tx + 78, 428, f"{score:.2f} | {desc}", size=11, fill='white' if is_top else 'text_light')
        tx += 170

    svg.rect(180, 468, 520, 30, fill='code_bg', stroke='dark', rx=4)
    svg.mono(190, 483, "Devolver top 3: list_contributors, get_repo_stats, get_commit_history", size=12)

    svg.save(os.path.join(OUT, 'fig4-8.svg'))


def fig4_9():
    """KV Cache Optimization — Figure 4-9."""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Optimización de KV Cache para carga dinámica de herramientas", size=FS_TITLE, bold=True)

    left_x = 30
    svg.text(220, 65, "Enfoque ingenuo (la caché se invalida)", size=FS_BODY, bold=True)

    blocks_naive = [
        ("Prompt del sistema", 120, 'medium', "Eres un asistente de IA...\n+ Esquemas de todas las herramientas", "~50K tokens"),
        ("Mensaje del usuario", 100, 'light', "Consultar precio de acción NVDA", ""),
        ("Asistente", 80, 'light', "tool_call: ...", ""),
    ]
    ny = 85
    for label, bh, fill, content, note in blocks_naive:
        svg.rect(left_x, ny, 380, bh, fill=fill, rx=4)
        svg.text(left_x + 190, ny + 22, label, size=FS_SMALL, bold=True)
        for j, line in enumerate(content.split('\n')):
            svg.text(left_x + 190, ny + 44 + j * 20, line, size=FS_TINY, fill='text_light')
        if note:
            svg.text(left_x + 360, ny + 22, note, size=FS_TINY, fill='darker', anchor='end')
        ny += bh + 8

    svg.rect(left_x, ny + 5, 380, 40, fill='dark')
    svg.text(left_x + 190, ny + 25, "¡Cada vez que se carga una herramienta → se invalida la caché!", size=FS_SMALL, fill='white', bold=True)

    right_x = 460
    svg.text(660, 65, "Enfoque optimizado (estabilidad de caché)", size=FS_BODY, bold=True)

    blocks_opt = [
        ("Prompt del sistema (fijo)", 75, 'medium',
         "Eres un asistente de IA...\nRol + Reglas + Herramientas básicas",
         "~2K tokens | KV Cache"),
        ("Barra estado Agente (ligera)", 45, 'code_bg',
         "Herramientas disps: web_search, get_weather...",
         "~200 tokens"),
        ("User: discover_tools", 40, 'light',
         '"Necesito revisar precio de acciones"',
         ""),
        ("Resultado herramienta", 55, 'light',
         "Devolver esquema de get_stock_quote",
         "Definición de herramienta aquí"),
        ("Mensaje del usuario", 40, 'light',
         "Consultar precio de acción NVDA",
         ""),
        ("Barra estado Agente (actualizada)", 45, 'code_bg',
         "+get_stock_quote añadido",
         "~220 tokens"),
    ]
    oy = 85
    for label, bh, fill, content, note in blocks_opt:
        svg.rect(right_x, oy, 400, bh, fill=fill, rx=4)
        svg.text(right_x + 200, oy + 16, label, size=FS_SMALL, bold=True)
        for j, line in enumerate(content.split('\n')):
            svg.text(right_x + 200, oy + 32 + j * 16, line, size=FS_TINY, fill='text_light')
        if note:
            svg.text(right_x + 390, oy + 16, note, size=11, fill='darker', anchor='end')
        oy += bh + 5

    svg.rect(right_x, oy + 5, 400, 40, fill='medium')
    svg.text(right_x + 200, oy + 25, "Prompt sistema no cambia → KV Cache se reutiliza totalmente", size=FS_SMALL, bold=True)

    svg.line(30, 475, w - 30, 475, color='dark', dash=True)
    comps = [
        ("Tasa acierto de caché", "~0% (se invalida en cada cambio)", "~95% (solo cambia ligeramente la pista)"),
        ("Latencia primer token", "Alta (recálculo 50K tokens cada vez)", "Baja (cómputo incremental ~200 tokens)"),
    ]
    cy = 495
    svg.text(250, cy, "Dimensión de comparación", size=FS_SMALL, bold=True)
    svg.text(500, cy, "Enfoque ingenuo", size=FS_SMALL, bold=True)
    svg.text(740, cy, "Enfoque optimizado", size=FS_SMALL, bold=True)
    for metric, naive, opt in comps:
        cy += 28
        svg.text(250, cy, metric, size=FS_TINY)
        svg.text(500, cy, naive, size=FS_TINY, fill='text_light')
        svg.text(740, cy, opt, size=FS_TINY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig4-9.svg'))


def fig4_10():
    """Tool Self-Evolution Pipeline — Figure 4-10."""
    w, h = 880, 500
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Autoevolución del Agente: de requisito a herramienta", size=FS_TITLE, bold=True)

    stages = [
        ("① Detección requisito", 'medium', [
            "Tarea: Extraer subtítulos YouTube",
            "Agente: Herramientas insufic.",
            "→ Iniciar autoevolución",
        ]),
        ("② Búsqueda web", 'light', [
            "search: youtube transcript",
            "python library",
            "→ 3 librerías candidatas",
        ]),
        ("③ Exploración GitHub", 'light', [
            "Visitar repo jdepoix/youtube-",
            "transcript-api",
            "→ Leer README + ejemplos",
        ]),
        ("④ Aprendizaje y prueba", 'light', [
            "Prueba code_interpreter:",
            "from youtube_transcript",
            "  _api import ...",
        ]),
        ("⑤ Encapsular herramienta", 'medium', [
            "Crear herramienta MCP:",
            "get_youtube_transcript",
            "(video_id) → texto",
        ]),
    ]

    stage_w, stage_h = 155, 145
    gap = 12
    total_w = len(stages) * stage_w + (len(stages) - 1) * gap
    sx = (w - total_w) / 2

    for i, (title, fill, details) in enumerate(stages):
        x = sx + i * (stage_w + gap)
        svg.rect(x, 60, stage_w, stage_h, fill=fill)
        svg.text(x + stage_w / 2, 82, title, size=FS_SMALL, bold=True)
        svg.line(x + 10, 94, x + stage_w - 10, 94, color='dark')
        for j, line in enumerate(details):
            svg.mono(x + 8, 114 + j * 20, line, size=11)
        if i < len(stages) - 1:
            svg.arrow(x + stage_w + 2, 60 + stage_h / 2, x + stage_w + gap - 2, 60 + stage_h / 2)

    svg.arrow(w / 2, 205, w / 2, 240)

    svg.rect(120, 240, w - 240, 50, fill='dark')
    svg.text(w / 2, 265, "⑥ Guardar en biblioteca de herramientas → reutilizar directamente en el futuro", size=FS_BODY, fill='white', bold=True)

    svg.arrow(w / 2, 290, w / 2, 320)
    svg.rect(60, 320, w - 120, 160, fill='white', stroke='border', dash=True)
    svg.text(w / 2, 345, "Reutilización de herramienta: siguiente encuentro con tarea similar", size=FS_BODY, bold=True)

    svg.rect(80, 365, 340, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(90, 382, "Agente: \"Necesito extraer subtítulos de YouTube\"", size=FS_TINY)
    svg.mono(90, 400, "→ search_tools(\"youtube transcript\")", size=FS_TINY)

    svg.arrow(420, 390, 460, 390)

    svg.rect(460, 365, 330, 50, fill='light')
    svg.text(625, 382, "¡Encontrada! get_youtube_transcript", size=FS_SMALL, bold=True)
    svg.text(625, 402, "Omitir búsqueda y creación, llamar directamente", size=FS_TINY, fill='text_light')

    svg.rect(200, 430, 480, 35, fill='medium')
    svg.text(w / 2, 448, "Capa herramientas + Capa conocimiento + Capa estrategia → mayor dominio con el uso", size=FS_SMALL, bold=True)

    svg.save(os.path.join(OUT, 'fig4-10.svg'))


def fig4_11():
    """Experiment 4.7 — Figure 4-11."""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experimento 4.7: Canalización de Agente autoevolutivo", size=FS_TITLE, bold=True)

    svg.rect(30, 60, w - 60, 48, fill='medium')
    svg.text(w / 2, 76, "Herramientas básicas (conjunto mínimo)", size=FS_SMALL, bold=True)
    base_tools = ["web_search", "read_webpage", "code_interpreter", "create_tool", "search_tools"]
    btx = 65
    for t in base_tools:
        tw = len(t) * 8 + 20
        _pill(svg, btx, 82, tw, 22, t, fill='dark', font_size=11, bold=True)
        btx += tw + 10

    svg.arrow(w / 2, 108, w / 2, 135)
    svg.rect(100, 135, w - 200, 45, fill='code_bg', stroke='dark', rx=4)
    svg.mono(110, 150,
             "Tarea: \"¿Precio reciente acción NVDA? ¿Cambio semanal?\" → Agente: ¡Sin herr. financiera!",
             size=FS_TINY)
    svg.mono(110, 168,
             "→ Detectar brecha de capacidad → Iniciar autoevolución",
             size=FS_TINY)

    svg.arrow(w / 2, 180, w / 2, 210)

    pipe_y = 210
    pipe_stages = [
        ("web_search", "Buscar soluciones", 'light',
         ["\"python stock price API\"",
          "→ yfinance, Alpha Vantage..."]),
        ("read_webpage", "Evaluar soluciones", 'light',
         ["yfinance: gratis, sin clave API",
          "Alpha Vantage: requiere registro..."]),
        ("code_interpreter", "Probar y verificar", 'light',
         ["import yfinance as yf",
          "yf.Ticker('NVDA').history()"]),
        ("create_tool", "Encapsular y registrar", 'medium',
         ["name: get_stock_data",
          "schema: {ticker, period}"]),
    ]

    pw = 190
    pgap = 15
    total_pw = len(pipe_stages) * pw + (len(pipe_stages) - 1) * pgap
    px = (w - total_pw) / 2
    for i, (tool, desc, fill, details) in enumerate(pipe_stages):
        svg.rect(px, pipe_y, pw, 120, fill=fill)
        _pill(svg, px + 10, pipe_y + 8, pw - 20, 22, tool, fill='dark', font_size=11, bold=True)
        svg.text(px + pw / 2, pipe_y + 48, desc, size=FS_SMALL, bold=True)
        for j, line in enumerate(details):
            svg.mono(px + 8, pipe_y + 70 + j * 18, line, size=11)
        if i < len(pipe_stages) - 1:
            svg.arrow(px + pw + 2, pipe_y + 60, px + pw + pgap - 2, pipe_y + 60)
        px += pw + pgap

    svg.arrow(w / 2, 330, w / 2, 360)
    svg.rect(200, 360, w - 400, 44, fill='dark')
    svg.text(w / 2, 382, "Biblioteca de herramientas: get_stock_data registrada", size=FS_BODY, fill='white', bold=True)

    svg.arrow(w / 2, 404, w / 2, 430)
    svg.rect(100, 430, w - 200, 40, fill='code_bg', stroke='dark', rx=4)
    svg.mono(110, 442,
             "Verificación de reutilización: \"Consultar acción TSLA\" → search_tools coincide → llama a get_stock_data",
             size=FS_TINY)
    svg.mono(110, 458,
             "Omitir búsqueda/evaluación/prueba → reducción de costo +90%",
             size=FS_TINY)

    svg.save(os.path.join(OUT, 'fig4-11.svg'))


def fig4_12():
    """Voyager learning loop — Figure 4-12."""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Voyager: Arquitectura de Agente para aprendizaje continuo", size=FS_TITLE, bold=True)

    svg.rect(20, 65, 260, 180, fill='white', stroke='border', dash=True)
    svg.text(150, 88, "Generador automático de plan", size=FS_BODY, bold=True)
    curriculum = [
        "Entrada: estado actual + habilidades",
        "Salida: siguiente objetivo de exploración",
        "",
        "Ejemplo secuencia objetivos:",
        "  Talar árbol → Crear tablas de madera",
        "  → Crear pico de madera → Minar piedra",
        "  → Hacer horno → Fundir mineral hierro",
    ]
    for i, line in enumerate(curriculum):
        svg.mono(32, 112 + i * 20, line, size=12)

    svg.rect(600, 65, 260, 180, fill='white', stroke='border', dash=True)
    svg.text(730, 88, "Mecanismo de prompt iterativo", size=FS_BODY, bold=True)
    iterative = [
        "Recopilar retroalim. en fallos:",
        "  - Observación entorno (error)",
        "  - Resultado autoverificación",
        "",
        "Integrar en prompt LLM",
        "→ Guiar refinamiento de código",
        "→ Iterar hasta tener éxito",
    ]
    for i, line in enumerate(iterative):
        svg.mono(612, 112 + i * 20, line, size=12)

    svg.arrow(280, 155, 370, 155, label="Objetivo")
    svg.arrow(560, 155, 600, 155, label="Retroalim.")

    svg.rect(370, 110, 190, 80, fill='medium')
    svg.text(465, 140, "Ejecución del Agente", size=FS_BODY, bold=True)
    svg.text(465, 165, "Generación código GPT-4", size=FS_SMALL, fill='text_light')

    svg.arrow(465, 190, 465, 260)
    svg.text(510, 230, "Éxito → Extraer", size=FS_SMALL, fill='text_light')

    svg.rect(120, 260, 640, 240, fill='white', stroke='border', dash=True)
    svg.text(440, 283, "Biblioteca de habilidades — núcleo del aprendizaje externalizado", size=FS_BODY, bold=True)

    skills = [
        ("chopTree()", "Talar árbol\nHabilidad básica", "function chopTree() {\n  bot.dig(nearest('log'));\n}"),
        ("craftPlanks()", "Crear tablas madera\nLlama a chopTree", "function craftPlanks() {\n  chopTree(); craft('planks');\n}"),
        ("craftPickaxe()", "Crear pico madera\nCombina habilidades", "function craftPickaxe() {\n  craftPlanks(); craft('stick');\n  craft('wooden_pickaxe');\n}"),
    ]
    skx = 140
    for name, desc, code in skills:
        svg.rect(skx, 305, 190, 175, fill='light')
        svg.text(skx + 95, 325, name, size=FS_SMALL, bold=True)
        for j, dl in enumerate(desc.split('\n')):
            svg.text(skx + 95, 347 + j * 18, dl, size=FS_TINY, fill='text_light')

        svg.rect(skx + 10, 385, 170, 80, fill='code_bg', stroke='dark', rx=4)
        for j, cl in enumerate(code.split('\n')):
            svg.mono(skx + 18, 400 + j * 18, cl, size=11)
        skx += 215

    svg.arrow_curved(120, 380, 150, 245, curve=60, label="Habilidades dispon.", dash=True, color='dark')

    svg.save(os.path.join(OUT, 'fig4-12.svg'))


def main():
    os.makedirs(OUT, exist_ok=True)
    figs = [
        fig4_1, fig4_2, fig4_3, fig4_4, fig4_5, fig4_6,
        fig4_7, fig4_8, fig4_9, fig4_10, fig4_11, fig4_12,
    ]
    for fn in figs:
        fn()
        print(f"  ✓ {fn.__name__}: {fn.__doc__}")
    print(f"\nGenerated {len(figs)} figures in {OUT}/")


if __name__ == '__main__':
    main()
