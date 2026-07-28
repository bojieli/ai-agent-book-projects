"""SVG diagram generation library for book illustrations.

Style: black/white/grayscale for B&W printing.
- White (#fff) backgrounds
- Light gray (#f0f0f0) box fills
- Medium gray (#d0d0d0) secondary fills
- Dark gray (#999) emphasis fills
- Black (#333) borders and text
- 2px stroke, 6px rounded corners
- Sans-serif fonts (20px body, 16px small, 24px title)
- Designed for print: readable at 50-60% scaling
"""

import html
import math
import os
import re

COLORS = {
    'white': '#ffffff',
    'light': '#f0f0f0',
    'medium': '#d0d0d0',
    'dark': '#999999',
    'darker': '#666666',
    'border': '#333333',
    'text': '#333333',
    'text_light': '#666666',
    'bg': '#ffffff',
    'code_bg': '#f5f5f5',
}

FONT = "Arial, 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', sans-serif"
MONO = "'Courier New', Courier, monospace"
STROKE_W = 2
CORNER_R = 6

FS_TITLE = 24
FS_BODY = 20
FS_SMALL = 16
FS_TINY = 14
FS_LABEL = 16

# Per academic convention: the figure itself does not include a title; the title is written in the main text.
# When OMIT_TITLE=True, any 'title-type' text with font_size==FS_TITLE (except short symbols like
# VS/→/+) is treated as a figure title and not rendered—regardless of whether it is at the top or middle of the figure (section titles
# of multi-panel figures are also removed). Short symbols are preserved via the TITLE_MIN_LEN length threshold.
OMIT_TITLE = True
TITLE_Y_THRESHOLD = 60   # Kept for backward compatibility; no longer relied upon independently
TITLE_MIN_LEN = 4        # Only FS_TITLE text with length >= this value is considered a title and removed
TITLE_CROP_PX = 40


def _escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


# ── Text width estimation ──────────────────────────────────────────────
# Approximate advance widths for Helvetica/Arial (units per 1000 em). Used to
# fit text inside boxes/badges so the (wider) English translations do not
# overflow shapes that were originally sized for compact CJK text.
_CHAR_W = {
    ' ': 278, '!': 278, '"': 355, '#': 556, '$': 556, '%': 889, '&': 667,
    "'": 191, '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333,
    '.': 278, '/': 278, '0': 556, '1': 556, '2': 556, '3': 556, '4': 556,
    '5': 556, '6': 556, '7': 556, '8': 556, '9': 556, ':': 278, ';': 278,
    '<': 584, '=': 584, '>': 584, '?': 556, '@': 1015, 'A': 667, 'B': 667,
    'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722, 'I': 278,
    'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722, 'O': 778, 'P': 667,
    'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944,
    'X': 667, 'Y': 667, 'Z': 611, '[': 278, '\\': 278, ']': 278, '^': 469,
    '_': 556, '`': 333, 'a': 556, 'b': 556, 'c': 500, 'd': 556, 'e': 556,
    'f': 278, 'g': 556, 'h': 556, 'i': 222, 'j': 222, 'k': 500, 'l': 222,
    'm': 833, 'n': 556, 'o': 556, 'p': 556, 'q': 556, 'r': 333, 's': 500,
    't': 278, 'u': 556, 'v': 500, 'w': 722, 'x': 500, 'y': 500, 'z': 500,
    '{': 334, '|': 260, '}': 334, '~': 584,
}

# Narrow / specific non-ASCII glyphs (per 1000 em).
_SPECIAL_W = {
    '·': 300, '°': 400, '‘': 278, '’': 278, '“': 500, '”': 500, '–': 556,
    '≈': 584, '×': 584, '÷': 584, '…': 1000, '—': 1000, '•': 400, '′': 278,
    '£': 556, '€': 556, '¥': 556, '§': 556, '™': 1000, '®': 737, '©': 737,
}


def _is_wide(ch):
    """Return True for glyphs that render roughly one full em wide (CJK, kana,
    circled numbers, geometric shapes, check marks, arrows, etc.)."""
    o = ord(ch)
    return (
        0x1100 <= o <= 0x115F or   # Hangul Jamo
        0x2460 <= o <= 0x24FF or   # enclosed alphanumerics ①②③
        0x2500 <= o <= 0x257F or   # box drawing
        0x25A0 <= o <= 0x25FF or   # geometric shapes △▲■
        0x2600 <= o <= 0x27BF or   # misc symbols & dingbats ✓✗★
        0x2E80 <= o <= 0xA4CF or   # CJK, kana, radicals
        0xAC00 <= o <= 0xD7A3 or   # Hangul syllables
        0xF900 <= o <= 0xFAFF or   # CJK compatibility
        0xFE30 <= o <= 0xFE4F or   # CJK compatibility forms
        0xFF00 <= o <= 0xFF60 or   # fullwidth forms
        0xFFE0 <= o <= 0xFFE6 or   # fullwidth signs
        o in (0x2190, 0x2191, 0x2192, 0x2193, 0x21D2, 0x2194)  # arrows
    )


def _char_w(ch, mono=False):
    if mono:
        return 600
    if ch in _SPECIAL_W:
        return _SPECIAL_W[ch]
    if _is_wide(ch):
        return 1000
    if ord(ch) < 0x100:
        return _CHAR_W.get(ch, 556)
    return 600


def _text_width(s, font_size, bold=False, mono=False):
    """Estimated rendered width of a single line of text, in pixels."""
    total = sum(_char_w(ch, mono) for ch in str(s))
    px = total / 1000.0 * font_size
    return px * 1.045 if bold else px


def _units(s):
    """Split a string into wrap units: latin words, single spaces, and single
    wide chars (each wide char is an independent break opportunity)."""
    units = []
    prev = None  # 'word' | 'space' | 'wide'
    for ch in s:
        if ch == ' ':
            units.append(' ')
            prev = 'space'
        elif _is_wide(ch):
            units.append(ch)
            prev = 'wide'
        else:
            if prev == 'word':
                units[-1] += ch
            else:
                units.append(ch)
            prev = 'word'
    return units


def _wrap_line(s, avail_w, font_size, bold=False, mono=False):
    """Greedy word-wrap of one logical line to fit avail_w pixels."""
    if avail_w <= 0 or _text_width(s, font_size, bold, mono) <= avail_w:
        return [s]
    lines = []
    cur = ''
    for u in _units(s):
        if u == ' ':
            candidate = cur + ' ' if cur else ''
        else:
            candidate = cur + u
        if cur == '' or _text_width(candidate, font_size, bold, mono) <= avail_w:
            cur = candidate
        else:
            lines.append(cur.rstrip())
            cur = '' if u == ' ' else u
    if cur.strip():
        lines.append(cur.rstrip())
    return lines or ['']


def _fit_font(s, avail_w, font_size, bold=False, mono=False, min_size=8):
    """Shrink font_size until the (unwrapped) string fits avail_w."""
    fs = font_size
    while fs > min_size and _text_width(s, fs, bold, mono) > avail_w:
        fs -= 0.5
    return fs


def _extent(x, w, anchor):
    """Return (left, right) pixel extent of a text run of width w anchored at x."""
    if anchor == 'start':
        return x, x + w
    if anchor == 'end':
        return x - w, x
    return x - w / 2, x + w / 2  # middle


# ── In-place overflow correction ───────────────────────────────────────
# Shrinks any <text> that overflows its smallest containing <rect> or the
# canvas. Only the font-size is changed (never positions), so it is safe and
# idempotent. Used both by SVG.render() (so generated figures self-correct
# standalone labels) and by fit_svg_text.py (to repair static/orphaned SVGs
# that no longer have a generator).
_TEXT_TAG = re.compile(r'<text\b([^>]*)>(.*?)</text>', re.S)
_RECT_TAG = re.compile(
    r'<rect\b[^>]*?x="([-\d.]+)"[^>]*?y="([-\d.]+)"[^>]*?'
    r'width="([-\d.]+)"[^>]*?height="([-\d.]+)"'
)
_VIEWBOX = re.compile(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"')
_ATTR = lambda attrs, name: (re.search(name + r'="([^"]*)"', attrs) or [None, None])[1]


def fit_overflow(svg, pad=5, min_size=7.0):
    """Return svg with over-wide text runs shrunk to fit their box/canvas."""
    mvb = _VIEWBOX.search(svg)
    if mvb:
        vb_x, _vb_y, vb_w, _vb_h = (float(g) for g in mvb.groups())
    else:
        vb_x, vb_w = 0.0, 1e9
    vb_right = vb_x + vb_w

    rects = [tuple(float(g) for g in m.groups()) for m in _RECT_TAG.finditer(svg)]

    def repl(m):
        attrs, content = m.group(1), m.group(2)
        text = html.unescape(re.sub(r'<[^>]+>', '', content))
        if not text.strip():
            return m.group(0)
        try:
            x = float(_ATTR(attrs, 'x'))
            y = float(_ATTR(attrs, 'y'))
            fs = float(_ATTR(attrs, 'font-size'))
        except (TypeError, ValueError):
            return m.group(0)
        anchor = _ATTR(attrs, 'text-anchor') or 'start'
        fam = _ATTR(attrs, 'font-family') or ''
        bold = (_ATTR(attrs, 'font-weight') == 'bold')
        mono = 'Courier' in fam
        floor = 6.0 if mono else min_size  # dense code insets tolerate a smaller floor
        w = _text_width(text, fs, bold, mono)
        lo, hi = _extent(x, w, anchor)

        # available width from the canvas
        if anchor == 'start':
            avail = vb_right - x
        elif anchor == 'end':
            avail = x - vb_x
        else:
            avail = 2 * min(x - vb_x, vb_right - x)

        # available width from the smallest containing rect
        cont = [r for r in rects
                if r[0] - 1 <= x <= r[0] + r[2] + 1 and r[1] - 1 <= y <= r[1] + r[3] + 1]
        if cont:
            rx, _ry, rw, _rh = min(cont, key=lambda r: r[2] * r[3])
            left, right = rx + pad, rx + rw - pad
            if anchor == 'start':
                box_avail = right - x
            elif anchor == 'end':
                box_avail = x - left
            else:
                box_avail = 2 * min(x - left, right - x)
            avail = min(avail, box_avail)

        if w <= avail + 1 or avail <= 0:
            if avail <= 0:
                new_fs = floor
            else:
                return m.group(0)
        else:
            # Floor (not round) to 0.5px so the shrunk text never re-overflows.
            new_fs = max(floor, math.floor(fs * avail / w * 2) / 2)
        if new_fs >= fs:
            return m.group(0)
        new_attrs = re.sub(r'font-size="[^"]*"', f'font-size="{new_fs:g}"', attrs)
        return f'<text{new_attrs}>{content}</text>'

    return _TEXT_TAG.sub(repl, svg)


def _marker_def():
    return (
        '<defs>'
        '<marker id="ah" markerWidth="12" markerHeight="8" refX="12" refY="4" orient="auto">'
        f'<polygon points="0 0, 12 4, 0 8" fill="{COLORS["border"]}"/>'
        '</marker>'
        '<marker id="ah-light" markerWidth="12" markerHeight="8" refX="12" refY="4" orient="auto">'
        f'<polygon points="0 0, 12 4, 0 8" fill="{COLORS["dark"]}"/>'
        '</marker>'
        '</defs>'
    )


class SVG:
    """SVG diagram builder."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.elems = []

    def rect(self, x, y, w, h, fill='light', stroke='border', rx=CORNER_R, dash=False):
        c_fill = COLORS.get(fill, fill)
        c_stroke = COLORS.get(stroke, stroke)
        d = ' stroke-dasharray="8,4"' if dash else ''
        self.elems.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{c_fill}" stroke="{c_stroke}" stroke-width="{STROKE_W}"{d}/>'
        )

    def box(self, x, y, w, h, label, fill='light', sublabel=None, bold=False, font_size=FS_BODY):
        self.rect(x, y, w, h, fill=fill)
        pad = 10
        avail_w = max(8, w - 2 * pad)
        main_raw = str(label).split('\n')
        sub_raw = str(sublabel).split('\n') if sublabel else []

        # Shrink the font until wrapped text fits both the width and the height
        # of the box (English translations are wider than the original CJK).
        fs = font_size
        while True:
            sub_fs = max(fs - 2, 8)
            main_lines = []
            for ln in main_raw:
                main_lines += _wrap_line(ln, avail_w, fs, bold)
            sub_lines = []
            for ln in sub_raw:
                sub_lines += _wrap_line(ln, avail_w, sub_fs, False)
            line_h = fs * 1.3
            total_h = (len(main_lines) + len(sub_lines)) * line_h
            widest = max(
                [_text_width(l, fs, bold) for l in main_lines]
                + [_text_width(l, sub_fs, False) for l in sub_lines]
                + [0]
            )
            if (total_h <= h - 6 and widest <= avail_w) or fs <= 9:
                break
            fs -= 0.5

        rendered = [(l, fs, bold, 'text') for l in main_lines] \
            + [(l, sub_fs, False, 'text_light') for l in sub_lines]
        line_h = fs * 1.3
        n = len(rendered)
        start_y = y + h / 2 - (n - 1) * line_h / 2
        for i, (line, lfs, lbold, lfill) in enumerate(rendered):
            ly = start_y + i * line_h
            fw = 'bold' if lbold else 'normal'
            self.elems.append(
                f'<text x="{x + w / 2}" y="{ly}" font-family="{FONT}" font-size="{lfs}" '
                f'fill="{COLORS[lfill]}" text-anchor="middle" dominant-baseline="central" '
                f'font-weight="{fw}">{_escape(line)}</text>'
            )

    def text(self, x, y, content, size=FS_BODY, bold=False, anchor='middle', fill='text', baseline='central', max_width=None):
        # Skip in-figure titles per academic convention (titles belong in body text).
        # Drop any FS_TITLE-sized phrase anywhere in the figure; keep short symbols
        # (VS / → / + etc.) which also happen to use the title size as diagram content.
        if OMIT_TITLE and size == FS_TITLE and len(str(content).strip()) >= TITLE_MIN_LEN:
            return
        if max_width:
            size = _fit_font(content, max_width, size, bold)
        c = COLORS.get(fill, fill)
        fw = 'bold' if bold else 'normal'
        self.elems.append(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{c}" '
            f'text-anchor="{anchor}" dominant-baseline="{baseline}" font-weight="{fw}">'
            f'{_escape(content)}</text>'
        )

    def mono(self, x, y, content, size=FS_SMALL, anchor='start', fill='text', max_width=None):
        """Monospace text for code snippets."""
        if max_width:
            size = _fit_font(content, max_width, size, mono=True)
        c = COLORS.get(fill, fill)
        self.elems.append(
            f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{c}" '
            f'text-anchor="{anchor}" dominant-baseline="central">'
            f'{_escape(content)}</text>'
        )

    def code_block(self, x, y, w, lines, font_size=FS_SMALL, line_h=None):
        """Render a block of monospace code lines with background."""
        avail = w - 20
        fs = font_size
        while fs > 6 and max((_text_width(l, fs, mono=True) for l in lines), default=0) > avail:
            fs -= 0.5
        if line_h is None:
            line_h = fs * 1.5
        h = len(lines) * line_h + 12
        self.rect(x, y, w, h, fill='code_bg', stroke='dark', rx=4)
        for i, line in enumerate(lines):
            ly = y + 10 + i * line_h + line_h / 2
            self.mono(x + 10, ly, line, size=fs)
        return h

    def multiline_text(self, x, y, lines, size=FS_BODY, anchor='middle', fill='text', line_h=None, bold=False, max_width=None):
        """Render multiple lines of text."""
        if line_h is None:
            line_h = size * 1.4
        for i, line in enumerate(lines):
            ly = y + i * line_h
            self.text(x, ly, line, size=size, anchor=anchor, fill=fill, bold=bold, max_width=max_width)

    def text_block(self, x, top_y, max_w, items, size=FS_SMALL, min_size=8,
                   line_gap=1.2, bold=False, anchor='middle', mono=False):
        """Word-wrap one or more captions to max_w at a single uniform font size
        (shrinking only if an unbreakable token is too wide), then stack them
        downward from top_y. Prevents the "long line shrunk tiny while the short
        line stays large" look that plain text()+fit_overflow produces.

        items: list of strings or (text, fill) tuples. Returns the bottom y.
        """
        norm = [t if isinstance(t, tuple) else (t, 'text') for t in items]

        def wrap_all(f):
            out = []
            for t, fl in norm:
                for ln in _wrap_line(str(t), max_w, f, bold, mono):
                    out.append((ln, fl))
            return out

        fs = size
        wrapped = wrap_all(fs)
        while fs > min_size and max((_text_width(l, fs, bold, mono) for l, _ in wrapped), default=0) > max_w:
            fs -= 0.5
            wrapped = wrap_all(fs)

        lh = fs * line_gap
        y = top_y + fs * 0.85
        for ln, fl in wrapped:
            if mono:
                self.mono(x, y, ln, size=fs, anchor=anchor, fill=fl)
            else:
                self.text(x, y, ln, size=fs, anchor=anchor, fill=fl, bold=bold)
            y += lh
        return y - lh + fs * 0.15

    def arrow(self, x1, y1, x2, y2, label=None, dash=False, color='border'):
        c = COLORS.get(color, color)
        d = ' stroke-dasharray="8,4"' if dash else ''
        mk = 'ah-light' if color in ('dark', COLORS['dark']) else 'ah'
        self.elems.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{c}" stroke-width="{STROKE_W}"{d} marker-end="url(#{mk})"/>'
        )
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self.elems.append(
                f'<text x="{mx}" y="{my - 10}" font-family="{FONT}" font-size="{FS_LABEL}" '
                f'fill="{COLORS["text_light"]}" text-anchor="middle">{_escape(label)}</text>'
            )

    def arrow_curved(self, x1, y1, x2, y2, curve=30, label=None, dash=False, color='border'):
        """Draw a curved arrow using a quadratic bezier."""
        c = COLORS.get(color, color)
        d = ' stroke-dasharray="8,4"' if dash else ''
        mk = 'ah-light' if color in ('dark', COLORS['dark']) else 'ah'
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            nx, ny = -dy / dist * curve, dx / dist * curve
        else:
            nx, ny = 0, -curve
        cx, cy = mx + nx, my + ny
        self.elems.append(
            f'<path d="M {x1},{y1} Q {cx},{cy} {x2},{y2}" fill="none" '
            f'stroke="{c}" stroke-width="{STROKE_W}"{d} marker-end="url(#{mk})"/>'
        )
        if label:
            lx, ly = (x1 + 2 * cx + x2) / 4, (y1 + 2 * cy + y2) / 4
            self.text(lx, ly - 10, label, size=FS_LABEL, fill='text_light')

    def line(self, x1, y1, x2, y2, dash=False, color='border'):
        c = COLORS.get(color, color)
        d = ' stroke-dasharray="8,4"' if dash else ''
        self.elems.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{c}" stroke-width="{STROKE_W}"{d}/>'
        )

    def circle(self, cx, cy, r, fill='light', label=None, font_size=FS_SMALL):
        c = COLORS.get(fill, fill)
        self.elems.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{c}" '
            f'stroke="{COLORS["border"]}" stroke-width="{STROKE_W}"/>'
        )
        if label:
            fs = _fit_font(label, r * 1.7, font_size)
            self.elems.append(
                f'<text x="{cx}" y="{cy}" font-family="{FONT}" font-size="{fs}" '
                f'fill="{COLORS["text"]}" text-anchor="middle" dominant-baseline="central">'
                f'{_escape(label)}</text>'
            )

    def diamond(self, cx, cy, w, h, fill='light', label=None, font_size=FS_SMALL):
        c = COLORS.get(fill, fill)
        pts = f'{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}'
        self.elems.append(
            f'<polygon points="{pts}" fill="{c}" stroke="{COLORS["border"]}" stroke-width="{STROKE_W}"/>'
        )
        if label:
            fs = _fit_font(label, w * 0.6, font_size)
            self.elems.append(
                f'<text x="{cx}" y="{cy}" font-family="{FONT}" font-size="{fs}" '
                f'fill="{COLORS["text"]}" text-anchor="middle" dominant-baseline="central">'
                f'{_escape(label)}</text>'
            )

    def brace_right(self, x, y1, y2, label=None):
        my = (y1 + y2) / 2
        d = (f'M {x},{y1} C {x + 20},{y1} {x + 20},{my - 5} {x + 25},{my} '
             f'C {x + 20},{my + 5} {x + 20},{y2} {x},{y2}')
        self.elems.append(
            f'<path d="{d}" fill="none" stroke="{COLORS["border"]}" stroke-width="{STROKE_W}"/>'
        )
        if label:
            self.text(x + 35, my, label, size=FS_SMALL, anchor='start')

    def group_box(self, x, y, w, h, label, fill='white'):
        """A dashed group boundary with a label at top-left."""
        self.rect(x, y, w, h, fill=fill, rx=8, dash=True)
        self.text(x + 12, y + 18, label, size=FS_SMALL, bold=True, fill='text_light',
                  anchor='start', max_width=w - 24)

    def badge(self, x, y, w, h, label, fill='dark', font_size=FS_SMALL):
        """Small rounded badge/tag. Widens (keeping its center) to fit the label."""
        need = _text_width(label, font_size, bold=True) + h + 8
        if need > w:
            cx = x + w / 2
            w = need
            x = cx - w / 2
        self.rect(x, y, w, h, fill=fill, rx=h // 2)
        self.text(x + w / 2, y + h / 2, label, size=font_size, fill='white', bold=True)

    def render(self):
        if OMIT_TITLE:
            crop = TITLE_CROP_PX
            vb = f'0 {crop} {self.width} {self.height - crop}'
            h_attr = self.height - crop
        else:
            vb = f'0 0 {self.width} {self.height}'
            h_attr = self.height
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" '
            f'width="{self.width}" height="{h_attr}" '
            f'style="background:{COLORS["bg"]}">',
            _marker_def(),
        ]
        parts.extend(self.elems)
        parts.append('</svg>')
        return fit_overflow('\n'.join(parts))

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.render())


def flow_lr(nodes, width=800, node_h=55, node_w=None, fills=None, spacing=25):
    """Left-to-right flow diagram: nodes connected by arrows."""
    n = len(nodes)
    if node_w is None:
        node_w = min(150, (width - spacing * (n + 1)) // n)
    total_w = n * node_w + (n - 1) * spacing
    x_start = (width - total_w) / 2
    height = node_h + 70
    svg = SVG(width, height)
    y = (height - node_h) / 2
    positions = []
    for i, label in enumerate(nodes):
        x = x_start + i * (node_w + spacing)
        f = (fills[i] if fills else 'light') if fills and i < len(fills) else 'light'
        svg.box(x, y, node_w, node_h, label, fill=f)
        positions.append((x, y))
        if i > 0:
            px = positions[i - 1][0] + node_w
            svg.arrow(px + 2, y + node_h / 2, x - 2, y + node_h / 2)
    return svg


def flow_tb(nodes, width=350, node_h=55, node_w=240, fills=None, spacing=35, arrow_labels=None):
    """Top-to-bottom flow diagram."""
    n = len(nodes)
    height = n * node_h + (n - 1) * spacing + 50
    svg = SVG(width, height)
    x = (width - node_w) / 2
    positions = []
    for i, label in enumerate(nodes):
        y = 25 + i * (node_h + spacing)
        f = (fills[i] if fills else 'light') if fills and i < len(fills) else 'light'
        svg.box(x, y, node_w, node_h, label, fill=f)
        positions.append((x, y))
        if i > 0:
            al = arrow_labels[i - 1] if arrow_labels and i - 1 < len(arrow_labels) else None
            svg.arrow(x + node_w / 2, positions[i - 1][1] + node_h + 2,
                      x + node_w / 2, y - 2, label=al)
    return svg


def tree_diagram(root, children, width=750, root_h=60, child_h=55, child_w=None, root_w=220):
    """Tree diagram: root node with children below."""
    n = len(children)
    if child_w is None:
        child_w = min(170, (width - 20) // max(n, 1))
    spacing = 20
    total_cw = n * child_w + (n - 1) * spacing
    x_start = (width - total_cw) / 2
    height = root_h + child_h + 120
    svg = SVG(width, height)
    rx = (width - root_w) / 2
    svg.box(rx, 20, root_w, root_h, root, fill='medium', bold=True)
    root_cx = width / 2
    root_bot = 20 + root_h
    for i, label in enumerate(children):
        cx = x_start + i * (child_w + spacing) + child_w / 2
        cy = root_bot + 55
        svg.line(root_cx, root_bot, cx, cy)
        svg.box(x_start + i * (child_w + spacing), cy, child_w, child_h, label)
    return svg


def layer_diagram(layers, width=600, layer_h=55, spacing=14):
    """Stacked horizontal layers (top = first layer)."""
    n = len(layers)
    lw = width - 80
    height = n * layer_h + (n - 1) * spacing + 50
    svg = SVG(width, height)
    x = 40
    for i, (label, fill) in enumerate(layers):
        y = 25 + i * (layer_h + spacing)
        svg.box(x, y, lw, layer_h, label, fill=fill)
    return svg


def comparison_lr(left_title, left_items, right_title, right_items, width=750, item_h=45):
    """Side-by-side comparison diagram."""
    col_w = (width - 100) // 2
    n = max(len(left_items), len(right_items))
    height = 80 + n * (item_h + 10) + 25
    svg = SVG(width, height)
    lx = 25
    rx = width - col_w - 25
    svg.box(lx, 20, col_w, 50, left_title, fill='medium', bold=True)
    svg.box(rx, 20, col_w, 50, right_title, fill='medium', bold=True)
    for i, label in enumerate(left_items):
        y = 85 + i * (item_h + 10)
        svg.box(lx, y, col_w, item_h, label, fill='light')
    for i, label in enumerate(right_items):
        y = 85 + i * (item_h + 10)
        svg.box(rx, y, col_w, item_h, label, fill='light')
    return svg


def cycle_diagram(nodes, width=480, height=480, radius=160):
    """Circular cycle diagram with arrows between nodes."""
    n = len(nodes)
    cx, cy = width / 2, height / 2
    svg = SVG(width, height)
    node_w, node_h = 120, 50
    positions = []
    for i in range(n):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        nx = cx + radius * math.cos(angle)
        ny = cy + radius * math.sin(angle)
        positions.append((nx, ny))
        svg.box(nx - node_w / 2, ny - node_h / 2, node_w, node_h, nodes[i], fill='light', font_size=FS_SMALL)

    for i in range(n):
        j = (i + 1) % n
        x1, y1 = positions[i]
        x2, y2 = positions[j]
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / dist, dy / dist
        offset_start = max(node_w, node_h) / 2 + 5
        offset_end = max(node_w, node_h) / 2 + 5
        svg.arrow(x1 + ux * offset_start, y1 + uy * offset_start,
                  x2 - ux * offset_end, y2 - uy * offset_end)
    return svg
