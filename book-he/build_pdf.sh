#!/bin/bash
# Build the Hebrew edition as a single RTL PDF.
#
# Engine: LuaLaTeX (not XeLaTeX as in Source/build_pdf.sh) — babel's
# bidi=basic needs LuaTeX, and it is the most reliable RTL route for a book
# that mixes Hebrew body text with Latin terms, code and URLs.
#
# Requirements: pandoc, lualatex + the packages listed in preamble.tex,
#               rsvg-convert (librsvg) for the SVG figures, and the Culmus
#               fonts shipped with TeX Live (David CLM / Nachlieli CLM).
# Usage: cd book-he && bash build_pdf.sh
#
# Figures live in book-he/images/. They are currently the English figure set:
# the SVG labels have not been translated to Hebrew yet.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# TinyTeX lives in the user's home directory (no admin install available).
if [ -d "$HOME/Library/TinyTeX/bin/universal-darwin" ]; then
    export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"
fi

export MKTEXTFM=0

OUT="AI-Agents-in-Depth-v2.0-he.pdf"
CHAPTERS=(
    introduction.he.md
    chapter1.he.md
    chapter2.he.md
    chapter3.he.md
    chapter4.he.md
    chapter5.he.md
    chapter6.he.md
    chapter7.he.md
    chapter8.he.md
    chapter9.he.md
    chapter10.he.md
    afterword.he.md
)

for ch in "${CHAPTERS[@]}"; do
    if [ ! -f "$ch" ]; then
        echo "Error: $ch not found" >&2
        exit 1
    fi
done

echo "Building Hebrew PDF from ${#CHAPTERS[@]} files..."

pandoc "${CHAPTERS[@]}" \
    -o "$OUT" \
    --from markdown+lists_without_preceding_blankline \
    --pdf-engine=lualatex \
    --lua-filter=experiment_box.lua \
    --toc \
    --toc-depth=3 \
    --number-sections \
    -V documentclass=book \
    -V classoption=oneside \
    -V author="בוג'י לי; תרגום לעברית: Itzik Woda" \
    --metadata title-meta="AI Agents in Depth (Hebrew edition)" \
    --metadata author-meta="Bojie Li; Hebrew translation: Itzik Woda" \
    -H preamble.tex \
    --include-before-body=cover.tex \
    --highlight-style=kate \
    --columns=80 \
    2>&1

if [ -f "$OUT" ]; then
    SIZE=$(du -h "$OUT" | cut -f1)
    PAGES=$(pdfinfo "$OUT" 2>/dev/null | awk '/^Pages:/ {print $2}')
    PAGES=${PAGES:-?}
    echo ""
    echo "Done: $OUT ($SIZE, $PAGES pages)"
else
    echo "Error: PDF generation failed" >&2
    exit 1
fi
