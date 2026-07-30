#!/bin/bash
# Build the complete book as a single PDF (ElegantBook design, teal/cyan theme).
# Requirements: pandoc, xelatex, ElegantBook class, rsvg-convert (librsvg),
#               Korean text (body, code, captions): Noto Serif/Sans CJK KR
#               or AppleMyungjo/Apple SD Gothic Neo (macOS fallback);
#               Simplified Chinese examples: Noto Sans CJK SC or
#               Songti SC/PingFang SC (macOS fallback);
#               Latin code: Menlo or DejaVu Sans Mono; symbols: Arial Unicode MS
#               or DejaVu Sans; final caption fallback: DejaVu Sans
# Usage: cd book-ko && bash build_pdf.sh
# ElegantBook has no `lang=ko`, so `lang=cn` provides the required CJK
# typesetting support while preamble.tex overrides reader-facing labels.
# Note: chapter/section numbers come from the document class; source headings
#       carry no manual numbers (see git history for the de-numbering pass).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# The full book exceeds XeTeX's default runtime memory on some TeX Live
# installations. Extend the existing format instead of rebuilding it.
export extra_mem_top=8000000
export extra_mem_bot=8000000
# Do not let missing macOS-only font probes trigger slow METAFONT attempts.
export MKTEXTFM=0

OUT="AI-Agents-in-Depth-ko.pdf"
CHAPTERS=(
    introduction.ko.md
    chapter1.ko.md
    chapter2.ko.md
    chapter3.ko.md
    chapter4.ko.md
    chapter5.ko.md
    chapter6.ko.md
    chapter7.ko.md
    chapter8.ko.md
    chapter9.ko.md
    chapter10.ko.md
    afterword.ko.md
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
    --lua-filter=korean_spacing.lua \
    --toc \
    --toc-depth=3 \
    --number-sections \
    -V documentclass=elegantbook \
    -V classoption=lang=cn \
    -V classoption=nofont \
    -V classoption=cyan \
    -V classoption=device=normal \
    -V author="Bojie Li" \
    --metadata title-meta="AI 에이전트를 깊이 이해하기: 설계 원리와 엔지니어링 실전" \
    --metadata author-meta="Bojie Li (한국어 번역: JeongJaeSoon)" \
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
