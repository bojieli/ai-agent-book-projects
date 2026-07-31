#!/usr/bin/env python3
"""Chapter 8 figures — Agent's self-evolution.

NOTE: this generator was previously a stray copy of chapter 9's figures, which
left fig8-1..fig8-7 showing chapter-9 content. It has been rewritten so each
figure matches its caption in chapter8.md. Figures are built with svg_lib;
titles live in the body text (svg_lib strips in-figure titles).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svg_lib import SVG, FS_SMALL, FS_TINY, FS_BODY

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')


def _pipeline(stages, fname, W=880, feedback=None):
    """Horizontal stage pipeline with an optional dashed feedback loop."""
    n = len(stages)
    bw = min(190, (W - 40 - (n - 1) * 22) // n)
    bh, gap = 84, 22
    H = 234 if feedback else 174   # +24 for the 40px title-crop margin
    s = SVG(W, H)
    x0 = (W - (n * bw + (n - 1) * gap)) / 2
    y = 48                          # start below the TITLE_CROP_PX=40 line
    pos = []
    for i, (lab, sub) in enumerate(stages):
        x = x0 + i * (bw + gap)
        s.box(x, y, bw, bh, lab, sublabel=sub, bold=True, fill='light')
        pos.append(x)
        if i > 0:
            s.arrow(pos[i - 1] + bw + 2, y + bh / 2, x - 2, y + bh / 2)
    if feedback:
        lx = pos[-1] + bw / 2
        fx = pos[0] + bw / 2
        ry = y + bh + 34
        s.line(lx, y + bh, lx, ry, dash=True)
        s.line(lx, ry, fx, ry, dash=True)
        s.arrow(fx, ry, fx, y + bh + 2, dash=True)
        s.text((lx + fx) / 2, ry + 18, feedback, size=FS_SMALL, fill='text_light')
    s.save(os.path.join(OUT, fname + '.svg'))


def fig8_1():  #Externalized learning loop
    _pipeline([("Complete task", "Generate raw experience"), ("Refine experience", "Summarize, compress, structure"),
               ("Store in external system", "Knowledge base/tools, retrievable"), ("Retrieve and reuse", "Invoke in next task")],
              'fig8-1', feedback="Experience accumulates persistently, reused across sessions")


def fig8_2():  #GAIA experience learning system
    _pipeline([("Successful trajectory", "Process of completing task"), ("Strategy summary", "Refine into knowledge summary"),
               ("Knowledge summary base", "Build semantic index"), ("Retrieval injection", "Agent uses when making decisions")],
              'fig8-2', feedback="Reuse historical experience for similar tasks")


def fig8_3():  #Hierarchical tool matching (server level → tool level)
    W, H = 620, 354
    s = SVG(W, H)
    cx = W / 2
    s.box(cx - 150, 46, 300, 52, "User query", sublabel="\"Debug this file\"", bold=True, fill='light')
    s.arrow(cx, 100, cx, 120)
    s.box(cx - 220, 122, 440, 62, "Layer 1: Server-level semantic search",
          sublabel="Hundreds of MCP servers → recall Top-K relevant servers", bold=True, fill='light')
    s.arrow(cx, 186, cx, 208)
    s.box(cx - 220, 210, 440, 62, "Layer 2: Tool-level semantic search",
          sublabel="Match only within tools of Top-K servers → Top-N tools", bold=True, fill='light')
    s.arrow(cx, 274, cx, 296)
    s.box(cx - 150, 298, 300, 46, "Selected tool",
          sublabel="Significantly narrows candidate scope, reduces selection cost", bold=True, fill='light')
    s.save(os.path.join(OUT, 'fig8-3.svg'))


def fig8_4():  #KV Cache Optimization for Dynamic Tool Loading (Naive vs Optimized)
    W, H = 860, 244
    s = SVG(W, H)
    s.text(220, 46, "Naive: all tool defs in system prompt", size=FS_SMALL, bold=True, fill='darker')
    s.rect(30, 62, 380, 70, fill='#f0d8d8')
    s.text(220, 84, "System prompt + all tool definitions", size=FS_SMALL, bold=True)
    s.text(220, 108, "Any tool change → whole KV cache invalidated", size=FS_TINY, fill='text_light')
    s.rect(30, 140, 380, 46, fill='light')
    s.text(220, 163, "Recalculated every round, high cost", size=FS_SMALL)

    s.text(640, 46, "Optimized: tool defs loaded on demand", size=FS_SMALL, bold=True, fill='darker')
    s.rect(450, 62, 380, 40, fill='#d8e8d8')
    s.text(640, 82, "Stable system prompt (cache-hit prefix)", size=FS_SMALL, bold=True)
    s.rect(450, 106, 380, 40, fill='light')
    s.text(640, 126, "On-demand appended tool definitions (changing part)", size=FS_SMALL)
    s.rect(450, 150, 380, 40, fill='light')
    s.text(640, 170, "Conversation trajectory", size=FS_SMALL)
    s.text(640, 206, "Stable prefix unchanged → KV Cache continuously reused", size=FS_TINY, fill='text_light')
    s.line(430, 54, 430, 220, dash=True)
    s.save(os.path.join(OUT, 'fig8-4.svg'))


def fig8_5():  #Agent Self-Evolution Pipeline (Requirement Identification → Tool Search → Code Encapsulation → Tool Registration)
    _pipeline([("① Requirement Identification", "Existing tools insufficient"), ("② Tool Search", "Open-world search"),
               ("③ Code Encapsulation", "Generate and encapsulate"), ("④ Tool Registration", "Incorporate into library for reuse")],
              'fig8-5', feedback="Newly registered tools can be reused by subsequent tasks, continuously expanding capability boundaries")


def fig8_6():  #Voyager Continuous Learning Architecture (Curriculum Generator + Skill Library + Iterative Prompting)
    _pipeline([("Curriculum Generator", "Propose progressive new tasks"), ("Iterative Prompting Mechanism", "Generate and debug skill code"),
               ("Skill Library", "Store reusable skills")],
              'fig8-6', W=760, feedback="Skill accumulation unlocks harder tasks (open-world exploration)")


def fig8_7():  #Experiment 8-5 Self-Evolution Pipeline (Search → Evaluate → Test → Encapsulate → Reuse)
    _pipeline([("① Search", "Find tools on open network"), ("② Evaluate", "Determine suitability"), ("③ Test", "Verify usability"),
               ("④ Package", "Wrap into standard tool"), ("⑤ Reuse", "Include in tool library")],
              'fig8-7', W=940, feedback="New tools are accumulated for reuse in subsequent tasks")


if __name__ == '__main__':
    for fn in (fig8_1, fig8_2, fig8_3, fig8_4, fig8_5, fig8_6, fig8_7):
        fn()
        print('saved', fn.__name__)
