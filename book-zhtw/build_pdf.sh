#!/bin/bash
# Build the complete book as a single PDF (ElegantBook design, teal/cyan theme).
# Requirements: pandoc, xelatex, ElegantBook class, rsvg-convert (librsvg),
#               fonts: Songti SC / Heiti SC (ctex), Menlo, Arial Unicode MS
# Usage: cd book-zhtw && bash build_pdf.sh
# Note: chapter/section numbers come from the document class; source headings
#       carry no manual numbers (see git history for the de-numbering pass).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

OUT="深入理解-AI-Agent-李博杰-v1.3-zhtw.pdf"
CHAPTERS=(
    introduction.zhtw.md
    chapter1.zhtw.md
    chapter2.zhtw.md
    chapter3.zhtw.md
    chapter4.zhtw.md
    chapter5.zhtw.md
    chapter6.zhtw.md
    chapter7.zhtw.md
    chapter8.zhtw.md
    chapter9.zhtw.md
    chapter10.zhtw.md
    afterword.zhtw.md
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
    -V classoption=lang=cn \
    -V classoption=nofont \
    -V classoption=cyan \
    -V classoption=device=normal \
    -V author="李博杰" \
    --metadata title-meta="深入理解 AI Agent：設計原理與工程實踐" \
    --metadata author-meta="李博杰" \
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
