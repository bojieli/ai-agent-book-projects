#!/usr/bin/env python3
"""Generate all SVG illustrations for Chapter 4 (Tools).

Figures (12 total):
  fig4-1:  MCP protocol sequence diagram (concrete message payloads)
  fig4-2:  Sub-Agent context preparation (4 strategies with examples)
  fig4-3:  Event-driven architecture (real event sources & payloads)
  fig4-4:  Async event processing (cancellation/queued/parallel timing)
  fig4-5:  Exp 4.4 — Event-driven agent architecture
  fig4-6:  Sync-async model contradiction (training vs deployment)
  fig4-7:  Exp 4.5 — Async agent with interruption
  fig4-8:  Tool discovery hierarchy (server→tool matching)
  fig4-9:  KV cache optimization (system prompt stability)
  fig4-10: Tool self-evolution pipeline (multi-stage)
  fig4-11: Exp 4.7 — Self-evolving agent pipeline
  fig4-12: Voyager learning cycle (curriculum + skill library)
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
    svg.text(w / 2, 30, "MCP protokol etkileşim sırası", size=FS_TITLE, bold=True)

    cl_x, sv_x = 200, 680
    svg.box(cl_x - 80, 50, 160, 44, "MCP İstemci", fill='medium', bold=True)
    svg.box(sv_x - 80, 50, 160, 44, "MCP Sunucu", fill='medium', bold=True)
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
    svg.text((cl_x + sv_x) / 2, y - 14, "initialize yanıtı", size=FS_BODY, bold=True)
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
    svg.text((cl_x + sv_x) / 2, y - 14, "tools/list yanıtı", size=FS_BODY, bold=True)
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
    svg.text((cl_x + sv_x) / 2, y - 14, "tools/call sonucu", size=FS_BODY, bold=True)
    svg.code_block(cl_x + 30, y + 6, 350, [
        '{"content": [{"type": "text",',
        '  "text": "Beijing: 22°C, açık"}]}',
    ], font_size=FS_TINY, line_h=18)

    # Phase labels on the left
    svg.text(50, 165, "① El sıkışma", size=FS_SMALL, bold=True, fill='text_light')
    svg.text(50, 310, "② Keşif", size=FS_SMALL, bold=True, fill='text_light')
    svg.text(50, 465, "③ Çağırma", size=FS_SMALL, bold=True, fill='text_light')

    svg.save(os.path.join(OUT, 'fig4-1.svg'))


# ──────────────────────── fig4-2 ────────────────────────

def fig4_2():
    """Sub-Agent context preparation (comparison of 4 strategies)"""
    w, h = 880, 530
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Alt Ajan bağlam aktarım stratejileri", size=FS_TITLE, bold=True)

    strategies = [
        ("Minimal aktarım", "dark",
         '"12345 numaralı siparişin durumunu sorgula"',
         "Sıfır bağlam → gizlilik ve güvenlik"),
        ("Elle filtreleme ve aktarım", "medium",
         '"Kullanıcı bölgesi: TR\\nÖzet: İade sorgusu"',
         "Açık seçim → kontrol edilebilir"),
        ("Otomatik kırpma ve aktarım", "light",
         '"Kullanıcı bilgisi + son 3 tur\\n+ ilgili araç sonuçları"',
         "Kural odaklı → dengeli"),
        ("LLM tarafından üretilen bağlam", "code_bg",
         '"LLM izlenceyi analiz eder\\n→ yapılandırılmış bağlam nesnesi"',
         "En akıllı → 1 ekstra çağrı"),
    ]

    col_w = 190
    gap = 18
    start_x = (w - 4 * col_w - 3 * gap) / 2

    # Main Agent at top
    svg.box(w / 2 - 100, 55, 200, 44, "Ana Ajan", fill='medium', bold=True)
    svg.text(w / 2, 118, "Alt Ajan için bağlam nasıl hazırlanır?", size=FS_SMALL, fill='text_light')

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

        svg.box(x + 15, top_y + 175, col_w - 30, 36, "Alt Ajan", fill='light', font_size=FS_SMALL)

    # Bottom: decision guide
    svg.line(30, 395, w - 30, 395, color='dark', dash=True)
    svg.text(w / 2, 418, "Seçim rehberi", size=FS_BODY, bold=True)

    guides = [
        ("Basit yüksek frekanslı çağrılar", "Hava kontrolü, hesap makinesi", "→ Minimal"),
        ("Orta karmaşıklık", "Veri sorgusu, dosya işleme", "→ Otomatik kırpma"),
        ("Karmaşık görevler", "Rapor üretimi, müşteri hizmetleri", "→ LLM üretimi"),
    ]
    gx = 80
    for label, example, rec in guides:
        svg.rect(gx, 438, 230, 70, fill='light')
        svg.text(gx + 115, 458, label, size=FS_SMALL, bold=True)
        svg.text(gx + 115, 478, example, size=FS_TINY, fill='text_light')
        svg.text(gx + 115, 498, rec, size=FS_SMALL, bold=True, fill='darker')
        gx += 260

    svg.save(os.path.join(OUT, 'fig4-2.svg'))


# ──────────────────────── fig4-3 ────────────────────────

def fig4_3():
    """Event-driven architecture (specific event source and payload)"""
    w, h = 880, 540
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Olay güdümlü asenkron Ajan mimarisi", size=FS_TITLE, bold=True)

    # Left: Event sources
    sources = [
        ("E-posta", 'on_email_reply', '{"from":"alice@...",\n "subject":"Re:toplantı"}'),
        ("Zamanlayıcı", 'on_timer_expire', '{"task_id":"daily_report",\n "scheduled":"09:00"}'),
        ("Webhook", 'on_webhook', '{"repo":"agent-lib",\n "event":"pr_merged"}'),
        ("Kullanıcı", 'on_user_message', '{"text":"Yarının havasına\nbak"}'),
    ]

    src_x, src_w = 20, 155
    svg.text(src_x + src_w / 2, 65, "Olay kaynağı", size=FS_BODY, bold=True)
    for i, (name, event_type, payload) in enumerate(sources):
        y = 85 + i * 110
        svg.box(src_x, y, src_w, 40, name, fill='medium', bold=True, font_size=FS_SMALL)
        svg.mono(src_x + 5, y + 56, event_type, size=FS_TINY)
        for j, pl in enumerate(payload.split('\n')):
            svg.mono(src_x + 5, y + 74 + j * 16, pl, size=11)

    # Middle: Event queue
    q_x, q_w = 215, 190
    svg.text(q_x + q_w / 2, 65, "Olay kuyruğu", size=FS_BODY, bold=True)
    svg.rect(q_x, 85, q_w, 390, fill='white', stroke='border', dash=True)

    queue_events = [
        ("user.input", "Öncelik: normal", 'light'),
        ("email.reply", "Öncelik: normal", 'light'),
        ("user.interrupt", "Öncelik: acil!", 'dark'),
        ("timer.trigger", "Öncelik: normal", 'light'),
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
    svg.text(ag_x + 200, 65, "Ajan işleme akışı", size=FS_BODY, bold=True)

    svg.arrow(q_x + q_w + 2, 280, ag_x - 2, 280, label="Olayı al")

    steps = [
        ("Yönlendirici", "LLM aciliyeti belirler", 'medium'),
        ("İzlenceye ekle", "Yapılandırılmış olay biçimi", 'light'),
        ("LLM çıkarımı", "Gözlemle → Düşün → Eyleme geç", 'light'),
        ("Araç yürütme", "Async/sync dağıtım", 'light'),
        ("Sonuç işleme", "Bildir/yanıtla/kaydet", 'medium'),
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
    svg.arrow_curved(ag_x + step_w, 450, ag_x + step_w, 130, curve=45, label="Döngü", dash=True, color='dark')

    svg.save(os.path.join(OUT, 'fig4-3.svg'))


# ──────────────────────── fig4-4 ────────────────────────

def fig4_4():
    """Async event handling: timing comparison of three strategies"""
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Olay işleme için üç strateji", size=FS_TITLE, bold=True)

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
    svg.text(lane_x / 2, y1 + 70, "İptal", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y1 + 95, "(Acil)", size=FS_SMALL, fill='text_light')

    time_bar(y1 + 15, 0.0, 0.40, 'medium', 'LLM muhakeme yapıyor...')
    svg.line(tl_x0 + tl_w * 0.40, y1 + 10, tl_x0 + tl_w * 0.40, y1 + 130, color='border', dash=True)
    svg.text(tl_x0 + tl_w * 0.40, y1 + 10, "⚡ user.interrupt: \"Dur!\"", size=FS_TINY, bold=True)
    time_bar(y1 + 15, 0.40, 0.45, 'dark', '×', h_bar=28)

    time_bar(y1 + 55, 0.0, 0.35, 'light', 'Araç yürütülüyor...')
    time_bar(y1 + 55, 0.40, 0.45, 'dark', '×', h_bar=28)

    time_bar(y1 + 95, 0.47, 1.0, 'medium', 'Yeni LLM muhakemesi (kesinti olayı + temizlenmiş kuyruk dahil)')

    # ── Lane 2: Queued ──
    y2 = 240
    svg.rect(lane_x, y2, lane_w, 140, fill='white', stroke='border', dash=True)
    svg.text(lane_x / 2, y2 + 70, "Kuyruk tabanlı", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y2 + 95, "(Normal)", size=FS_SMALL, fill='text_light')

    time_bar(y2 + 15, 0.0, 0.15, 'medium', 'LLM', h_bar=24)
    time_bar(y2 + 15, 0.18, 0.60, 'light', 'Araç yürütme (search_web)')
    time_bar(y2 + 15, 0.63, 0.90, 'medium', 'LLM kapsamlı işleme')

    svg.line(tl_x0 + tl_w * 0.35, y2 + 46, tl_x0 + tl_w * 0.35, y2 + 130, color='dark', dash=True)
    svg.text(tl_x0 + tl_w * 0.35, y2 + 58, "user: \"Sadece son 1 aya bak\"", size=FS_TINY, fill='text_light')

    _pill(svg, tl_x0 + tl_w * 0.30, y2 + 65, 150, 24, "Kuyruğa alındı, bekliyor", fill='light', font_size=FS_TINY)

    time_bar(y2 + 100, 0.63, 0.68, 'dark', '', h_bar=20)
    svg.text(tl_x0 + tl_w * 0.61, y2 + 110, "Toplu ekleme: tool.result + kullanıcı girdisi", size=FS_TINY, fill='text_light', anchor='end')

    # ── Lane 3: Parallel ──
    y3 = 400
    svg.rect(lane_x, y3, lane_w, 140, fill='white', stroke='border', dash=True)
    svg.text(lane_x / 2, y3 + 70, "Paralel", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y3 + 95, "(Bağımsız)", size=FS_SMALL, fill='text_light')

    time_bar(y3 + 15, 0.0, 0.80, 'light', 'Ana görev: Veri analizi (uzun süren yürütme)')

    svg.line(tl_x0 + tl_w * 0.30, y3 + 50, tl_x0 + tl_w * 0.30, y3 + 130, color='dark', dash=True)
    svg.text(tl_x0 + tl_w * 0.30, y3 + 58, "user: \"Bugün hava nasıl?\"", size=FS_TINY, fill='text_light')

    time_bar(y3 + 70, 0.32, 0.50, 'medium', 'Paralel LLM', h_bar=24)
    time_bar(y3 + 70, 0.52, 0.62, 'dark', 'Hava', h_bar=24)

    svg.text(tl_x0 + tl_w * 0.635, y3 + 82, "→ Kullanıcıya hemen yanıt ver", size=FS_TINY, fill='text_light', anchor='start')
    svg.text(tl_x0 + tl_w * 0.50, y3 + 115, "Etiket: [Ana görevle paralel]", size=FS_TINY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig4-4.svg'))


# ──────────────────────── fig4-5 ────────────────────────

def fig4_5():
    """Experiment 4.4: Event-driven Agent Architecture"""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Deney 4.4: Olay Güdümlü Ajan Mimarisi", size=FS_TITLE, bold=True)

    # Event sources (left column)
    src_data = [
        ("on_user_message", "Web/Uygulama"),
        ("on_email_reply", "E-posta sistemi"),
        ("on_github_pr_update", "GitHub"),
        ("on_timer_expire", "Zamanlayıcı"),
        ("on_webhook_received", "Webhook"),
        ("on_resource_alert", "Sistem uyarısı"),
    ]
    svg.text(85, 65, "Harici olay kaynağı", size=FS_BODY, bold=True)
    for i, (evt, src) in enumerate(src_data):
        y = 82 + i * 58
        svg.rect(10, y, 150, 44, fill='light')
        svg.text(85, y + 16, src, size=FS_SMALL, bold=True)
        svg.mono(15, y + 36, evt, size=11)

    # FastAPI Server (center)
    svg.rect(200, 80, 200, 390, fill='white', stroke='border', dash=True)
    svg.text(300, 100, "FastAPI sunucusu", size=FS_BODY, bold=True)

    svg.rect(215, 120, 170, 50, fill='medium')
    svg.text(300, 137, "HTTP uç noktası", size=FS_SMALL, bold=True)
    svg.text(300, 157, "POST /events/{type}", size=FS_TINY, fill='text_light')

    svg.rect(215, 190, 170, 50, fill='light')
    svg.text(300, 207, "Olay yönlendirici", size=FS_SMALL, bold=True)
    svg.text(300, 227, "LLM aciliyeti belirler", size=FS_TINY, fill='text_light')

    svg.rect(215, 260, 170, 50, fill='light')
    svg.text(300, 277, "Olay kuyruğu", size=FS_SMALL, bold=True)
    svg.text(300, 297, "Öncelik sıralaması", size=FS_TINY, fill='text_light')

    svg.rect(215, 330, 170, 50, fill='light')
    svg.text(300, 347, "Ajan döngüsü", size=FS_SMALL, bold=True)
    svg.text(300, 367, "Al → Muhakeme et → Yürüt", size=FS_TINY, fill='text_light')

    svg.rect(215, 400, 170, 50, fill='medium')
    svg.text(300, 417, "Oturum yönetimi", size=FS_SMALL, bold=True)
    svg.text(300, 437, "Çok iş parçacıklı bağlam", size=FS_TINY, fill='text_light')

    for i in range(4):
        svg.arrow(300, 170 + i * 70, 300, 190 + i * 70)

    for i in range(6):
        svg.arrow(160, 104 + i * 58, 213, 145)

    # MCP Tools (right)
    svg.text(610, 65, "MCP araç sunucusu", size=FS_BODY, bold=True)

    tools = [
        ("Algı araçları", "search_web, read_file\nread_webpage, parse_image"),
        ("yürütme aracı", "code_interpreter\nvirtual_terminal, write_file"),
        ("işbirliği aracı", "browser_use\nrequest_human_approval"),
        ("bildirim aracı", "send_email, send_slack\nsend_im_notification"),
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
    svg.text(805, 115, "kalıcılık katmanı", size=FS_SMALL, bold=True)
    items = ["konuşma geçmişi", "olay günlüğü", "zamanlanmış görev", "araç durumu", "denetim izi"]
    for i, item in enumerate(items):
        svg.text(805, 160 + i * 55, item, size=FS_SMALL)

    svg.save(os.path.join(OUT, 'fig4-5.svg'))


# ──────────────────────── fig4-6 ────────────────────────

def fig4_6():
    """sync-async model contradiction"""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(w / 2, 30, "eşzamanlı eğitim paradigması ile asenkron dağıtım gerçekliği", size=FS_TITLE, bold=True)

    # Top half: training pattern
    svg.rect(20, 55, w - 40, 195, fill='white', stroke='border', dash=True)
    svg.text(60, 78, "eğitim paradigması (katı biçimde eşzamanlı sıra)", size=FS_BODY, bold=True, anchor='start')
    _pill(svg, w - 200, 64, 160, 28, "API zorunlu kısıtı", fill='dark', font_size=FS_SMALL)

    steps_train = [
        ("Gözlem", 'medium', "Kullanıcı: Pekin havasını kontrol et"),
        ("Düşünme", 'light', "Hava aracını çağırmak gerekiyor"),
        ("Eylem", 'medium', "get_weather(Pekin)"),
        ("Gözlem", 'light', "22°C, açık"),
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
             "tool_call → sonrasında mutlaka tool_result gelmeli, yoksa API hatası", size=FS_TINY)

    # Separator
    svg.line(20, 262, w - 20, 262, color='dark', dash=True)
    svg.text(w / 2, 280, "çelişki", size=FS_BODY, bold=True, fill='darker')

    # Bottom half: async reality
    svg.rect(20, 295, w - 40, 210, fill='white', stroke='border', dash=True)
    svg.text(60, 318, "dağıtım gerçekliği (asenkron olaylar iç içe)", size=FS_BODY, bold=True, anchor='start')
    _pill(svg, w - 200, 304, 160, 28, "Biçim çakışması!", fill='dark', font_size=FS_SMALL)

    # Async timeline
    items = [
        ("Assistant", 'medium', "tool_call:\nget_weather(Pekin)", 0.0, 0.20),
        ("Bekliyor...", 'code_bg', "Araç yürütme ~5sn", 0.22, 0.50),
        ("Kullanıcı keser", 'dark', "\"Gerek yok, \nŞangay'ı kontrol et\"", 0.40, 0.55),
        ("???", 'code_bg', "tool_result ne zaman gelecek? \nBiçim nasıl korunacak?", 0.57, 0.78),
        ("yer tutucu", 'light', "[Araç hâlâ çalışıyor, \nkesintiye öncelik ver]", 0.80, 1.0),
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
             "Çözüm: yer tutucuyla biçimi koru + acil olmayan olayları kuyruğa al + yalnızca gerçekten acilken kes",
             size=FS_TINY)

    # Bottom insight
    svg.rect(140, 465, w - 280, 40, fill='dark')
    svg.text(w / 2, 485,
             "Temel çözüm: yeni nesil modellerin asenkron ortamlarda RL ile eğitilmesi gerekir",
             size=FS_SMALL, fill='white', bold=True)

    svg.save(os.path.join(OUT, 'fig4-6.svg'))


# ──────────────────────── fig4-7 ────────────────────────

def fig4_7():
    """Experiment 4.5: Asynchronous Agent with Interruption Capability"""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Deney 4.5: Asenkron Ajanda Kesinti ve Kurtarma", size=FS_TITLE, bold=True)

    # Timeline
    tl_y, tl_h = 60, 440
    tl_x0, tl_w = 120, 740

    # Lanes
    lanes = [
        ("Ajan", 80),
        ("Araç A", 180),
        ("Araç B", 260),
        ("Araç C", 340),
        ("İzlence", 420),
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
    tbar(80, 0.0, 0.12, 'medium', 'LLM: 3 aracı başlat')

    # Tools running
    tbar(180, 0.13, 0.45, 'light', 'Betik A: saniyede %3 → 33sn\'de tamamlanır')
    tbar(260, 0.13, 0.70, 'light', 'Betik B: saniyede %2 → 50sn...')
    tbar(340, 0.13, 0.90, 'code_bg', 'Betik C: saniyede %1 → 100sn...')

    # Event: tool A completes
    t_done = 0.45
    svg.line(tl_x0 + tl_w * t_done, 70, tl_x0 + tl_w * t_done, 450, color='border', dash=True)
    svg.text(tl_x0 + tl_w * t_done, 62, "A tamamlandı", size=FS_TINY, bold=True)

    # Agent checks others
    tbar(80, 0.46, 0.58, 'medium', 'B, C ilerlemesini sorgula')
    tbar(420, 0.46, 0.58, 'light', 'B≈%66 C≈%33')

    # Cancel C (< 50%)
    t_cancel = 0.60
    svg.line(tl_x0 + tl_w * t_cancel, 70, tl_x0 + tl_w * t_cancel, 450, color='dark', dash=True)
    svg.text(tl_x0 + tl_w * t_cancel, 62, "C'yi iptal et", size=FS_TINY, bold=True, fill='darker')

    tbar(340, 0.60, 0.65, 'dark', '×')

    # B finishes
    t_b_done = 0.70
    svg.line(tl_x0 + tl_w * t_b_done, 70, tl_x0 + tl_w * t_b_done, 450, color='border', dash=True)
    svg.text(tl_x0 + tl_w * t_b_done, 62, "B tamamlandı", size=FS_TINY, bold=True)

    # Agent generates report
    tbar(80, 0.72, 0.95, 'medium', 'LLM: A+B sonuçlarını birleştirip rapor üret')
    tbar(420, 0.72, 0.95, 'light', 'A sonucu + B sonucu + C iptal kaydı')

    # Annotations
    svg.rect(tl_x0, 460, tl_w, 40, fill='code_bg', stroke='dark', rx=4)
    svg.mono(tl_x0 + 10, 480,
             "Anahtar: yer tutucu enjeksiyonu + async tamamlanma olayı + cancel_tool(task_id) API",
             size=FS_TINY)

    svg.save(os.path.join(OUT, 'fig4-7.svg'))


# ──────────────────────── fig4-8 ────────────────────────

def fig4_8():
    """Tool discovery hierarchy (server→tool matching)"""
    w, h = 880, 540
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Hiyerarşik araç eşleştirme", size=FS_TITLE, bold=True)

    # Query at top
    svg.rect(250, 55, 380, 44, fill='medium')
    svg.text(440, 77, "Ajan: \"GitHub deposu katkıcı istatistiklerini sorgulamam gerekiyor\"", size=FS_SMALL, bold=True)

    svg.arrow(440, 99, 440, 130)

    # discover_tools
    svg.rect(300, 132, 280, 44, fill='dark')
    svg.text(440, 154, "discover_tools(doğal dil gereksinimi)", size=FS_SMALL, fill='white', bold=True)

    svg.arrow(440, 176, 440, 210)

    # Layer 1: Server matching
    svg.rect(20, 210, w - 40, 110, fill='white', stroke='border', dash=True)
    svg.text(55, 233, "Katman 1: Sunucu eşleştirme (anlamsal benzerlik)", size=FS_BODY, bold=True, anchor='start')

    servers = [
        ("GitHub", 0.92, 'dark'),
        ("Weather", 0.15, 'light'),
        ("Finance", 0.23, 'light'),
        ("ArXiv", 0.18, 'light'),
        ("Dosya Sistemi", 0.31, 'light'),
    ]
    sx = 50
    for name, score, fill in servers:
        svg.rect(sx, 255, 145, 50, fill=fill)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(sx + 72, 272, name, size=FS_SMALL, bold=True, fill=tc)
        svg.text(sx + 72, 292, f"Benzerlik: {score:.2f}", size=FS_TINY, fill='white' if fill == 'dark' else 'text_light')
        sx += 165

    # Arrow to layer 2
    svg.arrow(123, 305, 123, 345)
    svg.text(175, 330, "En iyi 1 sunucu", size=FS_SMALL, fill='text_light')

    # Layer 2: Tool matching within server
    svg.rect(20, 345, w - 40, 160, fill='white', stroke='border', dash=True)
    svg.text(55, 368, "Katman 2: Araç eşleştirme (GitHub sunucusunda 26 araç)", size=FS_BODY, bold=True, anchor='start')

    tools = [
        ("search_repositories", 0.41, "Depo ara"),
        ("list_contributors", 0.89, "Katkıcı listesi"),
        ("get_repo_stats", 0.85, "Depo istatistikleri"),
        ("create_issue", 0.12, "Issue oluştur"),
        ("get_commit_history", 0.67, "Commit geçmişi"),
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
    svg.mono(190, 483, "En iyi 3'ü döndür: list_contributors, get_repo_stats, get_commit_history", size=12)

    svg.save(os.path.join(OUT, 'fig4-8.svg'))


# ──────────────────────── fig4-9 ────────────────────────

def fig4_9():
    """KV Cache Optimization (System Prompt Stability)"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Dinamik Araç Yükleme için KV Cache Optimizasyonu", size=FS_TITLE, bold=True)

    # Left: naive approach
    left_x = 30
    svg.text(220, 65, "Naif Yaklaşım (Önbellek Geçersizleşir)", size=FS_BODY, bold=True)

    blocks_naive = [
        ("Sistem İstemi", 120, 'medium', "Sen bir AI asistanısın...\n+ Tüm araç şemaları", "~50K token"),
        ("Kullanıcı Mesajı", 100, 'light', "NVDA hisse fiyatını sorgula", ""),
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
    svg.text(left_x + 190, ny + 25, "Yeni bir araç her yüklendiğinde → tüm önbellek geçersizleşir!", size=FS_SMALL, fill='white', bold=True)

    # Right: optimized approach
    right_x = 460
    svg.text(660, 65, "Optimize Edilmiş Yaklaşım (Önbellek Kararlılığı)", size=FS_BODY, bold=True)

    blocks_opt = [
        ("Sistem İstemi (Sabit)", 75, 'medium',
         "Sen bir AI asistanısın...\nRol + Kurallar + Temel Araçlar",
         "~2K token | KV Cache"),
        ("Ajan Durum Çubuğu (Hafif)", 45, 'code_bg',
         "Mevcut araçlar: web_search, get_weather...",
         "~200 token"),
        ("User: discover_tools", 40, 'light',
         '"Hisse fiyatını kontrol etmem gerekiyor"',
         ""),
        ("Araç Sonucu", 55, 'light',
         "get_stock_quote şemasını döndür",
         "Araç tanımları burada"),
        ("Kullanıcı Mesajı", 40, 'light',
         "NVDA hisse fiyatını sorgula",
         ""),
        ("Ajan Durum Çubuğu (Güncellendi)", 45, 'code_bg',
         "+get_stock_quote eklendi",
         "~220 token"),
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
    svg.text(right_x + 200, oy + 25, "Sistem İstemi değişmedi → KV Cache tamamen yeniden kullanılır", size=FS_SMALL, bold=True)

    # Bottom comparison
    svg.line(30, 475, w - 30, 475, color='dark', dash=True)
    comps = [
        ("Önbellek İsabet Oranı", "~%0 (her araç değişiminde geçersizleşir)", "~%95 (yalnızca ipucu hafifçe değişir)"),
        ("İlk Token Gecikmesi", "Yüksek (her seferinde 50K token yeniden hesaplanır)", "Düşük (artımlı hesaplama ~200 token)"),
    ]
    cy = 495
    svg.text(250, cy, "Karşılaştırma Boyutu", size=FS_SMALL, bold=True)
    svg.text(500, cy, "Naif Yaklaşım", size=FS_SMALL, bold=True)
    svg.text(740, cy, "Optimize Edilmiş Yaklaşım", size=FS_SMALL, bold=True)
    for metric, naive, opt in comps:
        cy += 28
        svg.text(250, cy, metric, size=FS_TINY)
        svg.text(500, cy, naive, size=FS_TINY, fill='text_light')
        svg.text(740, cy, opt, size=FS_TINY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig4-9.svg'))


# ──────────────────────── fig4-10 ────────────────────────

def fig4_10():
    """Tool Self-Evolution Pipeline (Multi-Stage)"""
    w, h = 880, 500
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Ajanın Kendi Kendine Evrimi: Gereksinimden Araca", size=FS_TITLE, bold=True)

    # Pipeline stages
    stages = [
        ("① Gereksinim Tespiti", 'medium', [
            "Görev: YouTube Altyazı Çıkarımı",
            "Ajan: Mevcut araçlar yetersiz",
            "→ Kendi kendine evrimi başlat",
        ]),
        ("② Web Araması", 'light', [
            "search: youtube transcript",
            "python library",
            "→ 3 aday kütüphane bulundu",
        ]),
        ("③ GitHub Keşfi", 'light', [
            "jdepoix/youtube-",
            "transcript-api deposunu ziyaret et",
            "→ README + Örnekleri oku",
        ]),
        ("④ Öğrenme ve Test Etme", 'light', [
            "code_interpreter testi:",
            "from youtube_transcript",
            "  _api import ...",
        ]),
        ("⑤ Araç Kapsülleme", 'medium', [
            "MCP aracı oluştur:",
            "get_youtube_transcript",
            "(video_id) → metin",
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

    # Tool registry at bottom
    svg.arrow(w / 2, 205, w / 2, 240)

    svg.rect(120, 240, w - 240, 50, fill='dark')
    svg.text(w / 2, 265, "⑥ Araç kütüphanesine kaydet → gelecekte doğrudan yeniden kullan", size=FS_BODY, fill='white', bold=True)

    # Reuse scenario
    svg.arrow(w / 2, 290, w / 2, 320)
    svg.rect(60, 320, w - 120, 160, fill='white', stroke='border', dash=True)
    svg.text(w / 2, 345, "Araç yeniden kullanımı: benzer görevle bir sonraki karşılaşma", size=FS_BODY, bold=True)

    svg.rect(80, 365, 340, 50, fill='code_bg', stroke='dark', rx=4)
    svg.mono(90, 382, "Ajan: \"YouTube altyazılarını çıkarmam gerekiyor\"", size=FS_TINY)
    svg.mono(90, 400, "→ search_tools(\"youtube transcript\")", size=FS_TINY)

    svg.arrow(420, 390, 460, 390)

    svg.rect(460, 365, 330, 50, fill='light')
    svg.text(625, 382, "Bulundu! get_youtube_transcript", size=FS_SMALL, bold=True)
    svg.text(625, 402, "Arama ve oluşturmayı atla, doğrudan çağır", size=FS_TINY, fill='text_light')

    svg.rect(200, 430, 480, 35, fill='medium')
    svg.text(w / 2, 448, "Araç katmanı + Bilgi katmanı + Strateji katmanı → kullanımda daha da ustalaşır", size=FS_SMALL, bold=True)

    svg.save(os.path.join(OUT, 'fig4-10.svg'))


# ──────────────────────── fig4-11 ────────────────────────

def fig4_11():
    """Experiment 4.7: Agent searches for tools on the web, self-evolves"""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Deney 4.7: Kendi kendine evrimleşen Ajan boru hattı", size=FS_TITLE, bold=True)

    # Top: minimal base tools
    svg.rect(30, 60, w - 60, 48, fill='medium')
    svg.text(w / 2, 76, "Temel araçlar (minimal küme)", size=FS_SMALL, bold=True)
    base_tools = ["web_search", "read_webpage", "code_interpreter", "create_tool", "search_tools"]
    btx = 65
    for t in base_tools:
        tw = len(t) * 8 + 20
        _pill(svg, btx, 82, tw, 22, t, fill='dark', font_size=11, bold=True)
        btx += tw + 10

    # Task input
    svg.arrow(w / 2, 108, w / 2, 135)
    svg.rect(100, 135, w - 200, 45, fill='code_bg', stroke='dark', rx=4)
    svg.mono(110, 150,
             "Görev: \"NVDA son hisse fiyatı? Bir haftalık değişim?\" → Ajan: Finansal araç yok!",
             size=FS_TINY)
    svg.mono(110, 168,
             "→ Yetenek açığını tespit et → Kendi kendine evrimi başlat",
             size=FS_TINY)

    # Evolution pipeline
    svg.arrow(w / 2, 180, w / 2, 210)

    pipe_y = 210
    pipe_stages = [
        ("web_search", "Aday çözümleri ara", 'light',
         ["\"python stock price API\"",
          "→ yfinance, Alpha Vantage..."]),
        ("read_webpage", "Çözümleri değerlendir", 'light',
         ["yfinance: ücretsiz, API anahtarı gerektirmez",
          "Alpha Vantage: kayıt gerektirir..."]),
        ("code_interpreter", "Test et ve doğrula", 'light',
         ["import yfinance as yf",
          "yf.Ticker('NVDA').history()"]),
        ("create_tool", "Kapsülle ve kaydet", 'medium',
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

    # Tool registry
    svg.arrow(w / 2, 330, w / 2, 360)
    svg.rect(200, 360, w - 400, 44, fill='dark')
    svg.text(w / 2, 382, "Araç kütüphanesi: get_stock_data kaydedildi", size=FS_BODY, fill='white', bold=True)

    # Reuse
    svg.arrow(w / 2, 404, w / 2, 430)
    svg.rect(100, 430, w - 200, 40, fill='code_bg', stroke='dark', rx=4)
    svg.mono(110, 442,
             "Yeniden kullanım doğrulaması: \"TSLA hisse fiyatını sorgula\" → search_tools eşleşti → doğrudan get_stock_data çağrılıyor",
             size=FS_TINY)
    svg.mono(110, 458,
             "Arama/değerlendirme/test aşamalarını atla → maliyette %90+ azalma",
             size=FS_TINY)

    svg.save(os.path.join(OUT, 'fig4-11.svg'))


# ──────────────────────── fig4-12 (Voyager, was fig4_voyager) ────────

def fig4_12():
    """Voyager learning loop (curriculum + skill library + iterative prompting)"""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Voyager: Sürekli öğrenme için Ajan mimarisi", size=FS_TITLE, bold=True)

    svg.rect(20, 65, 260, 180, fill='white', stroke='border', dash=True)
    svg.text(150, 88, "Otomatik müfredat üreteci", size=FS_BODY, bold=True)
    curriculum = [
        "Girdi: mevcut durum + mevcut beceriler",
        "Çıktı: sıradaki keşif hedefi",
        "",
        "Örnek hedef dizisi:",
        "  Ağaç kes → Tahta kalas yap",
        "  → Tahta kazma yap → Taş çıkar",
        "  → Fırın yap → Demir cevheri erit",
    ]
    for i, line in enumerate(curriculum):
        svg.mono(32, 112 + i * 20, line, size=12)

    svg.rect(600, 65, 260, 180, fill='white', stroke='border', dash=True)
    svg.text(730, 88, "Yinelemeli istem mekanizması", size=FS_BODY, bold=True)
    iterative = [
        "Başarısızlıkta geri bildirim topla:",
        "  - Ortam gözlemi (hata mesajı)",
        "  - Kendi kendini doğrulama sonucu",
        "",
        "LLM İstemine entegre et",
        "→ Kod iyileştirmesini yönlendir",
        "→ Başarılı olana kadar birden çok kez yinele",
    ]
    for i, line in enumerate(iterative):
        svg.mono(612, 112 + i * 20, line, size=12)

    svg.arrow(280, 155, 370, 155, label="Hedef")
    svg.arrow(560, 155, 600, 155, label="Geri bildirim")

    svg.rect(370, 110, 190, 80, fill='medium')
    svg.text(465, 140, "Ajan yürütmesi", size=FS_BODY, bold=True)
    svg.text(465, 165, "GPT-4 kod üretimi", size=FS_SMALL, fill='text_light')

    svg.arrow(465, 190, 465, 260)
    svg.text(510, 230, "Başarı → Çıkar", size=FS_SMALL, fill='text_light')

    svg.rect(120, 260, 640, 240, fill='white', stroke='border', dash=True)
    svg.text(440, 283, "Beceri Kütüphanesi — dışsallaştırılmış öğrenmenin çekirdeği", size=FS_BODY, bold=True)

    skills = [
        ("chopTree()", "Ağaç kes\nTemel beceri", "function chopTree() {\n  bot.dig(nearest('log'));\n}"),
        ("craftPlanks()", "Tahta kalas yap\nchopTree'yi çağırır", "function craftPlanks() {\n  chopTree(); craft('planks');\n}"),
        ("craftPickaxe()", "Tahta kazma yap\nBirden çok beceriyi birleştirir", "function craftPickaxe() {\n  craftPlanks(); craft('stick');\n  craft('wooden_pickaxe');\n}"),
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

    svg.arrow_curved(120, 380, 150, 245, curve=60, label="Mevcut beceriler", dash=True, color='dark')

    svg.save(os.path.join(OUT, 'fig4-12.svg'))


# ──────────────────────── main ────────────────────────

def main():
    os.makedirs(OUT, exist_ok=True)
    figs = [
        fig4_1, fig4_2, fig4_3, fig4_4, fig4_5, fig4_6,
        fig4_7, fig4_8, fig4_9, fig4_10, fig4_11, fig4_12,
    ]
    # Note: fig4_11 = Exp 4.7 self-evolving agent, fig4_12 = Voyager
    # (ordered by chapter appearance)
    for fn in figs:
        fn()
        print(f"  ✓ {fn.__name__}: {fn.__doc__}")
    print(f"\nGenerated {len(figs)} figures in {OUT}/")


if __name__ == '__main__':
    main()
