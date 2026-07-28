#!/bin/bash
# Build the complete book as a single PDF (ElegantBook design, teal/cyan theme).
# Requirements: pandoc, xelatex, ElegantBook class, rsvg-convert (librsvg),
#               Japanese fonts: Hiragino Mincho ProN / Hiragino Sans (macOS) or
#               Noto Serif CJK JP / Noto Sans CJK JP (Linux/CI), Menlo
# Usage: cd book-ja && bash build_pdf.sh
# NOTE: This build is UNVALIDATED (no Japanese LaTeX toolchain was available when
#       it was written). ElegantBook has no `lang=jp`, so structural labels
#       (章/図/表, TOC) come from `lang=cn`; verify with a real xelatex run and
#       adjust fonts/labels as needed before enabling in CI.
# Note: chapter/section numbers come from the document class; source headings
#       carry no manual numbers (see git history for the de-numbering pass).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

OUT="AI-Agents-in-Depth-Bojie-Li-v1.3-ja.pdf"
CHAPTERS=(
    introduction.ja.md
    chapter1.ja.md
    chapter2.ja.md
    chapter3.ja.md
    chapter4.ja.md
    chapter5.ja.md
    chapter6.ja.md
    chapter7.ja.md
    chapter8.ja.md
    chapter9.ja.md
    chapter10.ja.md
    afterword.ja.md
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
    --metadata title-meta="AI Agent 徹底解説：設計原理とエンジニアリング実践" \
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
