#!/bin/bash
# Build the complete Arabic book as a single RTL PDF.
# Requirements: pandoc, xelatex, ElegantBook class, rsvg-convert (librsvg),
#               fonts: Noto Naskh Arabic or Amiri, Noto Sans Arabic,
#               and Courier New / DejaVu Sans Mono (see preamble.tex).
# Usage: cd book-ar && bash build_pdf.sh
#        PDF_ENGINE=tectonic bash build_pdf.sh  # lightweight local alternative
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
# 2) The mac-first monospace font (Courier New) is probed with
#    \IfFontExistsTF in preamble.tex. On systems without it, kpathsea otherwise
#    spawns METAFONT to build a TFM (slow, noisy, always fails) before the
#    DejaVu Sans Mono fallback engages. Disabling on-the-fly TFM creation makes
#    the probe return immediately with the correct "not found" result.
export MKTEXTFM=0

OUT="AI-Agents-in-Depth-v2.0-ar.pdf"
PDF_ENGINE="${PDF_ENGINE:-xelatex}"
CHAPTERS=(
    introduction.ar.md
    chapter1.ar.md
    chapter2.ar.md
    chapter3.ar.md
    chapter4.ar.md
    chapter5.ar.md
    chapter6.ar.md
    chapter7.ar.md
    chapter8.ar.md
    chapter9.ar.md
    chapter10.ar.md
    afterword.ar.md
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
    --pdf-engine="$PDF_ENGINE" \
    --lua-filter=crossref.lua \
    --lua-filter=experiment_box.lua \
    --toc \
    --toc-depth=3 \
    --number-sections \
    -V documentclass=elegantbook-ar \
    -V classoption=lang=en \
    -V classoption=cyan \
    -V classoption=device=normal \
    -V author="لي بوجي" \
    --metadata title-meta="فهم وكلاء الذكاء الاصطناعي بعمق: مبادئ التصميم والممارسة الهندسية" \
    --metadata author-meta="لي بوجي؛ الترجمة العربية: TheSyBuilder" \
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
