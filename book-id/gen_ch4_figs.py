#!/usr/bin/env python3
"""Generate all SVG illustrations for Chapter 4 (Tools).

Figures (9 total):
  fig4-1:  MCP protocol sequence diagram (concrete message payloads)
  fig4-2:  Event-driven architecture (real event sources & payloads)
  fig4-3:  Async event processing (cancellation/queued/parallel timing)
  fig4-4:  Exp 4.4 — Event-driven agent architecture
  fig4-5:  Sync-async model contradiction (training vs deployment)
  fig4-6:  Exp 4.5 — Async agent with interruption
  fig4-7:  Tool discovery hierarchy (server→tool matching)
  fig4-8:  KV cache optimization (system prompt stability)
  fig4-9:  Context structure after dynamic tool discovery (schemas scattered in trajectory)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    SVG, COLORS, FONT, MONO, STROKE_W, CORNER_R, _escape,
    FS_TITLE, FS_BODY, FS_SMALL, FS_TINY, FS_LABEL,
)

OUT = os.path.join(os.path.dirname(__file__), 'images')


def _pill(svg, x, y, w, h, label, fill='light', font_size=FS_SMALL, bold=False):
    svg.rect(x, y, w, h, fill=fill, rx=h // 2)
    c = 'white' if fill in ('dark', 'darker') else 'text'
    svg.text(x + w / 2, y + h / 2, label, size=font_size, fill=c, bold=bold)


def _seq_msg(svg, x1, x2, y, label, note=None, dash=False, note_side='above'):
    """Draw a sequence diagram message arrow with label."""
    svg.arrow(x1, y, x2, y, dash=dash)
    mid = (x1 + x2) / 2
    if note_side == 'above':
        svg.text(mid, y - 12, label, size=FS_SMALL, bold=True)
    else:
        svg.text(mid, y + 18, label, size=FS_SMALL, bold=True)
    if note:
        ny = y + 18 if note_side == 'above' else y + 34
        svg.text(mid, ny, note, size=FS_TINY, fill='text_light')


# ──────────────────────── fig4-1 ────────────────────────

def fig4_1():
    """MCP protocol sequence diagram (concrete message payloads)"""
    w, h = 880, 620
    svg = SVG(w, h)
    svg.text(w / 2, 30, "MCP protocol interaction sequence", size=FS_TITLE, bold=True)

    cl_x, sv_x = 200, 680
    svg.box(cl_x - 80, 50, 160, 44, "MCP Client", fill='medium', bold=True)
    svg.box(sv_x - 80, 50, 160, 44, "MCP Server", fill='medium', bold=True)
    svg.line(cl_x, 94, cl_x, 600, color='dark', dash=True)
    svg.line(sv_x, 94, sv_x, 600, color='dark', dash=True)

    # 1 initialize
    y = 130
    svg.arrow(cl_x + 4, y, sv_x - 4, y)
    svg.text((cl_x + sv_x) / 2, y - 14, "initialize", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"method": "initialize",',
        ' "capabilities": {"tools": true}}',
    ], font_size=FS_TINY, line_h=18)

    # 2 initialize response
    y = 200
    svg.arrow(sv_x - 4, y, cl_x + 4, y, dash=True)
    svg.text((cl_x + sv_x) / 2, y - 14, "initialize response", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"serverInfo": {"name": "weather-server"},',
        ' "capabilities": {"tools": {"listChanged":true}}}',
    ], font_size=FS_TINY, line_h=18)

    # 3 tools/list
    y = 280
    svg.arrow(cl_x + 4, y, sv_x - 4, y)
    svg.text((cl_x + sv_x) / 2, y - 14, "tools/list", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"method": "tools/list"}',
    ], font_size=FS_TINY, line_h=18)

    # 4 tools/list response
    y = 340
    svg.arrow(sv_x - 4, y, cl_x + 4, y, dash=True)
    svg.text((cl_x + sv_x) / 2, y - 14, "tools/list response", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 10, y + 6, 400, [
        '{"tools": [{"name": "get_weather",',
        '  "inputSchema": {"city": "string"}}]}',
    ], font_size=FS_TINY, line_h=18)

    # 5 tools/call
    y = 420
    svg.arrow(cl_x + 4, y, sv_x - 4, y)
    svg.text((cl_x + sv_x) / 2, y - 14, "tools/call", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"method": "tools/call",',
        ' "params": {"name": "get_weather",',
        '  "arguments": {"city": "Beijing"}}}',
    ], font_size=FS_TINY, line_h=18)

    # 6 tools/call response
    y = 510
    svg.arrow(sv_x - 4, y, cl_x + 4, y, dash=True)
    svg.text((cl_x + sv_x) / 2, y - 14, "tools/call result", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"content": [{"type": "text",',
        '  "text": "Beijing: 22°C, sunny"}]}',
    ], font_size=FS_TINY, line_h=18)

    # Phase labels on the left
    svg.text(50, 165, "① Handshake", size=FS_SMALL, bold=True, fill='text_light')
    svg.text(50, 310, "② Discovery", size=FS_SMALL, bold=True, fill='text_light')
    svg.text(50, 465, "③ Invocation", size=FS_SMALL, bold=True, fill='text_light')

    svg.save(os.path.join(OUT, 'fig4-1.svg'))


# ──────────────────────── fig4-2 ────────────────────────

def fig4_2():
    """Event-driven architecture (specific event source and payload)"""
    w, h = 880, 540
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Event-driven asynchronous Agent architecture", size=FS_TITLE, bold=True)

    # Left: Event sources
    sources = [
        ("Email", 'on_email_reply', '{"from":"alice@...",\n "subject":"Re:meeting"}'),
        ("Timer", 'on_timer_expire', '{"task_id":"daily_report",\n "scheduled":"09:00"}'),
        ("Webhook", 'on_webhook', '{"repo":"agent-lib",\n "event":"pr_merged"}'),
        ("User", 'on_user_message', '{"text":"Check tomorrow\'s weather for me\n"}'),
    ]

    src_x, src_w = 20, 155
    svg.text(src_x + src_w / 2, 65, "Event source", size=FS_BODY, bold=True)
    for i, (name, event_type, payload) in enumerate(sources):
        y = 85 + i * 110
        svg.box(src_x, y, src_w, 40, name, fill='medium', bold=True, font_size=FS_SMALL)
        svg.mono(src_x + 5, y + 56, event_type, size=FS_TINY)
        for j, pl in enumerate(payload.split('\n')):
            svg.mono(src_x + 5, y + 74 + j * 16, pl, size=11)

    # Middle: Event queue
    q_x, q_w = 215, 190
    svg.text(q_x + q_w / 2, 65, "Event queue", size=FS_BODY, bold=True)
    svg.rect(q_x, 85, q_w, 390, fill='white', stroke='border', dash=True)

    queue_events = [
        ("user.input", "Priority: normal", 'light'),
        ("email.reply", "Priority: normal", 'light'),
        ("user.interrupt", "Priority: urgent!", 'dark'),
        ("timer.trigger", "Priority: normal", 'light'),
    ]
    for i, (evt, pri, fill) in enumerate(queue_events):
        ey = 105 + i * 85
        svg.rect(q_x + 10, ey, q_w - 20, 60, fill=fill, rx=4)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(q_x + q_w / 2, ey + 22, evt, size=FS_SMALL, bold=True, fill=tc)
        svg.text(q_x + q_w / 2, ey + 44, pri, size=FS_TINY, fill='white' if fill == 'dark' else 'text_light')

    # Arrows from sources to queue
    for i in range(4):
        sy = 105 + i * 110
        svg.arrow(src_x + src_w + 2, sy, q_x - 2, 120 + i * 85)

    # Right: Agent processing
    ag_x = 450
    svg.text(ag_x + 200, 65, "Agent processing flow", size=FS_BODY, bold=True)

    svg.arrow(q_x + q_w + 2, 280, ag_x - 2, 280, label="Fetch event")

    steps = [
        ("Router", "LLM determines urgency", 'medium'),
        ("Append to trace", "Structured event format", 'light'),
        ("LLM inference", "Observe → Think → Act", 'light'),
        ("Tool execution", "Async/sync dispatch", 'light'),
        ("Result handling", "Notify/respond/store", 'medium'),
    ]

    step_w, step_h = 360, 50
    for i, (title, desc, fill) in enumerate(steps):
        sy = 110 + i * 80
        svg.rect(ag_x, sy, step_w, step_h, fill=fill)
        svg.text(ag_x + 18, sy + step_h / 2, title, size=FS_SMALL, bold=True, anchor='start')
        svg.text(ag_x + step_w - 12, sy + step_h / 2, desc, size=FS_TINY, fill='text_light', anchor='end')
        if i < len(steps) - 1:
            svg.arrow(ag_x + step_w / 2, sy + step_h + 2, ag_x + step_w / 2, sy + 78)

    # Feedback loop
    svg.arrow_curved(ag_x + step_w, 450, ag_x + step_w, 130, curve=45, label="Loop", dash=True, color='dark')

    svg.save(os.path.join(OUT, 'fig4-2.svg'))


# ──────────────────────── fig4-3 ────────────────────────

def fig4_3():
    """Async event handling: timing comparison of three strategies"""
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Three strategies for event handling", size=FS_TITLE, bold=True)

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

    # Timeline header
    svg.text(tl_x0 + tl_w * 0.25, 55, "t₁", size=FS_SMALL, fill='text_light')
    svg.text(tl_x0 + tl_w * 0.50, 55, "t₂", size=FS_SMALL, fill='text_light')
    svg.text(tl_x0 + tl_w * 0.75, 55, "t₃", size=FS_SMALL, fill='text_light')

    # ── Lane 1: Cancellation ──
    y1 = 80
    svg.rect(lane_x, y1, lane_w, 140, fill='white', stroke='border', dash=True)
    svg.text(lane_x / 2, y1 + 70, "Cancellation", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y1 + 95, "(Urgent)", size=FS_SMALL, fill='text_light')

    time_bar(y1 + 15, 0.0, 0.40, 'medium', 'LLM reasoning...')
    svg.line(tl_x0 + tl_w * 0.40, y1 + 10, tl_x0 + tl_w * 0.40, y1 + 130, color='border', dash=True)
    svg.text(tl_x0 + tl_w * 0.40, y1 + 10, "⚡ user.interrupt: \"Stop!\"", size=FS_TINY, bold=True)
    time_bar(y1 + 15, 0.40, 0.45, 'dark', '×', h_bar=28)

    time_bar(y1 + 55, 0.0, 0.35, 'light', 'Tool executing...')
    time_bar(y1 + 55, 0.40, 0.45, 'dark', '×', h_bar=28)

    time_bar(y1 + 95, 0.47, 1.0, 'medium', 'New LLM reasoning (including interrupt event + clear queue)')

    # ── Lane 2: Queued ──
    y2 = 240
    svg.rect(lane_x, y2, lane_w, 140, fill='white', stroke='border', dash=True)
    svg.text(lane_x / 2, y2 + 70, "Queue-based", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y2 + 95, "(Normal)", size=FS_SMALL, fill='text_light')

    time_bar(y2 + 15, 0.0, 0.15, 'medium', 'LLM', h_bar=24)
    time_bar(y2 + 15, 0.18, 0.60, 'light', 'Tool execution (search_web)')
    time_bar(y2 + 15, 0.63, 0.90, 'medium', 'LLM comprehensive processing')

    svg.line(tl_x0 + tl_w * 0.35, y2 + 46, tl_x0 + tl_w * 0.35, y2 + 130, color='dark', dash=True)
    svg.text(tl_x0 + tl_w * 0.35, y2 + 58, "user: \"Only look at the last 1 month\"", size=FS_TINY, fill='text_light')

    _pill(svg, tl_x0 + tl_w * 0.30, y2 + 65, 150, 24, "Enqueue waiting", fill='light', font_size=FS_TINY)

    time_bar(y2 + 100, 0.63, 0.68, 'dark', '', h_bar=20)
    svg.text(tl_x0 + tl_w * 0.61, y2 + 110, "Batch append: tool.result + user input", size=FS_TINY, fill='text_light', anchor='end')

    # ── Lane 3: Parallel ──
    y3 = 400
    svg.rect(lane_x, y3, lane_w, 140, fill='white', stroke='border', dash=True)
    svg.text(lane_x / 2, y3 + 70, "Parallel", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y3 + 95, "(Independent)", size=FS_SMALL, fill='text_light')

    time_bar(y3 + 15, 0.0, 0.80, 'light', 'Main task: Data analysis (long execution)')

    svg.line(tl_x0 + tl_w * 0.30, y3 + 50, tl_x0 + tl_w * 0.30, y3 + 130, color='dark', dash=True)
    svg.text(tl_x0 + tl_w * 0.30, y3 + 58, "user: \"How is the weather today?\"", size=FS_TINY, fill='text_light')

    time_bar(y3 + 70, 0.32, 0.50, 'medium', 'Parallel LLM', h_bar=24)
    time_bar(y3 + 70, 0.52, 0.62, 'dark', 'Weather', h_bar=24)

    svg.text(tl_x0 + tl_w * 0.635, y3 + 82, "→ Reply to user immediately", size=FS_TINY, fill='text_light', anchor='start')
    svg.text(tl_x0 + tl_w * 0.50, y3 + 115, "Tag: [Parallel with main task]", size=FS_TINY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig4-3.svg'))


# ──────────────────────── fig4-4 ────────────────────────

def fig4_4():
    """Experiment 4.4: Event-driven Agent Architecture"""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experiment 4.4: Event-driven Agent Architecture", size=FS_TITLE, bold=True)

    # Event sources (left column)
    src_data = [
        ("on_user_message", "Web/App"),
        ("on_email_reply", "Email system"),
        ("on_github_pr_update", "GitHub"),
        ("on_timer_expire", "Timer"),
        ("on_webhook_received", "Webhook"),
        ("on_resource_alert", "System alert"),
    ]
    svg.text(85, 65, "External event source", size=FS_BODY, bold=True)
    for i, (evt, src) in enumerate(src_data):
        y = 82 + i * 58
        svg.rect(10, y, 150, 44, fill='light')
        svg.text(85, y + 16, src, size=FS_SMALL, bold=True)
        svg.mono(15, y + 36, evt, size=11)

    # FastAPI Server (center)
    svg.rect(200, 80, 200, 390, fill='white', stroke='border', dash=True)
    svg.text(300, 100, "FastAPI server", size=FS_BODY, bold=True)

    svg.rect(215, 120, 170, 50, fill='medium')
    svg.text(300, 137, "HTTP endpoint", size=FS_SMALL, bold=True)
    svg.text(300, 157, "POST /events/{type}", size=FS_TINY, fill='text_light')

    svg.rect(215, 190, 170, 50, fill='light')
    svg.text(300, 207, "Event router", size=FS_SMALL, bold=True)
    svg.text(300, 227, "LLM determines urgency", size=FS_TINY, fill='text_light')

    svg.rect(215, 260, 170, 50, fill='light')
    svg.text(300, 277, "Event queue", size=FS_SMALL, bold=True)
    svg.text(300, 297, "Priority sorting", size=FS_TINY, fill='text_light')

    svg.rect(215, 330, 170, 50, fill='light')
    svg.text(300, 347, "Agent loop", size=FS_SMALL, bold=True)
    svg.text(300, 367, "Fetch → Reason → Execute", size=FS_TINY, fill='text_light')

    svg.rect(215, 400, 170, 50, fill='medium')
    svg.text(300, 417, "Session management", size=FS_SMALL, bold=True)
    svg.text(300, 437, "Multi-threaded context", size=FS_TINY, fill='text_light')

    for i in range(4):
        svg.arrow(300, 170 + i * 70, 300, 190 + i * 70)

    for i in range(6):
        svg.arrow(160, 104 + i * 58, 213, 145)

    # MCP Tools (right)
    svg.text(610, 65, "MCP tool server", size=FS_BODY, bold=True)

    tools = [
        ("Perception tools", "search_web, read_file\nread_webpage, parse_image"),
        ("execution tool", "code_interpreter\nvirtual_terminal, write_file"),
        ("collaboration tool", "browser_use\nrequest_human_approval"),
        ("notification tool", "send_email, send_slack\nsend_im_notification"),
    ]
    for i, (name, desc) in enumerate(tools):
        y = 82 + i * 100
        svg.rect(460, y, 250, 80, fill='light')
        svg.text(585, y + 22, name, size=FS_SMALL, bold=True)
        for j, line in enumerate(desc.split('\n')):
            svg.mono(470, y + 48 + j * 18, line, size=12)

    svg.arrow(400, 355, 458, 180)
    svg.arrow(458, 260, 400, 355)

    # Persistent store
    svg.rect(740, 82, 130, 380, fill='code_bg', stroke='dark', rx=4)
    svg.text(805, 115, "persistence layer", size=FS_SMALL, bold=True)
    items = ["conversation history", "event log", "scheduled task", "tool status", "audit trail"]
    for i, item in enumerate(items):
        svg.text(805, 160 + i * 55, item, size=FS_SMALL)

    svg.save(os.path.join(OUT, 'fig4-4.svg'))


# ──────────────────────── fig4-5 ────────────────────────

def fig4_5():
    """sync-async model contradiction"""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(w / 2, 30, "synchronous training paradigm vs asynchronous deployment reality", size=FS_TITLE, bold=True)

    # Top half: training pattern
    svg.rect(20, 55, w - 40, 195, fill='white', stroke='border', dash=True)
    svg.text(60, 78, "training paradigm (strictly synchronous sequence)", size=FS_BODY, bold=True, anchor='start')
    _pill(svg, w - 200, 64, 160, 28, "API mandatory constraint", fill='dark', font_size=FS_SMALL)

    steps_train = [
        ("Observation", 'medium', "User: Check Beijing weather"),
        ("Thinking", 'light', "Need to call weather tool"),
        ("Action", 'medium', "get_weather(Beijing)"),
        ("Observation", 'light', "22°C, sunny"),
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
             "tool_call → next must be tool_result, otherwise API error", size=FS_TINY)

    # Separator
    svg.line(20, 262, w - 20, 262, color='dark', dash=True)
    svg.text(w / 2, 280, "contradiction", size=FS_BODY, bold=True, fill='darker')

    # Bottom half: async reality
    svg.rect(20, 295, w - 40, 210, fill='white', stroke='border', dash=True)
    svg.text(60, 318, "deployment reality (asynchronous events interleaved)", size=FS_BODY, bold=True, anchor='start')
    _pill(svg, w - 200, 304, 160, 28, "Format conflict!", fill='dark', font_size=FS_SMALL)

    # Async timeline
    items = [
        ("Assistant", 'medium', "tool_call:\nget_weather(Beijing)", 0.0, 0.20),
        ("Waiting...", 'code_bg', "Tool execution ~5s", 0.22, 0.50),
        ("User interrupts", 'dark', "\"No need, \ncheck Shanghai's \"", 0.40, 0.55),
        ("???", 'code_bg', "When will tool_result arrive? \nHow to ensure format?", 0.57, 0.78),
        ("placeholder", 'light', "[Tool still executing, \nprioritize interruption]", 0.80, 1.0),
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
             "Solution: placeholder fixes format + non-urgent events enqueued + only interrupt when truly urgent",
             size=FS_TINY)

    # Bottom insight
    svg.rect(140, 465, w - 280, 40, fill='dark')
    svg.text(w / 2, 485,
             "Fundamental solution: next-generation models need to be trained via RL in asynchronous environments",
             size=FS_SMALL, fill='white', bold=True)

    svg.save(os.path.join(OUT, 'fig4-5.svg'))


# ──────────────────────── fig4-6 ────────────────────────

def fig4_6():
    """Experiment 4.5: Asynchronous Agent with Interruption Capability"""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Experiment 4.5: Asynchronous Agent Interruption and Recovery", size=FS_TITLE, bold=True)

    # Timeline
    tl_y, tl_h = 60, 440
    tl_x0, tl_w = 120, 740

    # Lanes
    lanes = [
        ("Agent", 80),
        ("Tool A", 180),
        ("Tool B", 260),
        ("Tool C", 340),
        ("Trajectory", 420),
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

    # Phase 1: Agent starts 3 tools
    tbar(80, 0.0, 0.12, 'medium', 'LLM: Launch 3 tools')

    # Tools running
    tbar(180, 0.13, 0.45, 'light', 'Script A: 3% per second → 33s to complete')
    tbar(260, 0.13, 0.70, 'light', 'Script B: 2% per second → 50s...')
    tbar(340, 0.13, 0.90, 'code_bg', 'Script C: 1% per second → 100s...')

    # Event: tool A completes
    t_done = 0.45
    svg.line(tl_x0 + tl_w * t_done, 70, tl_x0 + tl_w * t_done, 450, color='border', dash=True)
    svg.text(tl_x0 + tl_w * t_done, 62, "A completed", size=FS_TINY, bold=True)

    # Agent checks others
    tbar(80, 0.46, 0.58, 'medium', 'Query B, C progress')
    tbar(420, 0.46, 0.58, 'light', 'B≈66% C≈33%')

    # Cancel C (< 50%)
    t_cancel = 0.60
    svg.line(tl_x0 + tl_w * t_cancel, 70, tl_x0 + tl_w * t_cancel, 450, color='dark', dash=True)
    svg.text(tl_x0 + tl_w * t_cancel, 62, "Cancel C", size=FS_TINY, bold=True, fill='darker')

    tbar(340, 0.60, 0.65, 'dark', '×')

    # B finishes
    t_b_done = 0.70
    svg.line(tl_x0 + tl_w * t_b_done, 70, tl_x0 + tl_w * t_b_done, 450, color='border', dash=True)
    svg.text(tl_x0 + tl_w * t_b_done, 62, "B completed", size=FS_TINY, bold=True)

    # Agent generates report
    tbar(80, 0.72, 0.95, 'medium', 'LLM: Integrate A+B results to generate report')
    tbar(420, 0.72, 0.95, 'light', 'A result + B result + C cancellation record')

    # Annotations
    svg.rect(tl_x0, 460, tl_w, 40, fill='code_bg', stroke='dark', rx=4)
    svg.mono(tl_x0 + 10, 480,
             "Key: placeholder injection + async completion event + cancel_tool(task_id) API",
             size=FS_TINY)

    svg.save(os.path.join(OUT, 'fig4-6.svg'))


# ──────────────────────── fig4-7 ────────────────────────

def fig4_7():
    """Tool discovery hierarchy (server→tool matching)"""
    w, h = 880, 540
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Hierarchical tool matching", size=FS_TITLE, bold=True)

    # Query at top
    svg.rect(250, 55, 380, 44, fill='medium')
    svg.text(440, 77, "Agent: \"I need to query GitHub repository contributor statistics\"", size=FS_SMALL, bold=True)

    svg.arrow(440, 99, 440, 130)

    # discover_tools
    svg.rect(300, 132, 280, 44, fill='dark')
    svg.text(440, 154, "discover_tools(natural language requirement)", size=FS_SMALL, fill='white', bold=True)

    svg.arrow(440, 176, 440, 210)

    # Layer 1: Server matching
    svg.rect(20, 210, w - 40, 110, fill='white', stroke='border', dash=True)
    svg.text(55, 233, "Layer 1: Server matching (semantic similarity)", size=FS_BODY, bold=True, anchor='start')

    servers = [
        ("GitHub", 0.92, 'dark'),
        ("Weather", 0.15, 'light'),
        ("Finance", 0.23, 'light'),
        ("ArXiv", 0.18, 'light'),
        ("File System", 0.31, 'light'),
    ]
    sx = 50
    for name, score, fill in servers:
        svg.rect(sx, 255, 145, 50, fill=fill)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(sx + 72, 272, name, size=FS_SMALL, bold=True, fill=tc)
        svg.text(sx + 72, 292, f"Similarity: {score:.2f}", size=FS_TINY, fill='white' if fill == 'dark' else 'text_light')
        sx += 165

    # Arrow to layer 2
    svg.arrow(123, 305, 123, 345)
    svg.text(175, 330, "Top-1 server", size=FS_SMALL, fill='text_light')

    # Layer 2: Tool matching within server
    svg.rect(20, 345, w - 40, 160, fill='white', stroke='border', dash=True)
    svg.text(55, 368, "Layer 2: Tool matching (26 tools within GitHub server)", size=FS_BODY, bold=True, anchor='start')

    tools = [
        ("search_repositories", 0.41, "Search repositories"),
        ("list_contributors", 0.89, "Contributor list"),
        ("get_repo_stats", 0.85, "Repository statistics"),
        ("create_issue", 0.12, "Create Issue"),
        ("get_commit_history", 0.67, "Commit history"),
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

    # Bottom: result
    svg.rect(180, 468, 520, 30, fill='code_bg', stroke='dark', rx=4)
    svg.mono(190, 483, "Return Top-3: list_contributors, get_repo_stats, get_commit_history", size=12)

    svg.save(os.path.join(OUT, 'fig4-7.svg'))


# ──────────────────────── fig4-8 ────────────────────────

def fig4_8():
    """KV Cache Optimization (System Prompt Stability)"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "KV Cache Optimization for Dynamic Tool Loading", size=FS_TITLE, bold=True)

    # Left: naive approach
    left_x = 30
    svg.text(220, 65, "Naive Approach (Cache Invalidation)", size=FS_BODY, bold=True)

    blocks_naive = [
        ("System Prompt", 120, 'medium', "You are an AI assistant...\n+ All tool schemas", "~50K tokens"),
        ("User Message", 100, 'light', "Query NVDA stock price", ""),
        ("Assistant", 80, 'light', "tool_call: ...", ""),
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
    svg.text(left_x + 190, ny + 25, "Every time a new tool is loaded → entire cache invalidated!", size=FS_SMALL, fill='white', bold=True)

    # Right: optimized approach
    right_x = 460
    svg.text(660, 65, "Optimized Approach (Cache Stability)", size=FS_BODY, bold=True)

    blocks_opt = [
        ("System Prompt (Fixed)", 75, 'medium',
         "You are an AI assistant...\nRole + Rules + Base Tools",
         "~2K tokens | KV Cache"),
        ("Agent Status Bar (Lightweight)", 45, 'code_bg',
         "Available tools: web_search, get_weather...",
         "~200 tokens"),
        ("User: discover_tools", 40, 'light',
         '"I need to check stock price"',
         ""),
        ("Tool Result", 55, 'light',
         "Return get_stock_quote schema",
         "Tool definitions here"),
        ("User Message", 40, 'light',
         "Query NVDA stock price",
         ""),
        ("Agent Status Bar (Updated)", 45, 'code_bg',
         "+get_stock_quote added",
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
    svg.text(right_x + 200, oy + 25, "System Prompt unchanged → KV Cache fully reused", size=FS_SMALL, bold=True)

    # Bottom comparison
    svg.line(30, 475, w - 30, 475, color='dark', dash=True)
    comps = [
        ("Cache Hit Rate", "~0% (invalidated on every tool change)", "~95% (only hint changes slightly)"),
        ("First Token Latency", "High (recompute 50K tokens each time)", "Low (incremental compute ~200 tokens)"),
    ]
    cy = 495
    svg.text(250, cy, "Comparison Dimension", size=FS_SMALL, bold=True)
    svg.text(500, cy, "Naive Approach", size=FS_SMALL, bold=True)
    svg.text(740, cy, "Optimized Approach", size=FS_SMALL, bold=True)
    for metric, naive, opt in comps:
        cy += 28
        svg.text(250, cy, metric, size=FS_TINY)
        svg.text(500, cy, naive, size=FS_TINY, fill='text_light')
        svg.text(740, cy, opt, size=FS_TINY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig4-8.svg'))


# ──────────────────────── fig4-9 ────────────────────────

def fig4_9():
    """动态发现后的上下文结构：工具 schema 散落在轨迹各处"""
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "动态发现后的上下文结构：工具 schema 散落在轨迹各处", size=FS_TITLE, bold=True)

    col_x, col_w = 40, 520

    # 静态前缀组
    svg.rect(20, 50, col_w + 40, 118, fill='white', stroke='border', dash=True)
    svg.text(36, 72, "静态前缀（字节级不变，KV Cache 持续命中）", size=FS_SMALL, bold=True, anchor='start')
    svg.rect(col_x, 84, col_w, 34, fill='medium')
    svg.text(col_x + col_w / 2, 101, "System Prompt", size=FS_SMALL, bold=True)
    svg.rect(col_x, 124, col_w, 34, fill='medium')
    svg.text(col_x + col_w / 2, 141, "核心工具定义：web_search, code_interpreter, tool_search", size=FS_TINY, bold=True)

    # 轨迹组
    svg.rect(20, 180, col_w + 40, 386, fill='white', stroke='border', dash=True)
    svg.text(36, 202, "轨迹（只增不改，新内容追加在末尾）", size=FS_SMALL, bold=True, anchor='start')

    blocks = [
        ("User：查询 NVDA 股价", 'light', False),
        ("Assistant：tool_search_call(股价)", 'light', False),
        ("tool_search_output → 注入 get_stock_quote 完整 schema", '#d8e8d8', True),
        ("Assistant：调用 get_stock_quote → Tool Result", 'light', False),
        ("User：分析 GitHub 仓库的贡献者", 'light', False),
        ("Assistant：tool_search_call(GitHub)", 'light', False),
        ("tool_search_output → 注入 list_contributors 等 schema", '#d8e8d8', True),
        ("Assistant：调用 → Tool Result → 回复", 'light', False),
        ("…… 本轮最新内容", 'light', False),
    ]
    by = 214
    star_ys = []
    for label, fill, star in blocks:
        bh = 40 if star else 30
        svg.rect(col_x, by, col_w, bh, fill=fill)
        svg.text(col_x + col_w / 2, by + bh / 2, label, size=FS_TINY, bold=star)
        if star:
            star_ys.append(by + bh / 2)
        by += bh + 6

    # 右侧注释
    for sy in star_ys:
        svg.arrow(col_x + col_w + 2, sy, 592, sy, dash=True)
    svg.text(600, star_ys[0] - 12, "首次出现：prefill 一次（缓存写入）", size=FS_TINY, anchor='start', bold=True)
    svg.text(600, star_ys[0] + 10, "此后作为普通历史命中缓存", size=FS_TINY, anchor='start', fill='text_light')
    svg.text(600, star_ys[1] - 12, "不得移除/重排已加载工具", size=FS_TINY, anchor='start', bold=True)
    svg.text(600, star_ys[1] + 10, "否则缓存从变动点起失效", size=FS_TINY, anchor='start', fill='text_light')

    svg.save(os.path.join(OUT, 'fig4-9.svg'))


# ──────────────────────── main ────────────────────────

def main():
    os.makedirs(OUT, exist_ok=True)
    figs = [
        fig4_1, fig4_2, fig4_3, fig4_4, fig4_5,
        fig4_6, fig4_7, fig4_8, fig4_9,
    ]
    for fn in figs:
        fn()
        print(f"  ✓ {fn.__name__}: {fn.__doc__}")
    print(f"\nGenerated {len(figs)} figures in {OUT}/")


if __name__ == '__main__':
    main()
