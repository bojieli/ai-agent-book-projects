#!/bin/bash
# Build the Vietnamese translation as a single PDF.
# Requirements: pandoc, xelatex, ElegantBook class, rsvg-convert/librsvg,
#               and fonts that support Vietnamese + CJK fallback.
# Usage: cd book-vi && bash build_pdf.sh

set -e
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Homebrew and MacTeX often are not visible inside non-login shells.
export PATH="/opt/homebrew/bin:/usr/local/bin:/Library/TeX/texbin:$PATH"

for cmd in pandoc xelatex rsvg-convert python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: $cmd not found in PATH." >&2
        if [ "$cmd" = "xelatex" ]; then
            echo "If MacTeX is installed, run: export PATH=\"/Library/TeX/texbin:\\$PATH\"" >&2
            echo "Then check: /Library/TeX/texbin/xelatex --version" >&2
        elif [ "$cmd" = "rsvg-convert" ]; then
            echo "Install it with: brew install librsvg" >&2
        elif [ "$cmd" = "pandoc" ]; then
            echo "Install it with: brew install pandoc" >&2
        fi
        exit 1
    fi
done

OUT="AI-Agents-in-Depth-Bojie-Li-v1.3-vi.pdf"
CHAPTERS=(
    introduction.vi.md
    glossary.vi.md
    chapter1.vi.md
    chapter2.vi.md
    chapter3.vi.md
    chapter4.vi.md
    chapter5.vi.md
    chapter6.vi.md
    chapter7.vi.md
    chapter8.vi.md
    chapter9.vi.md
    chapter10.vi.md
    afterword.vi.md
)

for ch in "${CHAPTERS[@]}"; do
    if [ ! -f "$ch" ]; then
        echo "Error: $ch not found. Run the translation step first." >&2
        exit 1
    fi
done

echo "Checking Vietnamese SVG layout..."
python3 fix_svg_text_layout.py --check

echo "Building Vietnamese PDF from ${#CHAPTERS[@]} files..."
echo "Note: after the initial Pandoc warnings, XeLaTeX may be quiet for several minutes."
echo "Full build log: build_pdf_vi.log"

LOG="build_pdf_vi.log"
: > "$LOG"

pandoc "${CHAPTERS[@]}" \
    -o "$OUT" \
    --from markdown+lists_without_preceding_blankline \
    --pdf-engine=xelatex \
    --pdf-engine-opt=-interaction=nonstopmode \
    --pdf-engine-opt=-halt-on-error \
    --pdf-engine-opt=-file-line-error \
    --lua-filter=crossref.lua \
    --lua-filter=experiment_box.lua \
    --toc \
    --toc-depth=3 \
    --number-sections \
    -V documentclass=elegantbook \
    -V classoption=lang=cn \
    -V classoption=fontset=fandol \
    -V classoption=cyan \
    -V classoption=device=normal \
    -V author="Lý Bác Kiệt" \
    --metadata title-meta="Hiểu sâu về AI Agent: Nguyên lý thiết kế và thực hành kỹ thuật" \
    --metadata author-meta="Lý Bác Kiệt" \
    -H preamble.tex \
    --include-before-body=cover.tex \
    --highlight-style=kate \
    --columns=80 \
    > "$LOG" 2>&1 &

PANDOC_PID=$!
START_TIME=$(date +%s)
while kill -0 "$PANDOC_PID" >/dev/null 2>&1; do
    sleep 30
    if ! kill -0 "$PANDOC_PID" >/dev/null 2>&1; then
        break
    fi
    NOW=$(date +%s)
    ELAPSED=$((NOW - START_TIME))
    echo "Still building... ${ELAPSED}s elapsed. Last log lines:"
    tail -5 "$LOG" || true
    echo "---"
done

if ! wait "$PANDOC_PID"; then
    echo "PDF build failed. Last 80 log lines:" >&2
    tail -80 "$LOG" >&2 || true
    exit 1
fi

cat "$LOG"


if [ -f "$OUT" ]; then
    SIZE=$(du -h "$OUT" | cut -f1)
    PAGES=$(pdfinfo "$OUT" 2>/dev/null | awk '/^Pages:/ {print $2; exit}')
    PAGES=${PAGES:-?}
    echo ""
    echo "Done: $OUT ($SIZE, $PAGES pages)"
else
    echo "Error: PDF generation failed" >&2
    exit 1
fi
