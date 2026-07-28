#!/usr/bin/env python3
"""Verify that Chinese PDFs embed PingFang in SVG-derived figures.

Guards against the macOS-runner regression where PingFang (an on-demand font
since macOS Sequoia) is missing and rsvg-convert silently falls back to
Hiragino Sans, rendering Chinese figure text with Japanese glyph variants.

Usage: verify_pdf_fonts.py <pdf> [<pdf> ...]
"""

import re
import sys
import zlib
from collections import Counter

# A handful of Hiragino streams appear even in correct builds (rare glyphs
# PingFang lacks; the fontconfig cascade on CI falls back slightly more often
# than local CoreText: ~12 streams vs ~4). A wholesale fallback produces 50+.
HIRAGINO_LIMIT = 20


def scan(path):
    data = open(path, "rb").read()
    hits = Counter()
    for m in re.finditer(rb"stream\r?\n", data):
        start = m.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        try:
            decoded = zlib.decompress(data[start:end])
        except zlib.error:
            continue
        for name in (b"PingFang", b"Hiragino", b"Songti", b"Heiti", b"Noto"):
            if name in decoded:
                hits[name.decode()] += 1
    return hits


def main():
    failed = False
    for path in sys.argv[1:]:
        hits = scan(path)
        print(f"{path}: {dict(hits)}")
        if hits["PingFang"] == 0:
            print(f"  ERROR: no PingFang embedded -- figure font fallback occurred")
            failed = True
        if hits["Hiragino"] > HIRAGINO_LIMIT:
            print(f"  ERROR: {hits['Hiragino']} Hiragino streams (limit {HIRAGINO_LIMIT})"
                  " -- Japanese fallback font used for Chinese figure text")
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
