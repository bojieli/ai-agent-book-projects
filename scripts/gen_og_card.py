#!/usr/bin/env python3
"""Generate assets/og-card.png — the Open Graph / Twitter share card.

The card is a static 1200x630 PNG checked into the repo (regenerating it
is only needed when the branding text changes). scripts/seo_meta.py
references it as <site_url>/assets/og-card.png on every page.

Fonts are macOS system fonts (Hiragino Sans GB); run this on a Mac.
PingFang would be preferred but is an on-demand download on modern macOS
and often absent from /System/Library/Fonts.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630

HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"  # index 0 = W3, 2 = W6

# fenix palette (keep in sync with extras/book-theme.css)
INK, SOFT, MUTE = "#2c3e50", "#57606a", "#8b949e"
GREEN, BORDER, BG_SOFT = "#42b983", "#eaecef", "#f6f8fa"


def main() -> None:
    img = Image.new("RGB", (W, H), "#ffffff")
    d = ImageDraw.Draw(img)

    title_f = ImageFont.truetype(HIRA, 86, index=2)
    sub_f = ImageFont.truetype(HIRA, 33, index=0)
    mono_f = ImageFont.truetype(HIRA, 38, index=0)
    foot_f = ImageFont.truetype(HIRA, 26, index=0)

    x = 96
    d.text((x, 128), "深入理解 AI Agent", font=title_f, fill=INK)
    d.text((x, 270), "设计原理与工程实践 · 一本完整开源的 AI Agent 技术书",
           font=sub_f, fill=SOFT)

    # The book's core formula, in a flat code-chip
    fy, fh = 374, 84
    ftext = "Agent = LLM + 上下文 + 工具"
    fw = d.textlength(ftext, font=mono_f) + 72
    d.rounded_rectangle([x, fy, x + fw, fy + fh], radius=8,
                        fill=BG_SOFT, outline=BORDER, width=2)
    d.text((x + 36, fy + 21), ftext, font=mono_f, fill=GREEN)

    d.text((x, 528), "bojieli/ai-agent-book · 10 章正文 · 92 个配套实验 · 5 种语言",
           font=foot_f, fill=MUTE)
    d.rectangle([0, H - 10, W, H], fill=GREEN)

    img.save("assets/og-card.png", optimize=True)
    print("wrote assets/og-card.png")


if __name__ == "__main__":
    main()
