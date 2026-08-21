"""对照组：「生成一盆绿植」——程序化渲染 vs 文生图模型，Vision LLM 评审。

- 路线 A（代码）：matplotlib 程序化绘制一盆绿植（确定性、可复现）。
- 路线 B（生成模型）：Gemini 原生文生图。
- 评审：Kimi 视觉模型分别打分（自然度 1-10）并给出结论。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, Polygon

import llm
from flange_spec import PLANT_PROMPT
from receipts import ReceiptBook


def draw_procedural_plant(out_path: Path, seed: int = 42) -> Path:
    """程序化绘制一盆绿植：花盆 + 茎 + 叶（椭圆）。确定性输出。"""
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(5, 6), dpi=128)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")
    ax.set_facecolor("#f5f2ec")

    # 花盆（梯形）
    pot = Polygon([(3.2, 0.8), (6.8, 0.8), (6.2, 3.4), (3.8, 3.4)],
                  closed=True, facecolor="#b5654a", edgecolor="#8a4a36", lw=2)
    rim = Polygon([(3.0, 3.4), (7.0, 3.4), (6.9, 3.9), (3.1, 3.9)],
                  closed=True, facecolor="#c97558", edgecolor="#8a4a36", lw=2)
    ax.add_patch(pot)
    ax.add_patch(rim)

    # 茎与叶
    n_branches = 7
    for i in range(n_branches):
        angle = np.pi / 2 + (i - (n_branches - 1) / 2) * 0.28
        length = 3.2 + rng.uniform(-0.4, 0.9)
        x0, y0 = 5.0, 3.8
        x1 = x0 + np.cos(angle) * length * 0.6
        y1 = y0 + np.sin(angle) * length * 0.6
        x2 = x0 + np.cos(angle) * length
        y2 = y0 + np.sin(angle) * length
        xs = np.linspace(x0, x2, 50)
        ys = np.linspace(y0, y2, 50) + 0.3 * np.sin(np.linspace(0, np.pi, 50))
        xs = xs + 0.3 * np.sin(np.linspace(0, np.pi, 50)) * np.sign(angle - np.pi / 2)
        ax.plot(xs, ys, color="#3d6b35", lw=2.5, solid_capstyle="round")
        # 每条茎顶端一片大叶，中间两片小叶
        leaf_specs = [(x2, y2 + 0.35, 1.5, 0.75, np.degrees(angle) - 90),
                      (x1 - 0.5, y1, 1.0, 0.5, np.degrees(angle) - 130),
                      (x1 + 0.5, y1 + 0.2, 1.0, 0.5, np.degrees(angle) - 50)]
        for (lx, ly, w, h, deg) in leaf_specs:
            green = rng.uniform(0.25, 0.45)
            ax.add_patch(Ellipse((lx, ly), w, h, angle=deg,
                                 facecolor=(0.1, green, 0.15), edgecolor="#274d22",
                                 lw=1.0, alpha=0.95))

    fig.savefig(out_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


JUDGE_PROMPT = """你是图像质量评审。下面是同一任务「{task}」的两个结果：
- 第一张：程序化代码（matplotlib）渲染
- 第二张：文生图模型生成

请只输出 JSON（不要 markdown 代码块），格式：
{{
  "procedural": {{"naturalness": 1-10, "comment": "一句话"}},
  "generative": {{"naturalness": 1-10, "comment": "一句话"}},
  "verdict": "哪边更自然、为什么（两三句话）"
}}
naturalness 指「看起来像真实世界的一盆绿植」的程度。"""


def judge_plants(procedural_png: Path, generative_png: Path, book: ReceiptBook) -> dict:
    """Kimi 视觉模型对两张图打自然度分，返回解析后的评审记录。"""
    content, _usage = llm.kimi_chat(
        [{
            "role": "user",
            "content": [
                {"type": "text", "text": JUDGE_PROMPT.format(task=PLANT_PROMPT)},
                llm.image_message_part(str(procedural_png)),
                llm.image_message_part(str(generative_png)),
            ],
        }],
        book, name="control-plant-vision-judge",
        model=llm.VISION_MODEL, max_tokens=1024,
    )
    m = re.search(r"\{.*\}", content, re.S)
    parsed = json.loads(m.group(0)) if m else {"parse_error": True}
    return {"judge_model": llm.VISION_MODEL, "raw_response": content, "parsed": parsed}
