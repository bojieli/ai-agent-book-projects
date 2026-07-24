"""Generate all Chapter 2 figures.

9 figures total (fig2-1 through fig2-9):
  fig2-1:  Context window composition (reworked — with actual content snippets)
  fig2-2:  Local LLM tool calling architecture (NEW — Exp 2.1)
  fig2-3:  Chat Template token structure (reworked — larger fonts)
  fig2-4:  KV Cache prefix reuse (reworked — concrete token sequences)
  fig2-5:  System hint injection (reworked — actual hint text)
  fig2-6:  Context compression strategy comparison (reworked — data viz)
  fig2-7:  Context compression pipeline variants (NEW — Exp 2.7)
  fig2-8:  Skills progressive disclosure (reworked — concrete PPTX example)
  fig2-9:  Memory strategy comparison (NEW — Exp 2.10)

Deleted (no longer generated):
  old fig2-4: Prompt structured (text code examples already show this)
  old fig2-8: Working memory → long-term memory (text explains clearly)
"""
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    SVG, COLORS, FONT, MONO,
    FS_TITLE, FS_BODY, FS_SMALL, FS_TINY, FS_LABEL, STROKE_W, CORNER_R,
    _escape,
)

OUT = os.path.join(os.path.dirname(__file__), 'images')


# ════════════════════════════════════════════════════════════════════
#  fig2-1: Context Window Composition (reworked)
# ════════════════════════════════════════════════════════════════════

def fig2_1():
    """Context window with actual content snippets in each layer."""
    W, H = 820, 620
    s = SVG(W, H)

    s.text(410, 30, 'Overview of context window composition', size=FS_TITLE, bold=True)

    lx, lw = 40, 700
    layers = [
        ('System Prompt', 'medium', [
            '"You are a helpful assistant. You MUST answer concisely."',
            '"Use tools when the user asks for real-time information."',
        ]),
        ('Tool Definitions', 'light', [
            '{"name": "web_search", "description": "Search the web",',
            ' "parameters": {"query": {"type": "string"}}}',
        ]),
        ('Conversation History', 'light', [
            'user: "What\'s the weather in Beijing today?"',
            'assistant: [tool_call] → get_weather("Beijing")',
            'tool: {"temp": "23°C", "conditions": "clear"}',
        ]),
        ('Reasoning Trace', '#e8e8e8', [
            '<think>The user asks about the weather. I already have the tool result,',
            'so I can directly summarize and respond without calling the tool again.</think>',
        ]),
        ('Current generation position →', 'white', [
            'assistant: "Beijing is clear today, temperature 23°C..."  ← LLM is generating',
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

    # Right side brace
    brace_top = 60
    brace_bot = y - 8
    s.brace_right(lx + lw + 8, brace_top, brace_bot)
    s.text(lx + lw + 15, (brace_top + brace_bot) / 2 - 12, 'Context', size=FS_BODY, bold=True, anchor='start')
    s.text(lx + lw + 15, (brace_top + brace_bot) / 2 + 12, 'Window', size=FS_BODY, bold=True, anchor='start')

    # Bottom annotation
    s.rect(100, y + 15, 620, 50, fill='code_bg', stroke='dark', rx=4)
    s.text(410, y + 32, 'Window size: Qwen3 = 32K tokens | Claude = 200K | Gemini = 2M', size=FS_SMALL)
    s.text(410, y + 52, 'All content serialized into token stream → processed by Transformer attention mechanism', size=FS_SMALL, fill='text_light')

    s.save(f'{OUT}/fig2-1.svg')


# ════════════════════════════════════════════════════════════════════
#  fig2-2: Local LLM Tool Calling Architecture (NEW — Exp 2.1)
# ════════════════════════════════════════════════════════════════════

def fig2_2():
    """Qwen3-0.6B on local hardware + tool registry + ReAct loop."""
    W, H = 820, 540
    s = SVG(W, H)

    s.text(410, 30, 'Experiment 2.1: Local LLM Tool Calling Architecture', size=FS_TITLE, bold=True)

    # Hardware box (left)
    s.group_box(30, 65, 220, 130, 'Local Hardware')
    s.box(50, 100, 180, 35, 'Apple M2 / 16GB', fill='light', font_size=FS_SMALL)
    s.box(50, 145, 180, 35, 'MLX Inference Backend', fill='light', font_size=FS_SMALL)

    # Model box (center)
    s.rect(290, 65, 240, 130, fill='medium')
    s.text(410, 95, 'Qwen3-0.6B', size=FS_BODY, bold=True)
    s.text(410, 120, '0.6B parameters · Q4 quantization', size=FS_SMALL, fill='text_light')
    s.text(410, 145, '> 100 tokens/s', size=FS_SMALL, fill='text_light')
    s.text(410, 170, 'ReAct + Tool calling capability', size=FS_SMALL)

    # Tool registry (right)
    s.group_box(570, 65, 220, 130, 'Tool Registry')
    s.box(590, 100, 180, 35, 'get_current_time', fill='code_bg', font_size=FS_SMALL)
    s.box(590, 145, 180, 35, 'get_temperature', fill='code_bg', font_size=FS_SMALL)

    # Arrows hardware → model, model ↔ tools
    s.arrow(252, 130, 288, 130)
    s.arrow(532, 122, 568, 122)
    s.arrow(568, 138, 532, 138)

    # ReAct loop (below)
    s.group_box(50, 220, 720, 290, 'ReAct Loop')

    # Step 1: User query
    s.rect(80, 260, 300, 40, fill='light')
    s.text(90, 280, 'user: "What\'s the time and weather in Vancouver?"', size=FS_TINY, anchor='start')

    # Step 2: Think
    s.rect(80, 310, 300, 55, fill='#e8e8e8')
    s.text(90, 328, '<think>', size=FS_TINY, anchor='start', bold=True)
    s.text(90, 348, 'Need to call get_current_time', size=FS_TINY, anchor='start')
    s.text(90, 363, 'and get_temperature tools', size=FS_TINY, anchor='start')
    s.arrow(230, 302, 230, 308)

    # Step 3: Tool calls
    s.rect(80, 375, 300, 50, fill='code_bg', stroke='dark', rx=4)
    s.mono(90, 393, '<tool_call>', size=FS_TINY)
    s.mono(90, 411, '{"name":"get_current_time",...}', size=FS_TINY)
    s.arrow(230, 367, 230, 373)

    # Step 4: Tool results
    s.rect(80, 435, 300, 40, fill='light')
    s.text(90, 455, '<tool_response> {"time":"05:18","temp":"13.2°C"}', size=FS_TINY, anchor='start')
    s.arrow(230, 427, 230, 433)

    # Right side: loop arrow + final output
    # Loop arrow goes along the left outer edge to avoid blocking text inside the left column
    s.arrow_curved(80, 455, 80, 280, curve=-40, color='dark')
    s.text(30, 367, 'Continue loop', size=FS_TINY, fill='text_light', bold=True)

    # Final output box
    s.rect(430, 280, 320, 55, fill='medium')
    s.text(440, 298, 'Final output:', size=FS_SMALL, bold=True, anchor='start')
    s.text(440, 318, '"Vancouver: 05:18 AM, 13.2°C,', size=FS_TINY, anchor='start')
    s.text(440, 335, '  clear sky, humidity 93%"', size=FS_TINY, anchor='start')

    # Streaming annotation
    s.rect(430, 360, 320, 80, fill='code_bg', stroke='dark', rx=4)
    s.text(590, 378, 'Streaming key timings', size=FS_SMALL, bold=True)
    s.text(440, 400, '<think>... → hidden, not shown to user', size=FS_TINY, anchor='start')
    s.text(440, 418, 'plain text → real-time streaming display', size=FS_TINY, anchor='start')
    s.text(440, 436, '<tool_call> → parse and execute tool', size=FS_TINY, anchor='start')

    s.save(f'{OUT}/fig2-2.svg')


# ════════════════════════════════════════════════════════════════════
#  fig2-3: Chat Template Token Structure (reworked)
# ════════════════════════════════════════════════════════════════════

def fig2_3():
    """Chat template token structure with actual token content and larger fonts."""
    W, H = 920, 580
    s = SVG(W, H)

    s.text(W / 2, 30, 'Token Structure of Chat Template', size=FS_TITLE, bold=True)

    lx = 40
    rw = 800

    y = 65
    segments = [
        ('<|im_start|>system', 'darker', 'white', [
            '# Tools',
            'You may call one or more functions...',
            '<tools>{"name":"get_weather",...}</tools>',
            '<tool_call>{"name":..., "arguments":...}</tool_call>',
        ]),
        ('<|im_end|>', 'dark', 'white', []),
        ('<|im_start|>user', 'darker', 'white', [
            '"What\'s the weather like in Beijing today?"',
        ]),
        ('<|im_end|>', 'dark', 'white', []),
        ('<|im_start|>assistant', 'darker', 'white', [
            '<think>Need to query weather, call get_weather tool</think>',
            '<tool_call>{"name":"get_weather","args":{"city":"Beijing"}}</tool_call>',
        ]),
        ('<|im_end|>', 'dark', 'white', []),
        ('<|im_start|>user', 'darker', 'white', [
            '<tool_response>{"temp":"23°C","sky":"clear"}</tool_response>',
        ]),
        ('<|im_end|>', 'dark', 'white', []),
        ('<|im_start|>assistant', 'darker', 'white', [
            '← LLM starts generating new tokens from here',
        ]),
    ]

    for tag, tag_fill, _, content_lines in segments:
        if not content_lines:
            # End token — small badge
            s.badge(lx, y, 140, 24, tag, fill=tag_fill, font_size=FS_TINY)
            y += 32
        else:
            total_h = 26 + len(content_lines) * 20 + 8
            s.rect(lx, y, rw, total_h, fill='light')
            s.badge(lx + 5, y + 4, 200, 22, tag, fill=tag_fill, font_size=FS_TINY)
            for i, line in enumerate(content_lines):
                s.mono(lx + 220, y + 8 + i * 20 + 12, line, size=FS_TINY)
            y += total_h + 4

    # Right annotation
    s.text(lx + rw + 5, 80, 'special', size=FS_SMALL, anchor='start', bold=True)
    s.text(lx + rw + 5, 100, 'tokens', size=FS_SMALL, anchor='start', bold=True)

    s.save(f'{OUT}/fig2-3.svg')


# ════════════════════════════════════════════════════════════════════
#  fig2-4: KV Cache Prefix Reuse (reworked)
# ════════════════════════════════════════════════════════════════════

def fig2_4():
    """KV Cache with concrete token sequences showing prefix reuse."""
    W, H = 820, 480
    s = SVG(W, H)

    s.text(410, 30, 'KV Cache Prefix Reuse Mechanism', size=FS_TITLE, bold=True)

    lx = 40
    bw = 740

    # Request 1
    s.text(lx, 70, 'Request 1', size=FS_BODY, bold=True, anchor='start')
    # System prompt portion (cached)
    s.rect(lx, 85, 380, 40, fill='medium')
    s.text(lx + 190, 105, 'System Prompt + Tools (1200 tokens)', size=FS_SMALL)
    # User message
    s.rect(lx + 385, 85, 180, 40, fill='light')
    s.text(lx + 475, 105, 'user: "How\'s the weather?"', size=FS_SMALL)
    # KV computed
    s.rect(lx + 570, 85, 170, 40, fill='#e8e8e8')
    s.text(lx + 655, 105, '→ generate response', size=FS_SMALL)

    # Request 2 (cache hit)
    s.text(lx, 155, 'Request 2', size=FS_BODY, bold=True, anchor='start')
    # Same prefix — cached
    s.rect(lx, 170, 380, 40, fill='medium')
    s.text(lx + 190, 190, 'System Prompt + Tools (cache hit ✓)', size=FS_SMALL)
    # Different user msg
    s.rect(lx + 385, 170, 180, 40, fill='light')
    s.text(lx + 475, 190, 'user: "What time is it?"', size=FS_SMALL)
    s.rect(lx + 570, 170, 170, 40, fill='#e8e8e8')
    s.text(lx + 655, 190, '→ generate response', size=FS_SMALL)

    # Cache reuse arrow
    s.arrow(lx + 190, 127, lx + 190, 168, label='KV reuse', color='dark')

    # Request 3 (cache miss)
    s.text(lx, 245, 'Request 3', size=FS_BODY, bold=True, anchor='start')
    s.text(lx + 85, 245, '(system prompt changed)', size=FS_SMALL, anchor='start', fill='text_light')
    s.rect(lx, 260, 400, 40, fill='white', dash=True)
    s.text(lx + 200, 280, 'System + Tools + "Time: 10:30:45"', size=FS_SMALL)
    s.rect(lx + 405, 260, 160, 40, fill='light')
    s.text(lx + 485, 280, 'user: "How\'s the weather?"', size=FS_SMALL)
    s.rect(lx + 570, 260, 170, 40, fill='#e8e8e8')
    s.text(lx + 655, 280, '→ full recomputation ✗', size=FS_SMALL)

    # Performance comparison
    s.rect(80, 330, 660, 130, fill='code_bg', stroke='dark', rx=4)
    s.text(410, 355, 'Performance Comparison (3000 token context)', size=FS_BODY, bold=True)

    # Table header
    s.line(100, 370, 720, 370, color='dark')
    s.text(230, 390, 'cache hit', size=FS_SMALL, bold=True)
    s.text(490, 390, 'cache miss', size=FS_SMALL, bold=True)
    s.line(100, 405, 720, 405, color='dark')

    # Rows
    s.text(130, 425, 'TTFT', size=FS_SMALL, anchor='start')
    s.text(230, 425, '~0.5 seconds', size=FS_SMALL)
    s.text(490, 425, '3 - 5 seconds', size=FS_SMALL)

    s.text(130, 450, 'Cost', size=FS_SMALL, anchor='start')
    s.text(230, 450, 'only new tokens billed', size=FS_SMALL)
    s.text(490, 450, 'all tokens rebilled', size=FS_SMALL)

    s.save(f'{OUT}/fig2-4.svg')


# ════════════════════════════════════════════════════════════════════
#  fig2-5: Agent Status Bar Injection Architecture (reworked)
# ════════════════════════════════════════════════════════════════════

def fig2_5():
    """Show WHERE hints are inserted with actual hint text."""
    W, H = 820, 580
    s = SVG(W, H)

    s.text(410, 30, 'System prompt injection architecture', size=FS_TITLE, bold=True)

    # Left: WITHOUT hints
    col_w = 350
    col_gap = 70
    lx1 = 30
    lx2 = lx1 + col_w + col_gap

    s.text(lx1 + col_w / 2, 65, 'No system prompt', size=FS_BODY, bold=True)
    s.text(lx2 + col_w / 2, 65, 'With system prompt', size=FS_BODY, bold=True)

    # Left column: raw trajectory
    y = 90
    left_items = [
        ('system', 'System Prompt + Tools', 'medium', 35),
        ('user', '"Help me contact Xfinity to negotiate"', 'light', 35),
        ('assistant', 'phone_call(Xfinity) → 1st attempt', '#e8e8e8', 35),
        ('tool', 'Result: waited 45 minutes, not connected', 'light', 35),
        ('assistant', 'web_search("Xfinity deals")', '#e8e8e8', 35),
        ('tool', 'Result: [large amount of search content...]', 'light', 35),
        ('assistant', 'phone_call(Xfinity) → 2nd attempt', '#e8e8e8', 35),
        ('tool', 'Result: connected, quoted $65/month', 'light', 35),
        ('assistant', 'phone_call(Xfinity) → 3rd attempt', '#e8e8e8', 35),
        ('tool', 'Result: confirmed price reduction to $59/month', 'light', 35),
        ('user', '"Can you call again to follow up?"', 'light', 35),
    ]

    for role, content, fill, h in left_items:
        s.rect(lx1, y, col_w, h, fill=fill, rx=4)
        s.text(lx1 + 8, y + h / 2, f'{role}:', size=FS_TINY, anchor='start', bold=True)
        s.mono(lx1 + 65, y + h / 2, content, size=FS_TINY - 2)
        y += h + 3

    s.text(lx1 + col_w / 2, y + 15, '→ Model needs to scan entire context to "count"', size=FS_SMALL, fill='text_light')
    s.text(lx1 + col_w / 2, y + 35, 'number of calls made, prone to miscounting', size=FS_SMALL, fill='text_light')

    # Right column: with system hints
    y = 90
    right_items = [
        ('system', 'System Prompt + Tools', 'medium', 35),
        ('user', '"Help me contact Xfinity to negotiate"', 'light', 35),
        ('...', '[ Same trajectory content ]', '#e8e8e8', 90),
        ('user', '"Can you call again to follow up?"', 'light', 35),
    ]
    for role, content, fill, h in right_items:
        s.rect(lx2, y, col_w, h, fill=fill, rx=4)
        s.text(lx2 + 8, y + h / 2, f'{role}:', size=FS_TINY, anchor='start', bold=True)
        s.mono(lx2 + 65, y + h / 2, content, size=FS_TINY - 2)
        y += h + 3

    # System hint block (highlighted)
    hint_y = y
    hint_h = 130
    s.rect(lx2, hint_y, col_w, hint_h, fill='medium', stroke='border', rx=4)
    s.text(lx2 + 10, hint_y + 18, '<agent_status>', size=FS_SMALL, bold=True, anchor='start')
    hints = [
        'phone_call called 3 times (Xfinity: 3)',
        'Constraint check: limit reached (3/3) ✗',
        'TODO: [✓]Contact Xfinity [✓]Confirm price reduction',
        'Current time: 2025-09-14 10:30',
        'Current status: waiting for user confirmation',
    ]
    for i, h in enumerate(hints):
        s.mono(lx2 + 15, hint_y + 40 + i * 20, h, size=FS_TINY - 2)
    s.text(lx2 + col_w - 10, hint_y + hint_h - 12, '</agent_status>', size=FS_SMALL, bold=True, anchor='end')

    s.text(lx2 + col_w / 2, hint_y + hint_h + 18, '→ Model directly reads refined status', size=FS_SMALL, fill='text_light')
    s.text(lx2 + col_w / 2, hint_y + hint_h + 38, 'Accurately follows constraints, no more calls', size=FS_SMALL, fill='text_light')

    # VS divider
    s.text(lx1 + col_w + col_gap / 2, 300, 'VS', size=FS_BODY, bold=True)

    s.save(f'{OUT}/fig2-5.svg')


# ════════════════════════════════════════════════════════════════════
#  fig2-6: Context Compression Strategy Comparison (reworked)
# ════════════════════════════════════════════════════════════════════

def fig2_6():
    """Data visualization comparing 6 strategies with actual experiment numbers."""
    W, H = 820, 530
    s = SVG(W, H)

    s.text(410, 30, 'Context compression strategy comparison (OpenAI founder tracking experiment)', size=FS_TITLE, bold=True)

    # Table layout
    tx = 30
    tw = 760

    # Column header centers aligned to the data columns below (concise labels
    # so nothing overlaps in the narrow columns).
    header_y = 68
    headers = [
        (tx + 72, 'Strategy'),
        (tx + 195, 'Tokens'),
        (tx + 282, 'Ratio'),
        (tx + 352, 'Iters'),
        (tx + 432, 'Result'),
        (tx + 475 + 90, 'Token usage'),
    ]
    for cx, label in headers:
        s.text(cx, header_y, label, size=FS_SMALL, bold=True)

    s.line(tx, header_y + 12, tx + tw, header_y + 12)

    strategies = [
        ('No compression', '> 110K', '100%', '5 (Failed)', False, 110000),
        ('Individual summary', '123,205', '6.8%', '24', True, 123205),
        ('Combined summary', '55,462', '2.1%', '21', True, 55462),
        ('Context-aware', '25,198', '0.9%', '15', True, 25198),
        ('Aware + citation', '45,544', '1.4%', '17', True, 45544),
        ('Adaptive window', '181,372', '—', '8', True, 181372),
    ]

    max_tokens = 190000
    bar_x = tx + 475
    bar_max_w = 280

    for i, (name, tokens, ratio, iters, success, token_val) in enumerate(strategies):
        y = header_y + 30 + i * 62

        # Strategy name
        s.text(tx + 72, y + 15, name, size=FS_SMALL, anchor='middle',
               bold=(name == 'Context-aware'))

        # Token count
        s.text(tx + 195, y + 15, tokens, size=FS_SMALL)

        # Compression rate
        s.text(tx + 282, y + 15, ratio, size=FS_SMALL)

        # Iterations
        s.text(tx + 352, y + 15, iters, size=FS_SMALL)

        # Result
        result_text = '✓ Success' if success else '✗ Failure'
        result_color = 'text' if success else 'dark'
        s.text(tx + 432, y + 15, result_text, size=FS_SMALL, fill=result_color)

        # Bar
        bar_w = (token_val / max_tokens) * bar_max_w
        bar_fill = '#e8e8e8' if name != 'Context-aware' else 'medium'
        if not success:
            bar_fill = 'white'
        s.rect(bar_x, y, bar_w, 30, fill=bar_fill, stroke='border', rx=3)

    # Highlight best strategy
    best_y = header_y + 30 + 3 * 62 - 5
    s.rect(tx - 2, best_y, tw + 4, 42, fill='white', stroke='border', rx=4, dash=True)

    # Bottom insight
    s.rect(100, H - 60, 620, 45, fill='code_bg', stroke='dark', rx=4)
    s.text(410, H - 45, 'Context-aware compression: 77% token reduction, highest success rate, fewest iterations', size=FS_SMALL, bold=True)
    s.text(410, H - 25, 'Key: incorporate query intent and existing information into compression decisions', size=FS_SMALL, fill='text_light')

    s.save(f'{OUT}/fig2-6.svg')


# ════════════════════════════════════════════════════════════════════
#  fig2-7: Context Compression Pipeline Variants (NEW — Exp 2.7)
# ════════════════════════════════════════════════════════════════════

def fig2_7():
    """6 compression strategies as pipeline variants."""
    W, H = 820, 600
    s = SVG(W, H)

    s.text(410, 30, 'Experiment 2.7: Processing flow of six compression strategies', size=FS_TITLE, bold=True)

    # Input annotation
    s.text(410, 58, 'Each search returns ~70K characters → each strategy handles it differently', size=FS_SMALL, fill='text_light')

    strategies = [
        ('① No compression', 'Directly retain', 'Full original text into context', '> 110K tok → overflow', False),
        ('② Individual summary', 'Independent summary', 'Each result independently generates 2-3 paragraph summary', '123K tok · 6.8%', True),
        ('③ Combined summary', 'Merged summary', 'All results concatenated then unified summary', '55K tok · 2.1%', True),
        ('④ Context-aware', 'Intelligent compression', 'Given query + context → targeted compression', '25K tok · 0.9%', True),
        ('⑤ Aware + citation', 'Intelligent + traceability', 'Compressed content + retain URL citation markers', '45K tok · 1.4%', True),
        ('⑥ Adaptive window', 'Delay Compression', '< 80% window retains original text, batch compression beyond', '181K tok · Maximum Fidelity', True),
    ]

    lx = 30
    row_h = 78
    start_y = 75

    for i, (name, method, desc, result, success) in enumerate(strategies):
        y = start_y + i * row_h

        # Strategy name badge
        fill = 'darker' if i == 3 else 'dark'
        s.badge(lx, y, 130, 26, name, fill=fill, font_size=FS_TINY)

        # Method box
        s.rect(lx, y + 30, 120, 40, fill='#e8e8e8', rx=4)
        s.text(lx + 60, y + 50, method, size=FS_SMALL)

        # Arrow
        s.arrow(lx + 122, y + 50, lx + 135, y + 50)

        # Description
        s.rect(lx + 138, y + 30, 330, 40, fill='code_bg', stroke='dark', rx=4)
        s.text(lx + 303, y + 50, desc, size=FS_TINY)

        # Arrow
        s.arrow(lx + 470, y + 50, lx + 483, y + 50)

        # Result
        res_fill = 'medium' if i == 3 else ('white' if not success else 'light')
        s.rect(lx + 486, y + 30, 275, 40, fill=res_fill, rx=4)
        s.text(lx + 623, y + 50, result, size=FS_TINY)

    s.save(f'{OUT}/fig2-7.svg')


# ════════════════════════════════════════════════════════════════════
#  fig2-8: Skills Progressive Disclosure (reworked)
# ════════════════════════════════════════════════════════════════════

def fig2_8():
    """Agent Skills with concrete PPTX example showing 3 layers."""
    W, H = 820, 540
    s = SVG(W, H)

    s.text(410, 30, 'Skills Progressive Disclosure Mechanism (PPTX Skill Example)', size=FS_TITLE, bold=True)

    # Layer 1: Metadata (always loaded)
    y1 = 70
    s.rect(40, y1, 740, 90, fill='medium')
    s.text(60, y1 + 20, 'Layer 1: Metadata (loaded at startup, ~200 tokens)', size=FS_BODY, bold=True, anchor='start')
    s.rect(60, y1 + 40, 700, 40, fill='code_bg', rx=4)
    s.mono(70, y1 + 60, 'skills: [{name: "PPTX", desc: "Create PowerPoint presentations from content"}', size=FS_TINY)
    s.mono(70, y1 + 75, '        {name: "PDF",  desc: "Extract and analyze PDF documents"}, ...]', size=FS_TINY - 2)

    # Trigger arrow
    s.arrow(410, y1 + 92, 410, y1 + 115)
    s.text(430, y1 + 103, 'Task trigger: "Generate PPT from paper"', size=FS_SMALL, anchor='start', fill='text_light')

    # Layer 2: Core SKILL.md
    y2 = y1 + 120
    s.rect(40, y2, 740, 130, fill='light')
    s.text(60, y2 + 20, 'Layer 2: SKILL.md Core Flow (loaded on demand, ~2K tokens)', size=FS_BODY, bold=True, anchor='start')
    s.rect(60, y2 + 40, 700, 80, fill='code_bg', rx=4)
    lines2 = [
        'PPTX Skill Core Flow:',
        '1. markitdown extracts text → 2. Unzip PPTX to access XML',
        '3. Modify slide{N}.xml content → 4. Repackage as .pptx',
        'References: → html2pptx.md | → reference.md | → scripts/',
    ]
    for i, line in enumerate(lines2):
        s.mono(70, y2 + 56 + i * 19, line, size=FS_TINY)

    # Trigger arrow
    s.arrow(410, y2 + 132, 410, y2 + 155)
    s.text(430, y2 + 143, 'Need detailed method: "Create PPT using HTML template"', size=FS_SMALL, anchor='start', fill='text_light')

    # Layer 3: Sub-documents
    y3 = y2 + 160
    s.rect(40, y3, 740, 130, fill='white', dash=True)
    s.text(60, y3 + 20, 'Layer 3: Sub-documents (selective deep dive, loaded on demand)', size=FS_BODY, bold=True, anchor='start')

    doc_w = 215
    docs = [
        ('html2pptx.md', 'HTML template → PPT\n complete workflow'),
        ('reference.md', 'XML format specification\n and technical details'),
        ('scripts/*.py', 'Executable tools:\nthumbnail.py etc.'),
    ]
    for i, (name, desc) in enumerate(docs):
        dx = 60 + i * (doc_w + 20)
        s.rect(dx, y3 + 45, doc_w, 70, fill='code_bg', stroke='dark', rx=4)
        s.text(dx + doc_w / 2, y3 + 62, name, size=FS_SMALL, bold=True)
        desc_lines = desc.split('\n')
        for j, dl in enumerate(desc_lines):
            s.text(dx + doc_w / 2, y3 + 82 + j * 16, dl, size=FS_TINY, fill='text_light')

    # Bottom: KV Cache note
    s.rect(100, y3 + 140, 620, 35, fill='code_bg', stroke='dark', rx=4)
    s.text(410, y3 + 158, 'Fixed metadata → KV Cache friendly | Dynamic content appended → Cache not broken', size=FS_SMALL)

    s.save(f'{OUT}/fig2-8.svg')


# ════════════════════════════════════════════════════════════════════
#  fig2-9: Mem0 Architecture (reworked)
# ════════════════════════════════════════════════════════════════════

def fig2_9():
    """Mem0 architecture with actual data flow and concrete memory examples."""
    W, H = 820, 530
    s = SVG(W, H)

    s.text(410, 30, 'Mem0 Memory Management Architecture', size=FS_TITLE, bold=True)

    # Input conversation
    s.rect(30, 70, 250, 80, fill='light')
    s.text(40, 88, 'New conversation input:', size=FS_SMALL, bold=True, anchor='start')
    s.mono(40, 110, 'user: "I moved to Shenzhen,', size=FS_TINY)
    s.mono(40, 128, 'new address is Nanshan Science Park"', size=FS_TINY)

    # MemoryBase (center)
    s.rect(310, 65, 200, 100, fill='medium')
    s.text(410, 85, 'MemoryBase', size=FS_BODY, bold=True)
    s.text(410, 108, 'Memory Lifecycle Management', size=FS_SMALL, fill='text_light')
    s.text(410, 130, 'Analyze → Classify → Decide', size=FS_SMALL, fill='text_light')
    s.arrow(282, 110, 308, 110)

    # LLMBase (above MemoryBase)
    s.rect(330, 185, 160, 50, fill='#e8e8e8')
    s.text(410, 203, 'LLMBase', size=FS_SMALL, bold=True)
    s.text(410, 222, 'Semantic analysis + Relationship judgment', size=FS_TINY)
    s.arrow(410, 167, 410, 183, color='dark')
    s.arrow(410, 183, 410, 167, color='dark')

    # Decision output
    s.rect(310, 255, 200, 80, fill='code_bg', stroke='dark', rx=4)
    s.text(320, 273, 'Decision result:', size=FS_SMALL, bold=True, anchor='start')
    s.mono(320, 293, 'Old: "User lives in Beijing Haidian"', size=FS_TINY)
    s.mono(320, 311, '→ UPDATE: "Lives in Shenzhen Nanshan"', size=FS_TINY)
    s.mono(320, 329, '→ ADD: "Moved to Shenzhen"', size=FS_TINY - 2)
    s.arrow(410, 237, 410, 253, color='dark')

    # EmbeddingBase (right)
    s.rect(560, 70, 220, 70, fill='light')
    s.text(670, 90, 'EmbeddingBase', size=FS_SMALL, bold=True)
    s.text(670, 112, 'Text → Vector (compute-intensive)', size=FS_TINY, fill='text_light')
    s.arrow(512, 95, 558, 90)

    # VectorStoreBase (right, below)
    s.rect(560, 160, 220, 100, fill='light')
    s.text(670, 180, 'VectorStoreBase', size=FS_SMALL, bold=True)
    s.text(670, 200, 'Persistence + Retrieval (I/O intensive)', size=FS_TINY, fill='text_light')
    s.text(670, 225, 'Chroma / Qdrant / Milvus', size=FS_TINY, fill='text_light')
    s.text(670, 248, '(HNSW / LSH index)', size=FS_TINY, fill='text_light')
    s.arrow(670, 142, 670, 158)

    # Stored memories example
    s.rect(560, 290, 220, 120, fill='code_bg', stroke='dark', rx=4)
    s.text(570, 310, 'Stored memory entries:', size=FS_SMALL, bold=True, anchor='start')
    s.mono(570, 332, '"Lives in Shenzhen Nanshan Science Park"', size=FS_TINY)
    s.mono(570, 352, '"Email: john@x.com"', size=FS_TINY)
    s.mono(570, 372, '"Preference: Chinese communication"', size=FS_TINY)
    s.mono(570, 392, '"Job: ML engineer"', size=FS_TINY)
    s.arrow(670, 262, 670, 288, color='dark')

    # Plugin mechanism note
    s.rect(30, 170, 250, 60, fill='code_bg', stroke='dark', rx=4)
    s.text(155, 192, 'Plugin mechanism', size=FS_SMALL, bold=True)
    s.text(155, 212, 'Replaceable LLM / embedding model / storage backend', size=FS_TINY, fill='text_light')

    # Retrieval path
    s.rect(30, 390, 250, 80, fill='light')
    s.text(40, 408, 'Memory retrieval:', size=FS_SMALL, bold=True, anchor='start')
    s.mono(40, 430, 'query: "Where does the user live?"', size=FS_TINY)
    s.mono(40, 450, '→ Vector similarity matching', size=FS_TINY)
    s.mono(40, 468, '→ "Lives in Shenzhen Nanshan Science Park"', size=FS_TINY)
    s.arrow_curved(282, 430, 558, 350, curve=-30, label='Retrieval', color='dark')

    s.save(f'{OUT}/fig2-10.svg')


# ════════════════════════════════════════════════════════════════════
#  fig2-11: Memobase Multi-type Memory Architecture (reworked)
# ════════════════════════════════════════════════════════════════════

def fig2_11_memobase():
    """Memobase 4 memory types with concrete examples."""
    W, H = 820, 560
    s = SVG(W, H)

    s.text(410, 30, 'Memobase multi-type memory architecture', size=FS_TITLE, bold=True)

    types = [
        ('Episodic memory', 'Episodic', [
            '2025-09-10 User booked Shanghai→Tokyo',
            '2025-09-12 Flight rescheduled to 9/20',
            '2025-09-13 Hotel changed to Shinjuku branch',
        ], 'Timestamped event sequence'),
        ('Semantic memory', 'Semantic', [
            'User → is → ML engineer',
            'User → is allergic to peanuts',
            'User → prefers → window seat',
        ], 'Entity-relationship network'),
        ('Procedural memory', 'Procedural', [
            'Travel planning pattern:',
            '  Destination→Budget→Transport→Accommodation→Activities',
            '(Automatically extracted from multiple interactions)',
        ], 'Reusable strategy pattern'),
        ('Working memory', 'Working', [
            'Current task: Book a hotel in Tokyo',
            'Completed: Flight booked (ANA NH919)',
            'Pending: Choose hotel + arrange airport pickup',
        ], 'Current task status'),
    ]

    col_w = 185
    gap = 10
    total = len(types) * col_w + (len(types) - 1) * gap
    start_x = (W - total) / 2

    for i, (name, eng, examples, desc) in enumerate(types):
        x = start_x + i * (col_w + gap)

        # Header
        s.rect(x, 65, col_w, 55, fill='medium')
        s.text(x + col_w / 2, 82, name, size=FS_BODY, bold=True)
        s.text(x + col_w / 2, 105, eng, size=FS_TINY, fill='text_light')

        # Examples
        ex_h = len(examples) * 20 + 20
        s.rect(x, 130, col_w, ex_h, fill='code_bg', stroke='dark', rx=4)
        for j, ex in enumerate(examples):
            s.mono(x + 8, 148 + j * 20, ex, size=FS_TINY - 2)

        # Description
        s.text(x + col_w / 2, 130 + ex_h + 18, desc, size=FS_TINY, fill='text_light')

    # Interaction arrows between working memory and long-term types
    arrow_y = 280
    wm_x = start_x + 3 * (col_w + gap) + col_w / 2

    for i in range(3):
        lt_x = start_x + i * (col_w + gap) + col_w / 2
        s.arrow_curved(wm_x - 20, arrow_y, lt_x + 20, arrow_y, curve=-30, dash=True, color='dark')

    s.text(410, arrow_y - 10, 'Working memory ↔ Long-term memory dynamic interaction', size=FS_SMALL, fill='text_light')

    # Memory compression section (below)
    comp_y = 310
    s.rect(40, comp_y, 740, 110, fill='light')
    s.text(60, comp_y + 22, 'Memory compression and organization', size=FS_BODY, bold=True, anchor='start')

    comp_stages = [
        ('Importance scoring', ['Access frequency × Time decay', '× Emotional intensity × Uniqueness']),
        ('Clustering compression', ['Group similar memories', '→ Generate representative summary']),
        ('Abstraction and generalization', ['Episodic memory → Semantic memory', 'Specific events → General rules']),
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

    # Privacy section
    priv_y = comp_y + 125
    s.rect(40, priv_y, 740, 90, fill='#e8e8e8')
    s.text(60, priv_y + 20, 'Privacy protection: Hierarchical information storage', size=FS_BODY, bold=True, anchor='start')

    levels = [
        ('L1 Public', 'Name, email', 'Plaintext'),
        ('L2 Internal', 'Phone, address', 'Partial masking'),
        ('L3 Confidential', 'ID number, password', 'Placeholder replacement'),
    ]

    lev_w = 230
    for j, (level, info, strategy) in enumerate(levels):
        lx = 55 + j * (lev_w + 10)
        s.rect(lx, priv_y + 38, lev_w, 40, fill='code_bg', stroke='dark', rx=4)
        s.text(lx + 8, priv_y + 58, f'{level}: {info} → {strategy}', size=FS_TINY, anchor='start')

    s.save(f'{OUT}/fig2-11.svg')


# ════════════════════════════════════════════════════════════════════
#  fig2-9: Memory Strategy Comparison (NEW — Exp 2.10)
# ════════════════════════════════════════════════════════════════════

def fig2_9_memory_comparison():
    """4 memory modes showing how the same info is stored differently."""
    W, H = 820, 620
    s = SVG(W, H)

    s.text(410, 30, 'Experiment 2.10: Comparison of four memory strategies', size=FS_TITLE, bold=True)

    # Input conversation example
    s.rect(40, 60, 740, 55, fill='light')
    s.text(50, 78, 'Original dialogue:', size=FS_SMALL, bold=True, anchor='start')
    s.mono(50, 98, '"I am a senior engineer at TechCorp, leading a team of 5 to build a recommendation system, using ML for three years"', size=FS_TINY)

    strategies = [
        ('Simple Notes', 'Atomic facts', [
            '"User company: TechCorp"',
            '"User Position: Senior Engineer"',
            '"User Team: 5 people"',
            '"User Expertise: Recommendation System"',
        ], 'Pros: O(1) operation, extremely low overhead\nCons: Complete loss of relevance'),
        ('Enhanced Notes', 'Full Paragraph', [
            '"Senior engineer at',
            'TechCorp, leads a team',
            'of 5 building a rec.',
            'system, 3 yrs in ML."',
        ], 'Pros: Semantic completeness\nCons: Redundancy + complex updates'),
        ('JSON Cards', 'Hierarchical Structure', [
            'work:',
            '  company: "TechCorp"',
            '  title: "Senior Engineer"',
            '  team_size: 5',
        ], 'Pros: Partial updates\nCons: Rigid classification'),
        ('Adv. JSON Cards', 'Contextualized Knowledge', [
            '{category: "work",',
            ' title: "Senior Engineer",',
            ' backstory: "Self-introduction",',
            ' ts: "09-14"}',
        ], 'Pros: Disambiguation + traceability\nCons: High generation cost'),
    ]

    col_w = 185
    gap = 10
    total = len(strategies) * col_w + (len(strategies) - 1) * gap
    start_x = (W - total) / 2

    for i, (name, approach, storage, tradeoff) in enumerate(strategies):
        x = start_x + i * (col_w + gap)

        # Header
        s.rect(x, 130, col_w, 50, fill='medium')
        s.text(x + col_w / 2, 148, name, size=FS_SMALL, bold=True)
        s.text(x + col_w / 2, 168, approach, size=FS_TINY, fill='text_light')

        # Arrow from input
        s.arrow(x + col_w / 2, 117, x + col_w / 2, 128, color='dark')

        # Storage representation
        storage_h = len(storage) * 18 + 16
        s.rect(x, 190, col_w, storage_h, fill='code_bg', stroke='dark', rx=4)
        for j, line in enumerate(storage):
            s.mono(x + 8, 205 + j * 18, line, size=FS_TINY - 2)

        # Tradeoff (Pros/Cons) — wrapped so long lines don't collide with neighbours
        s.text_block(x + col_w / 2, 200 + storage_h + 6, col_w - 6,
                     tradeoff.split('\n'), size=FS_TINY, min_size=9, line_gap=1.25)

    # Evaluation framework (bottom)
    eval_y = 420
    s.rect(40, eval_y, 740, 180, fill='light')
    s.text(60, eval_y + 22, 'Three-Level Evaluation Framework', size=FS_BODY, bold=True, anchor='start')

    eval_levels = [
        ('Level 1: Basic Recall', 'Store and retrieve direct information', '"My membership number is 12345" → Exact return', 'light'),
        ('Level 2: Multi-session Retrieval', 'Cross-session associative reasoning', '"Schedule maintenance for my car" → Identify two cars', '#e8e8e8'),
        ('Level 3: Proactive Service', 'Integrate multiple memories, anticipatory assistance', 'Book international flight → Discover passport is about to expire', 'medium'),
    ]

    for i, (level, desc, example, fill) in enumerate(eval_levels):
        ey = eval_y + 45 + i * 45
        s.rect(60, ey, 180, 38, fill=fill, rx=4)
        s.text(150, ey + 19, level, size=FS_SMALL, bold=True)
        s.text(252, ey + 12, desc, size=FS_TINY, anchor='start')
        s.mono(252, ey + 29, example, size=FS_TINY - 2, anchor='start')

    s.save(f'{OUT}/fig2-9.svg')


# ════════════════════════════════════════════════════════════════════
#  Main
# ════════════════════════════════════════════════════════════════════

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
    print("Chapter 2: 9 figures generated.")
