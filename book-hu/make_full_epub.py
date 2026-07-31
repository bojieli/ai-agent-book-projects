#!/usr/bin/env python3
"""Build and validate the complete Hungarian EPUB 3 edition."""

from pathlib import Path
import shutil
import subprocess
import sys


BOOK_DIR = Path(__file__).resolve().parent
ROOT = BOOK_DIR.parent
OUTPUT = BOOK_DIR / "AI-Agent-Book_HU.epub"
CHAPTERS = [
    "introduction.md",
    *(f"chapter{number}.md" for number in range(1, 11)),
    "afterword.md",
    "reference-answers.md",
]


def require(command: str) -> str:
    path = shutil.which(command)
    if path is None:
        raise SystemExit(f"Hiba: a(z) {command} program szükséges az EPUB elkészítéséhez.")
    return path


def main() -> None:
    pandoc = require("pandoc")
    missing = [name for name in CHAPTERS if not (BOOK_DIR / name).is_file()]
    if missing:
        raise SystemExit(f"Hiba: hiányzó forrásfájlok: {', '.join(missing)}")

    command = [
        pandoc,
        *CHAPTERS,
        "-o",
        str(OUTPUT),
        "--from=markdown+lists_without_preceding_blankline-raw_html",
        "--to=epub3",
        "--standalone",
        "--toc",
        "--toc-depth=3",
        "--number-sections",
        "--mathml",
        "--split-level=1",
        "--highlight-style=kate",
        f"--lua-filter={ROOT / 'epub_external_links.lua'}",
        f"--css={ROOT / 'epub.css'}",
        "--metadata=title:AI Agent – Tervezési elvek és gyakorlat",
        "--metadata=author:Bojie Li",
        "--metadata=lang:hu",
        "--metadata=dir:ltr",
        "--metadata=identifier:https://github.com/bojieli/ai-agent-book#hu",
    ]
    subprocess.run(command, cwd=BOOK_DIR, check=True)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "flatten_epub_toc.py"),
            str(OUTPUT),
            "Címlap",
            "Tartalomjegyzék",
        ],
        check=True,
    )

    epubcheck = shutil.which("epubcheck")
    if epubcheck:
        subprocess.run([epubcheck, str(OUTPUT)], check=True)
    else:
        print("Figyelem: az epubcheck nem található; az EPUB-validáció kimaradt.")

    print(f"Elkészült: {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.1f} MiB)")


if __name__ == "__main__":
    main()
