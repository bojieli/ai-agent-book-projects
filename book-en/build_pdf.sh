#!/bin/bash
# Build the complete book as a single PDF (ElegantBook design, teal/cyan theme).
# Requirements: pandoc, xelatex, ElegantBook class, rsvg-convert (librsvg),
#               fonts: Menlo / Arial Unicode MS (macOS) — Linux auto-falls back
#               to DejaVu Sans/Mono and Noto CJK (see preamble.tex).
# Usage: cd book && bash build_pdf.sh
# Note: chapter/section numbers come from the document class; source headings
#       carry no manual numbers (see git history for the de-numbering pass).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Runtime environment tweaks (harmless on macOS, needed on Linux/TeX Live) ──
# 1) This book is large enough to exhaust XeTeX's default main memory
#    ("TeX capacity exceeded ... [main memory size=5000000]") during page
#    output. main_memory is baked into the format at dump time, but
#    extra_mem_top/bot extend an existing format at runtime — so we bump them
#    here instead of rebuilding the xelatex format.
export extra_mem_top=8000000
export extra_mem_bot=8000000
# 2) The mac-only monospace font (Menlo) is probed with \IfFontExistsTF in
#    preamble.tex. On systems without it, kpathsea otherwise spawns METAFONT to
#    build a Menlo.tfm (slow, noisy, always fails) before the DejaVu Sans Mono
#    fallback engages. Disabling on-the-fly TFM creation makes the probe return
#    immediately with the correct "not found" result.
export MKTEXTFM=0

OUT="AI-Agents-in-Depth-Bojie-Li-v1.3.pdf"
CHAPTERS=(
    introduction.md
    chapter1.md
    chapter2.md
    chapter3.md
    chapter4.md
    chapter5.md
    chapter6.md
    chapter7.md
    chapter8.md
    chapter9.md
    chapter10.md
    afterword.md
)

# Verify all chapters exist
for ch in "${CHAPTERS[@]}"; do
    if [ ! -f "$ch" ]; then
        echo "Error: $ch not found" >&2
        exit 1
    fi
done

echo "Building PDF from ${#CHAPTERS[@]} files..."

pandoc "${CHAPTERS[@]}" \
    -o "$OUT" \
    --from markdown+lists_without_preceding_blankline \
    --pdf-engine=xelatex \
    --lua-filter=crossref.lua \
    --lua-filter=experiment_box.lua \
    --toc \
    --toc-depth=3 \
    --number-sections \
    -V documentclass=elegantbook \
    -V classoption=lang=en \
    -V classoption=cyan \
    -V classoption=device=normal \
    -V author="Bojie Li" \
    --metadata title-meta="AI Agents in Depth: Design Principles and Engineering Practice" \
    --metadata author-meta="Bojie Li (English translation: Devaraj)" \
    -H preamble.tex \
    --include-before-body=cover.tex \
    --highlight-style=kate \
    --columns=80 \
    2>&1

if [ -f "$OUT" ]; then
    SIZE=$(du -h "$OUT" | cut -f1)
    PAGES=$(python3 -c "
import subprocess, re
r = subprocess.run(['pdfinfo', '$OUT'], capture_output=True, text=True)
m = re.search(r'Pages:\s+(\d+)', r.stdout)
print(m.group(1) if m else '?')
" 2>/dev/null || echo "?")
    echo ""
    echo "Done: $OUT ($SIZE, $PAGES pages)"
else
    echo "Error: PDF generation failed" >&2
    exit 1
fi
