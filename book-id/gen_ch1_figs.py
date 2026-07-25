"""Generate all Chapter 1 figures."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import *

OUT = os.path.join(os.path.dirname(__file__), 'images')


def fig1_4():
    """Kimi K3 / GPT-5.6 native agent architecture — caption Figure 1-4"""
    s = SVG(820, 520)

    # Title
    s.text(410, 30, '"Model as Agent" architecture: native tool calling', size=FS_TITLE, bold=True)

    # Central model box
    s.rect(260, 70, 300, 100, fill='medium')
    s.text(410, 100, 'LLM（Kimi K3 / GPT-5.6）', size=FS_BODY, bold=True)
    s.text(410, 130, 'Native agent capabilities after RL training', size=FS_SMALL, fill='text_light')

    # Built-in tools on the right
    s.group_box(620, 70, 180, 210, 'Native tools')
    s.box(635, 105, 150, 50, '$web_search', fill='light', font_size=FS_SMALL)
    s.box(635, 170, 150, 50, 'code_interpreter', fill='light', font_size=FS_SMALL)
    s.box(635, 235, 150, 50, 'More tools...', fill='white', font_size=FS_SMALL)

    s.arrow(560, 120, 633, 130)
    s.arrow(633, 195, 560, 145)

    # ReAct loop below
    s.group_box(100, 210, 460, 280, 'ReAct loop (autonomous execution within the model)')

    # Step 1: User input
    s.box(120, 250, 200, 55, 'User: Search for Bitcoin trend in the last month\n', fill='light', font_size=FS_SMALL)

    # Step 2: Think
    s.box(120, 325, 200, 55, 'Thought: Need to search real-time\ndata, then analyze with code', fill='#e8e8e8', font_size=FS_SMALL)
    s.arrow(220, 307, 220, 323)

    # Step 3: Tool call
    s.box(340, 250, 200, 55, 'Call $web_search\n"BTC price last month"', fill='light', font_size=FS_SMALL)
    s.arrow(322, 277, 338, 277)

    # Step 4: Tool result
    s.box(340, 325, 200, 55, 'Result: [price data]\n$67,230 → $71,450', fill='#e8e8e8', font_size=FS_SMALL)
    s.arrow(440, 307, 440, 323)

    # Step 5: Code
    s.box(120, 400, 200, 55, 'Call code_interpreter\nRSI, MACD calculation code', fill='light', font_size=FS_SMALL)
    s.arrow(340, 377, 220, 398, color='dark')

    # Step 6: Final
    s.box(340, 400, 200, 55, 'Final output: Technical analysis\nreport + visualization chart', fill='medium', font_size=FS_SMALL)
    s.arrow(322, 427, 338, 427)

    # RL training signal — go through the gap between ReAct/tools on the right, avoid blocking internal content
    s.arrow_curved(565, 480, 410, 172, curve=40, dash=True, color='dark')
    s.text(605, 330, 'RL training signal', size=FS_TINY, fill='text_light', bold=True, anchor='start')

    # Left side: what's different from traditional
    s.group_box(15, 70, 230, 120, 'Differences from traditional frameworks')
    s.text(130, 110, '✗ No external orchestration code needed', size=FS_SMALL, anchor='middle')
    s.text(130, 135, '✗ No need to manually write ReAct loop', size=FS_SMALL, anchor='middle')
    s.text(130, 160, '✓ Model autonomously decides the entire process', size=FS_SMALL, anchor='middle')

    s.save(f'{OUT}/fig1-4.svg')  # "Model as Agent" architecture → Figure 1-4


def fig1_1():
    """Three learning paradigms — caption Figure 1-1."""
    s = SVG(820, 480)

    s.text(410, 30, 'Three learning paradigms for agents', size=FS_TITLE, bold=True)

    col_w = 240
    gap = 20
    x_start = (820 - 3 * col_w - 2 * gap) / 2

    for i, (title, time_label, items, example) in enumerate([
        ('Post-training', 'Training time', [
            'Modify model weights',
            'Permanent · general',
            'High cost · slow to update',
        ], 'e.g. learn when to call a tool'),
        ('In-context learning', 'Inference time', [
            'Soft update via attention',
            'Temporary · adapts instantly',
            'Bounded by context window',
        ], 'e.g. learn a format from 3 examples'),
        ('Externalized learning', 'Runtime', [
            'Knowledge base + generated tools',
            'Persistent · updatable',
            'Reliable · verifiable',
        ], 'e.g. freeze a workflow into a tool'),
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
    s.text(60, 455, 'Slow (Weeks)', size=FS_SMALL, fill='text_light', anchor='start')
    s.text(410, 455, 'Learning Speed', size=FS_SMALL, fill='text_light')
    s.text(760, 455, 'Fast (Milliseconds)', size=FS_SMALL, fill='text_light', anchor='end')

    s.save(f'{OUT}/fig1-1.svg')  # Three Learning Paradigms → Figure 1-1


def fig1_2():
    """Context ablation experiment design — caption Figure 1-2."""
    W = 1000
    s = SVG(W, 470)

    s.text(W / 2, 30, 'Context Ablation Experiment Design', size=FS_TITLE, bold=True)

    # Two-line column headers so each fits its column without overlap.
    components = [
        ('System', 'prompt'),
        ('Tool', 'definitions'),
        ('Tool exec', 'results'),
        ('Thought', 'process'),
        ('History', 'messages'),
    ]
    comp_w = 108
    comp_gap = 10
    label_x = 168          # row labels right-anchored here
    comp_x = 182           # check grid starts here

    for i, (l1, l2) in enumerate(components):
        x = comp_x + i * (comp_w + comp_gap)
        s.text(x + comp_w / 2, 56, l1, size=FS_SMALL, bold=True)
        s.text(x + comp_w / 2, 76, l2, size=FS_SMALL, bold=True)

    # Result column header
    result_x = comp_x + len(components) * (comp_w + comp_gap) + 12
    s.text(result_x + 90, 66, 'Result', size=FS_SMALL, bold=True)

    # Experiment rows (labels shortened to sit within the left margin)
    conditions = [
        ('Full baseline', [True, True, True, True, True], '✓ Works normally'),
        ('No tool defs', [True, False, True, True, True], '✗ Cannot call tools'),
        ('No tool results', [True, True, False, True, True], '✗ Blind loop'),
        ('No reasoning', [True, True, True, False, True], '△ Inconsistent decisions'),
        ('No history', [True, True, True, True, False], '△ Repeated operations'),
    ]

    for j, (label, flags, result) in enumerate(conditions):
        y = 100 + j * 68

        # Row label
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

        # Result (in its own column to the right of the check grid)
        s.text(result_x + 90, y + 28, result, size=FS_SMALL, anchor='middle',
               fill='text' if '✓' in result else ('text_light' if '△' in result else 'dark'))

    s.save(f'{OUT}/fig1-2.svg')  # Context ablation experiment → Figure 1-2


def fig1_3():
    """Agent trajectory — caption Figure 1-3."""
    s = SVG(820, 680)

    s.text(410, 30, 'Agent trajectory: ReAct loop for multi-currency aggregation task', size=FS_TITLE, bold=True)

    lx = 40  # left margin
    rw = 480  # box width
    code_w = 460

    y = 60

    # Round 1
    s.badge(lx, y, 80, 26, 'Round 1', fill='darker')
    y += 36

    # User message
    s.rect(lx, y, rw, 50, fill='light')
    s.text(lx + 10, y + 16, 'user', size=FS_SMALL, bold=True, anchor='start')
    s.text(lx + 10, y + 38, '"Calculate total annual revenue: Q1 $2.5M, Q2 €2.1M, Q3 £1.8M"', size=FS_TINY, anchor='start')
    y += 60

    # Assistant reasoning
    s.rect(lx, y, rw, 45, fill='#e8e8e8')
    s.text(lx + 10, y + 14, 'assistant.reasoning', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.text(lx + 10, y + 34, '"Need to convert EUR and GBP to USD, then aggregate"', size=FS_TINY, anchor='start')
    y += 55

    # Tool calls
    s.rect(lx, y, rw, 70, fill='code_bg', stroke='dark', rx=4)
    s.text(lx + 10, y + 14, 'assistant.tool_calls', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.mono(lx + 10, y + 36, 'convert_currency(2100000, "EUR", "USD")', size=FS_TINY)
    s.mono(lx + 10, y + 54, 'convert_currency(1800000, "GBP", "USD")', size=FS_TINY)
    y += 80

    # Tool results
    s.rect(lx, y, rw, 55, fill='light')
    s.text(lx + 10, y + 14, 'tool (result)', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.mono(lx + 10, y + 36, 'EUR→USD: 2,282,608.70', size=FS_TINY)
    s.mono(lx + 250, y + 36, 'GBP→USD: 2,278,481.01', size=FS_TINY)
    y += 65

    # Round 2
    s.badge(lx, y, 80, 26, 'Round 2', fill='darker')
    y += 36

    # Assistant reasoning 2
    s.rect(lx, y, rw, 45, fill='#e8e8e8')
    s.text(lx + 10, y + 14, 'assistant.reasoning', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.text(lx + 10, y + 34, '"Exchange rates obtained, call code interpreter to aggregate"', size=FS_TINY, anchor='start')
    y += 55

    # Code interpreter call
    s.rect(lx, y, rw, 50, fill='code_bg', stroke='dark', rx=4)
    s.text(lx + 10, y + 14, 'assistant.tool_calls', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.mono(lx + 10, y + 36, 'code_interpreter("total = 2.5M + 2.28M + 2.28M")', size=FS_TINY)
    y += 60

    # Round 3
    s.badge(lx, y, 80, 26, 'Round 3', fill='darker')
    y += 36

    # Final answer
    s.rect(lx, y, rw, 45, fill='medium')
    s.text(lx + 10, y + 14, 'assistant.content (final answer)', size=FS_SMALL, bold=True, anchor='start')
    s.text(lx + 10, y + 36, '"Total annual revenue $7,061,089.71, quarterly average $2,353,696.57"', size=FS_TINY, anchor='start')
    y += 55

    # Right side: brace + annotation
    bx = 540
    s.brace_right(bx, 60, y - 10, '')
    s.text(600, 250, 'Trajectory', size=FS_BODY, bold=True, anchor='start')
    s.text(600, 280, '=', size=FS_BODY, anchor='start')
    s.text(600, 310, 'Complete input seen', size=FS_BODY, anchor='start')
    s.text(600, 340, 'by LLM at each', size=FS_BODY, anchor='start')
    s.text(600, 370, 'call', size=FS_BODY, anchor='start')

    # Key insight box on right
    s.group_box(570, 410, 230, 140, 'Key features')
    s.text(685, 445, 'Context accumulation', size=FS_SMALL, bold=True)
    s.text(685, 470, 'Full history seen each round', size=FS_TINY, fill='text_light')
    s.text(685, 500, 'Structured trajectory', size=FS_SMALL, bold=True)
    s.text(685, 525, 'user / assistant / tool', size=FS_TINY, fill='text_light')

    s.save(f'{OUT}/fig1-3.svg')  # Agent trajectory → Figure 1-3


def fig1_wf_chaining():
    """Prompt chaining — workflow pattern (ch1 Orchestration Patterns section)."""
    s = SVG(820, 300)

    s.text(410, 28, 'Prompt chaining pattern: multi-step content creation', size=FS_TITLE, bold=True)

    # Nodes with concrete descriptions
    nodes = [
        ('Requirements document', 'light', FS_SMALL),
        ('LLM: Generate outline', '#e8e8e8', FS_SMALL),
        ('LLM: Write body', '#e8e8e8', FS_SMALL),
        ('LLM: Translation', '#e8e8e8', FS_SMALL),
        ('Multilingual Documentation', 'medium', FS_SMALL),
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

    # Gate symbols between steps
    gate_y = y + node_h + 15
    for i in [1, 2]:
        gx = x_start + i * (node_w + gap) + node_w / 2
        s.diamond(gx, gate_y + 22, 60, 40, fill='white', label='Gating', font_size=FS_TINY)
        s.line(gx, y + node_h, gx, gate_y + 2, dash=True, color='dark')

    # Example content snippets below
    snippet_y = gate_y + 60
    snippets = [
        (x_start + 15, '"Product Release Notes"'),
        (x_start + node_w + gap + 15, '→ 5-Section Outline'),
        (x_start + 2 * (node_w + gap) + 15, '→ 3000-Word Document'),
        (x_start + 3 * (node_w + gap) + 15, '→ EN / JP / KR'),
    ]
    for sx, txt in snippets:
        s.text(sx, snippet_y, txt, size=FS_TINY, fill='text_light', anchor='start')

    s.save(f'{OUT}/fig1-10.svg')  # Prompt chaining workflow (unused in chapter) → Figure 1-10


def fig1_wf_routing():
    """Routing — workflow pattern (ch1 Orchestration Patterns section)."""
    s = SVG(820, 440)

    s.text(410, 28, 'Routing Pattern: Customer Service Classification', size=FS_TITLE, bold=True)

    # Input
    s.box(30, 130, 150, 55, 'User Query', fill='medium', font_size=FS_BODY)

    # Router
    s.diamond(300, 157, 140, 80, fill='#e8e8e8', label='Classifier', font_size=FS_SMALL)
    s.arrow(182, 157, 230, 157)

    # Branches
    branches = [
        (55, 'Refund Request', 'Refund Policy Prompt\n+ Order API', 'light'),
        (155, 'Technical Support', 'Diagnostic Prompt\n+ Log Tools', 'light'),
        (255, 'FAQ', 'FAQ Prompt\n+ Knowledge Base', 'light'),
        (355, 'Other', 'Haiku (Low Cost)\n+ General Prompt', 'white'),
    ]

    bx = 490
    bw = 160
    for i, (by_offset, label, desc, fill) in enumerate(branches):
        by = by_offset
        s.box(bx, by, bw, 50, label, fill=fill, bold=True, font_size=FS_SMALL)
        s.box(bx + bw + 10, by, 140, 50, desc, fill='code_bg', font_size=FS_TINY)
        s.arrow(370, 157, bx - 2, by + 25)

    # Annotation
    s.text(410, 425, 'Key: Classification can be done by LLM or traditional classifier; simple/common queries are routed to smaller models', size=FS_SMALL, fill='text_light')

    s.save(f'{OUT}/fig1-6.svg')


def fig1_wf_parallel():
    """Parallelization — workflow pattern (ch1 Orchestration Patterns section)."""
    s = SVG(820, 360)

    s.text(410, 28, 'Parallelization Pattern: Multi-Perspective Code Review', size=FS_TITLE, bold=True)

    # Input
    s.box(30, 130, 150, 55, 'Code Commit\nPull Request', fill='medium', font_size=FS_SMALL)

    # Split
    s.text(220, 157, 'Segmentation', size=FS_SMALL, bold=True)

    # Parallel workers
    workers = [
        (70, 'Security Review LLM₁', 'SQL Injection\nXSS\nPermission Leakage'),
        (155, 'Style Review LLM₂', 'Naming Conventions\nCode Duplication\nComplexity'),
        (240, 'Logic Review LLM₃', 'Boundary Conditions\nNull Pointers\nConcurrency Issues'),
    ]

    wx = 290
    ww = 155
    for i, (wy, title, items) in enumerate(workers):
        s.box(wx, wy, ww, 55, title, fill='light', bold=True, font_size=FS_SMALL)
        s.box(wx + ww + 5, wy, 130, 55, items, fill='code_bg', font_size=FS_TINY)
        s.arrow(180, 157, wx - 2, wy + 28)

    # Aggregate
    s.box(640, 130, 150, 55, 'Aggregate Results\nComprehensive Review Report', fill='medium', font_size=FS_SMALL)
    for i, (wy, _, _) in enumerate(workers):
        s.arrow(wx + ww + 135 + 2, wy + 28, 638, 157)

    s.save(f'{OUT}/fig1-7.svg')


def fig1_wf_orchestrator():
    """Orchestrator-workers — workflow pattern (ch1 Orchestration Pattern section)."""
    s = SVG(820, 440)

    s.text(410, 28, 'Orchestrator-worker pattern: multi-file code modification', size=FS_TITLE, bold=True)

    # Orchestrator at top: title + internal sub-description arranged vertically
    s.rect(260, 60, 300, 95, fill='medium')
    s.text(410, 82, 'Orchestrator LLM', size=FS_BODY, bold=True)
    s.rect(270, 105, 280, 38, fill='#e8e8e8', rx=4)
    s.text(410, 124, '"Analyze Issue → Locate Files → Assign Subtasks"', size=FS_TINY)

    # Workers
    workers = [
        (40, 'Worker 1', 'Modify auth.py\nAdd OAuth2 support', 'Read/Edit\nFile tool'),
        (290, 'Worker 2', 'Modify api.py\nAdd new endpoint', 'Read/Edit\nFile tool'),
        (540, 'Worker 3', 'Write test_auth.py\nTest cases', 'Execute tests\nTool'),
    ]

    wy = 220
    ww = 230
    wh = 55
    for wx, title, task, tools in workers:
        s.box(wx, wy, ww, wh, f'{title}：{task}', fill='light', font_size=FS_SMALL)
        s.box(wx + 20, wy + wh + 10, ww - 40, 40, tools, fill='code_bg', font_size=FS_TINY)
        s.arrow(410, 157, wx + ww / 2, wy - 2)

    # Synthesize
    s.box(260, 370, 300, 55, 'Orchestrator: merge results → verify consistency', fill='medium', font_size=FS_SMALL)
    for wx, _, _, _ in workers:
        s.arrow(wx + ww / 2, wy + wh + 52, 410, 368)

    s.save(f'{OUT}/fig1-8.svg')


def fig1_wf_evaluator():
    """Evaluator-optimizer — workflow pattern (ch1 Orchestration Pattern section)."""
    s = SVG(820, 380)

    s.text(410, 28, 'Evaluator-optimizer pattern: literary translation iteration', size=FS_TITLE, bold=True)

    # Generator
    s.box(50, 100, 200, 65, 'Generator LLM\nGenerate initial translation', fill='light', font_size=FS_SMALL)

    # Output
    s.rect(50, 185, 200, 45, fill='code_bg', stroke='dark', rx=4)
    s.text(150, 208, '"Spring sleep unaware of dawn" → v1 translation', size=FS_TINY)
    s.arrow(150, 167, 150, 183)

    # Evaluator
    s.box(330, 100, 200, 65, 'Evaluator LLM\nMulti-dimensional scoring', fill='#e8e8e8', font_size=FS_SMALL)
    s.arrow(252, 207, 330, 160)

    # Evaluation criteria
    s.rect(330, 185, 200, 80, fill='code_bg', stroke='dark', rx=4)
    s.text(340, 205, 'Accuracy: 4/5', size=FS_TINY, anchor='start')
    s.text(340, 225, 'Fluency: 3/5 ← needs improvement', size=FS_TINY, anchor='start')
    s.text(340, 245, 'Cultural adaptation: 4/5', size=FS_TINY, anchor='start')
    s.arrow(430, 167, 430, 183)

    # Feedback loop — label placed above arc to avoid blocking evaluator content
    s.arrow_curved(430, 267, 150, 98, curve=80, dash=True, color='dark')
    s.text(290, 90, 'Feedback + improvement suggestions', size=FS_TINY, fill='text_light', bold=True)

    # Iteration indicator
    s.box(610, 100, 170, 55, 'Iteration count: n', fill='white', font_size=FS_SMALL)
    s.text(695, 170, 'Exit conditions:', size=FS_SMALL, bold=True, anchor='start')
    s.text(695, 195, '① All dimensions ≥ 4/5', size=FS_TINY, anchor='start', fill='text_light')
    s.text(695, 218, '② Maximum rounds reached', size=FS_TINY, anchor='start', fill='text_light')

    # Final output
    s.box(220, 310, 380, 55, 'Final output: high-quality translation after 3 iterations', fill='medium', font_size=FS_SMALL)

    s.save(f'{OUT}/fig1-9.svg')


def fig1_5():
    """Autonomous Agent loop — caption Figure 1-5."""
    s = SVG(820, 500)

    s.text(410, 28, 'Autonomous Agent execution loop', size=FS_TITLE, bold=True)

    # While loop structure
    s.rect(80, 60, 500, 380, fill='white', stroke='border', rx=8, dash=True)
    s.text(330, 82, 'while not done:', size=FS_BODY, bold=True)

    # Step 1: Think — title above box, code inside box
    s.rect(120, 100, 420, 60, fill='#e8e8e8')
    s.text(130, 115, '① Think (Reasoning)', size=FS_SMALL, bold=True, anchor='start')
    s.rect(130, 125, 400, 28, fill='code_bg', rx=4)
    s.mono(140, 140, '"Analyzing search results...insufficient information, need further search"', size=FS_TINY)

    # Step 2: Act
    s.rect(120, 175, 420, 60, fill='light')
    s.text(130, 190, '② Acting', size=FS_SMALL, bold=True, anchor='start')
    s.rect(130, 200, 400, 28, fill='code_bg', rx=4)
    s.mono(140, 215, 'web_search("Agent RL training techniques 2025")', size=FS_TINY)
    s.arrow(330, 162, 330, 173)

    # Step 3: Observe
    s.rect(120, 250, 420, 60, fill='light')
    s.text(130, 265, '③ Observing', size=FS_SMALL, bold=True, anchor='start')
    s.rect(130, 275, 400, 28, fill='code_bg', rx=4)
    s.mono(140, 290, 'tool_result: "Found 3 relevant papers..."', size=FS_TINY)
    s.arrow(330, 237, 330, 248)

    # Loop back arrow
    s.arrow_curved(540, 280, 540, 120, curve=-40, label='Continue loop', color='dark')

    # Exit conditions on the right
    s.group_box(610, 60, 190, 190, 'Exit conditions')
    exits = [
        '① Task completed',
        '② Call final_answer',
        '③ No tool call returned',
        '④ Maximum rounds reached',
        '⑤ Error count exceeded',
    ]
    for i, ex in enumerate(exits):
        s.text(620, 100 + i * 32, ex, size=FS_SMALL, anchor='start')

    # Bottom: concrete iteration example
    s.rect(80, 360, 500, 70, fill='medium', rx=6)
    s.text(330, 380, 'Practical execution example: SWE-bench code fix', size=FS_SMALL, bold=True)
    s.text(330, 405, 'Search code → Locate bug → Edit file → Run tests → Fix fails → Edit again → Tests pass → Done', size=FS_TINY)
    s.text(330, 425, '(5 rounds of iteration, 12 tool calls)', size=FS_TINY, fill='text_light')

    # Done arrow
    s.arrow(330, 312, 330, 358, label='done = True')

    s.save(f'{OUT}/fig1-5.svg')  # Autonomous Agent execution loop → Figure 1-5


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    # In-chapter figures (referenced as 图 1-1 ~ 图 1-5)
    fig1_1()
    fig1_2()
    fig1_3()
    fig1_4()
    fig1_5()
    # Workflow pattern figures (currently unused in chapter1.md;
    # kept for potential future use)
    fig1_wf_chaining()
    fig1_wf_routing()
    fig1_wf_parallel()
    fig1_wf_orchestrator()
    fig1_wf_evaluator()
    print("Chapter 1: 5 in-chapter + 5 workflow figures generated.")
