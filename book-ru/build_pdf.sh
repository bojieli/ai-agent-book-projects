#!/bin/bash
# Сборка русского перевода в единый PDF (ElegantBook, тема navy).
# Русская адаптация book-en/build_pdf.sh: главы и картинки берутся из этого каталога.
#
# Требуется: pandoc, xelatex, класс ElegantBook, и конвертер SVG→PDF —
#            rsvg-convert (librsvg) ЛИБО inkscape (у pandoc на Windows нет rsvg-convert).
#            Кириллический шрифт (Cambria/PT Serif/DejaVu Serif/Times New Roman) и
#            CJK-шрифт для остаточных иероглифов (Microsoft YaHei/Noto Sans CJK SC/…).
# Запуск:    cd book-ru && bash build_pdf.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

SRC_DIR="."
OUT="AI-Agents-in-Depth-ru.pdf"
NAMES=(introduction chapter1 chapter2 chapter3 chapter4 chapter5 chapter6 \
       chapter7 chapter8 chapter9 chapter10 afterword)

CHAPTERS=()
for n in "${NAMES[@]}"; do
    f="$SRC_DIR/$n.md"
    [ -f "$f" ] || { echo "Error: $f не найден" >&2; exit 1; }
    CHAPTERS+=("$f")
done

# ── SVG → PDF (pandoc не встраивает SVG в xelatex без конвертера) ──────────
# Русские подписи в схемах вписаны заранее (svg_lib.fit_overflow); здесь только
# растеризация в PDF. Идемпотентно: конвертируем лишь новые/изменённые файлы.
IMG_DIR="$SRC_DIR/images"
convert_one() {  # $1 = svg, $2 = pdf
    if command -v rsvg-convert >/dev/null 2>&1; then
        rsvg-convert -f pdf -o "$2" "$1"
    elif command -v inkscape >/dev/null 2>&1; then
        inkscape --export-type=pdf --export-filename="$2" "$1" >/dev/null 2>&1
    else
        return 1
    fi
}
if command -v rsvg-convert >/dev/null 2>&1 || command -v inkscape >/dev/null 2>&1; then
    n=0
    for svg in "$IMG_DIR"/*.svg; do
        [ -f "$svg" ] || continue
        pdf="${svg%.svg}.pdf"
        if [ ! -f "$pdf" ] || [ "$svg" -nt "$pdf" ]; then
            convert_one "$svg" "$pdf" && n=$((n+1))
        fi
    done
    echo "SVG → PDF: сконвертировано $n файл(ов)."
else
    echo "Warning: не найден ни rsvg-convert, ни inkscape — SVG-схемы не встроятся." >&2
fi

echo "Building PDF from ${#CHAPTERS[@]} files..."
pandoc "${CHAPTERS[@]}" \
    -o "$OUT" \
    --from markdown+lists_without_preceding_blankline \
    --pdf-engine=xelatex \
    --resource-path="$SRC_DIR" \
    --lua-filter=svg2pdf.lua \
    --lua-filter=crossref.lua \
    --lua-filter=experiment_box.lua \
    --toc --toc-depth=3 --number-sections \
    -V documentclass=elegantbook \
    -V classoption=lang=en \
    -V classoption=cyan \
    -V classoption=device=normal \
    -V author="Ли Боцзе (李博杰)" \
    --metadata title-meta="Глубокое понимание AI Agent: принципы проектирования и инженерная практика" \
    --metadata author-meta="Ли Боцзе" \
    -H preamble.tex \
    --include-before-body=cover.tex \
    --highlight-style=kate \
    --columns=80 \
    2>&1

if [ -f "$OUT" ]; then
    echo ""
    echo "Done: $OUT ($(du -h "$OUT" | cut -f1))"
else
    echo "Error: PDF generation failed" >&2
    exit 1
fi
