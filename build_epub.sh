#!/usr/bin/env bash
# Build EPUB 3 editions from the Markdown sources.
# Usage: ./build_epub.sh [all|zh-CN|zh-TW|en|es|id|ru|ta|vi|tr|ko|hu|ja|ar]
# Note: `all` does NOT include ja or ar while their PDF pipelines are being
# validated. Build them explicitly with `./build_epub.sh ja|ar`.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SELECTION="${1:-all}"

for command in pandoc pdftoppm python3; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Error: $command is required." >&2
        exit 1
    fi
done

case "$SELECTION" in
    all|zh-CN|zh-TW|en|es|id|ru|ta|vi|tr|ko|hu|ja|ar) ;;
    *)
        echo "Usage: $0 [all|zh-CN|zh-TW|en|es|id|ru|ta|vi|tr|ko|hu|ja|ar]" >&2
        exit 2
        ;;
esac

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ai-agent-book-epub.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

build_edition() {
    local language="$1"
    local directory title author pdf output title_label toc_label direction
    local -a chapters

    case "$language" in
        zh-CN)
            directory="book"
            title="深入理解 AI Agent：设计原理与工程实践"
            author="李博杰"
            pdf="深入理解-AI-Agent-李博杰-v1.4.pdf"
            output="深入理解-AI-Agent-李博杰-v1.4.epub"
            title_label="扉页"
            toc_label="目录"
            chapters=(introduction.md chapter{1..10}.md afterword.md)
            ;;
        zh-TW)
            directory="book-zhtw"
            title="深入理解 AI Agent：設計原理與工程實踐"
            author="李博杰；繁體中文（台灣）翻譯：tigercosmos"
            pdf="深入理解-AI-Agent-李博杰-v1.4-zhtw.pdf"
            output="深入理解-AI-Agent-李博杰-v1.4-zhtw.epub"
            title_label="扉頁"
            toc_label="目錄"
            chapters=(introduction.zhtw.md chapter{1..10}.zhtw.md afterword.zhtw.md)
            ;;
        en)
            directory="book-en"
            title="AI Agents in Depth: Design Principles and Engineering Practice"
            author="Bojie Li; English translation: Devaraj"
            pdf="AI-Agents-in-Depth-Bojie-Li-v1.4.pdf"
            output="AI-Agents-in-Depth-Bojie-Li-v1.4.epub"
            title_label="Title Page"
            toc_label="Table of Contents"
            chapters=(introduction.md chapter{1..10}.md afterword.md)
            ;;
        es)
            directory="book-es"
            title="Agentes de IA en Profundidad: Principios de Diseño y Práctica de Ingeniería"
            author="Bojie Li; traducción al español: Santh"
            pdf="AI-Agents-en-Profundidad-Bojie-Li-v1.4-es.pdf"
            output="AI-Agents-en-Profundidad-Bojie-Li-v1.4-es.epub"
            title_label="Portada"
            toc_label="Índice"
            chapters=(introduction.es.md chapter{1..10}.es.md afterword.es.md glossary.es.md reference-answers.es.md)
            ;;
        id)
            directory="book-id"
            title="Memahami AI Agent secara Mendalam: Prinsip Desain dan Praktik Rekayasa"
            author="Bojie Li; terjemahan bahasa Indonesia: JOICE HIELMAN ABBRORI"
            pdf="AI-Agents-in-Depth-Bojie-Li-v1.4-id.pdf"
            output="AI-Agents-in-Depth-Bojie-Li-v1.4-id.epub"
            title_label="Halaman Judul"
            toc_label="Daftar Isi"
            chapters=(introduction.md chapter{1..10}.md afterword.md)
            ;;
        ru)
            directory="book-ru"
            title="Глубокое понимание AI Agent: принципы проектирования и инженерная практика"
            author="Ли Боцзе (李博杰); русский перевод: ui99ru"
            pdf="AI-Agents-in-Depth-ru.pdf"
            output="AI-Agents-in-Depth-ru.epub"
            title_label="Титульный лист"
            toc_label="Содержание"
            chapters=(introduction.md chapter{1..10}.md afterword.md)
            ;;
        ta)
            directory="book-ta"
            title="AI Agents ஆழத்தில்: வடிவமைப்பு கோட்பாடுகள் மற்றும் பொறியியல் நடைமுறைகள்"
            author="Bojie Li; தமிழ் மொழிபெயர்ப்பு: Devaraj"
            pdf="AI-Agents-in-Depth-Bojie-Li-v1.4-ta.pdf"
            output="AI-Agents-in-Depth-Bojie-Li-v1.4-ta.epub"
            title_label="தலைப்புப் பக்கம்"
            toc_label="பொருளடக்கம்"
            chapters=(introduction.ta.md chapter{1..10}.ta.md afterword.ta.md)
            ;;
        vi)
            directory="book-vi"
            title="Hiểu sâu về AI Agent: Nguyên lý thiết kế và thực hành kỹ thuật"
            author="Lý Bác Kiệt; bản dịch tiếng Việt: Toàn Nguyễn"
            pdf="AI-Agents-in-Depth-Bojie-Li-v1.4-vi.pdf"
            output="AI-Agents-in-Depth-Bojie-Li-v1.4-vi.epub"
            title_label="Trang tiêu đề"
            toc_label="Mục lục"
            chapters=(introduction.vi.md glossary.vi.md chapter{1..10}.vi.md afterword.vi.md)
            ;;
        tr)
            directory="book-tr"
            title="AI Agent'ları Derinlemesine Anlamak: Tasarım İlkeleri ve Mühendislik Pratiği"
            author="Bojie Li; Türkçe çeviri: memisemre"
            pdf="AI-Agents-in-Depth-Bojie-Li-v1.4-tr.pdf"
            output="AI-Agents-in-Depth-Bojie-Li-v1.4-tr.epub"
            title_label="Başlık Sayfası"
            toc_label="İçindekiler"
            chapters=(introduction.tr.md chapter{1..10}.tr.md afterword.tr.md)
            ;;
        ko)
            directory="book-ko"
            title="AI 에이전트를 깊이 이해하기: 설계 원리와 엔지니어링 실전"
            author="Bojie Li; 한국어 번역: JeongJaeSoon"
            pdf="AI-Agents-in-Depth-ko.pdf"
            output="AI-Agents-in-Depth-ko.epub"
            title_label="표제지"
            toc_label="목차"
            chapters=(introduction.ko.md chapter{1..10}.ko.md afterword.ko.md)
            ;;
        hu)
            directory="book-hu"
            title="AI Agent – Tervezési elvek és gyakorlat"
            author="Bojie Li"
            pdf="AI-Agents-in-Depth-hu.pdf"
            output="AI-Agents-in-Depth-hu.epub"
            title_label="Címlap"
            toc_label="Tartalomjegyzék"
            chapters=(introduction.md chapter{1..10}.md afterword.md)
            ;;
        ja)
            directory="book-ja"
            title="AI Agent 徹底解説：設計原理とエンジニアリング実践"
            author="李博杰；日本語訳：Ikko Eltociear Ashimine"
            pdf="AI-Agents-in-Depth-Bojie-Li-v1.4-ja.pdf"
            output="AI-Agents-in-Depth-Bojie-Li-v1.4-ja.epub"
            title_label="扉"
            toc_label="目次"
            chapters=(introduction.ja.md chapter{1..10}.ja.md afterword.ja.md)
            ;;
        ar)
            directory="book-ar"
            title="فهم وكلاء الذكاء الاصطناعي بعمق: مبادئ التصميم والممارسة الهندسية"
            author="لي بوجي؛ الترجمة العربية: TheSyBuilder"
            pdf="AI-Agents-in-Depth-ar.pdf"
            output="AI-Agents-in-Depth-ar.epub"
            title_label="صفحة العنوان"
            toc_label="المحتويات"
            chapters=(introduction.ar.md chapter{1..10}.ar.md afterword.ar.md)
            ;;
    esac

    local edition_dir="$ROOT/$directory"
    direction="ltr"
    if [ "$language" = "ar" ]; then
        direction="rtl"
    fi
    local chapter
    for chapter in "${chapters[@]}" "$pdf"; do
        if [ ! -f "$edition_dir/$chapter" ]; then
            echo "Error: $directory/$chapter not found." >&2
            exit 1
        fi
    done

    local cover="$TMP_DIR/cover-$language.jpg"
    pdftoppm -f 1 -singlefile -jpeg -r 160 \
        "$edition_dir/$pdf" "${cover%.jpg}"

    echo "Building $language EPUB..."
    (
        cd "$edition_dir"
        pandoc "${chapters[@]}" \
            -o "$output" \
            --from markdown+lists_without_preceding_blankline \
            --to epub3 \
            --standalone \
            --toc \
            --toc-depth=3 \
            --number-sections \
            --mathml \
            --split-level=1 \
            --highlight-style=kate \
            --lua-filter="$ROOT/epub_external_links.lua" \
            --css="$ROOT/epub.css" \
            --epub-cover-image="$cover" \
            --metadata title="$title" \
            --metadata author="$author" \
            --metadata lang="$language" \
            --metadata dir="$direction" \
            --metadata identifier="https://github.com/bojieli/ai-agent-book#$language"
    )

    if [ "$language" = "ar" ]; then
        python3 "$ROOT/flatten_epub_toc.py" \
            "$edition_dir/$output" "$title_label" "$toc_label" rtl
    else
        python3 "$ROOT/flatten_epub_toc.py" \
            "$edition_dir/$output" "$title_label" "$toc_label"
    fi

    if command -v epubcheck >/dev/null 2>&1; then
        epubcheck "$edition_dir/$output"
    else
        echo "Built $directory/$output (install epubcheck to validate it)."
    fi
}

if [ "$SELECTION" = "all" ]; then
    for language in zh-CN zh-TW en es id ru ta vi tr ko hu; do
        build_edition "$language"
    done
else
    build_edition "$SELECTION"
fi
