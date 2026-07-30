#! /usr/bin/env python3
"""Generate EPUB from all Hungarian translated chapters"""

import os
import re
import sys
from ebooklib import epub, ITEM_IMAGE
import markdown

book_dir = os.path.dirname(os.path.abspath(__file__))

# All chapters in order
chapters = [
    ("introduction.md", "Bevezető"),
    ("chapter1.md", "1. fejezet: A Harness-ek alapjai"),
    ("chapter2.md", "2. fejezet: Kontextusmérnökség"),
    ("chapter3.md", "3. fejezet: Felhasználói memória és Tudásbázis"),
    ("chapter4.md", "4. fejezet: Eszközök"),
    ("chapter5.md", "5. fejezet: Kódoló Agent és eszközfejlesztés"),
    ("chapter6.md", "6. fejezet: Ügynökök kiértékelése"),
    ("chapter7.md", "7. fejezet: Modell finomhangolás"),
    ("chapter8.md", "8. fejezet: Munkafolyamatok és orchestáció"),
    ("chapter9.md", "9. fejezet: Multimodalitás"),
    ("chapter10.md", "10. fejezet: Többügynökös együttműködés"),
    ("afterword.md", "Utószó"),
    ("reference-answers.md", "Függelék: Gondolkodtató kérdések válaszai"),
]

# Check which files exist
existing = []
missing = []
for fname, title in chapters:
    fpath = os.path.join(book_dir, fname)
    if os.path.exists(fpath):
        existing.append((fname, title, fpath))
    else:
        print(f"⚠️  HIÁNYZIK: {fname}")
        missing.append(fname)

if missing:
    print(f"❌ Hiányzó fejezetek: {', '.join(missing)}")
    sys.exit(1)

if not existing:
    print("❌ Nincs egyetlen fájl sem!")
    sys.exit(1)

# Create EPUB book
book = epub.EpubBook()

# Metadata
book.set_identifier("ai-agent-book-hu-001")
book.set_title("AI Agent – Tervezési elvek és gyakorlat (magyar)")
book.set_language("hu")
book.add_author("Li Bojie")
book.add_metadata("DC", "description", "Az 'AI Agent: Tervezési elvek és gyakorlat' című könyv teljes magyar fordítása.")

# CSS
style = """
body { font-family: 'Liberation Serif', Georgia, serif; line-height: 1.6; margin: 1em; }
h1, h2, h3, h4 { font-family: 'Liberation Sans', Arial, sans-serif; }
h1 { font-size: 1.6em; margin-top: 1.5em; }
h2 { font-size: 1.3em; margin-top: 1.2em; }
h3 { font-size: 1.1em; margin-top: 1em; }
h4 { font-size: 1.05em; margin-top: 0.8em; }
p { margin: 0.5em 0; text-align: justify; }
pre { background: #f4f4f4; padding: 0.8em; border-radius: 4px; font-size: 0.85em; overflow-x: auto; white-space: pre-wrap; }
code { background: #f4f4f4; padding: 0.1em 0.3em; border-radius: 3px; font-size: 0.9em; }
blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 1em; color: #555; }
img { max-width: 100%; height: auto; display: block; margin: 1em auto; }
ul, ol { margin: 0.5em 0; }
table { border-collapse: collapse; margin: 1em 0; font-size: 0.9em; }
th, td { border: 1px solid #ccc; padding: 0.4em 0.6em; }
th { background: #eee; }
strong { font-weight: bold; }
em { font-style: italic; }
a { color: #2266cc; }
sup { font-size: 0.75em; }
.footnote { font-size: 0.85em; color: #555; margin-top: 1em; }
"""

css = epub.EpubItem(uid="style", file_name="style/default.css", media_type="text/css", content=style)
book.add_item(css)

# Add all images
img_dir = os.path.join(book_dir, "images")
img_map = {}
if os.path.isdir(img_dir):
    for fname in sorted(os.listdir(img_dir)):
        fpath = os.path.join(img_dir, fname)
        if not os.path.isfile(fpath):
            continue
        ext = fname.rsplit(".", 1)[-1].lower()
        mime = {"svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif"}.get(ext, "application/octet-stream")
        with open(fpath, "rb") as f:
            img_data = f.read()
        img_item = epub.EpubItem(uid=f"img_{fname}", file_name=f"images/{fname}", media_type=mime, content=img_data)
        book.add_item(img_item)
        img_map[fname] = f"images/{fname}"
    print(f"✅ {len(img_map)} kép beágyazva")

# Convert and add each chapter
epub_chapters = []
toc_entries = []
spine_entries = ["nav"]

for fname, title, fpath in existing:
    with open(fpath, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert markdown to HTML
    md_extras = ["extra", "codehilite", "tables", "fenced_code"]
    html_body = markdown.markdown(md_content, extensions=md_extras)

    # Fix image paths
    for old_name, new_path in img_map.items():
        html_body = html_body.replace(f'src="images/{old_name}"', f'src="{new_path}"')

    # Create chapter
    safe_name = fname.replace(".md", ".xhtml")
    chapter = epub.EpubHtml(title=title, file_name=safe_name, lang="hu")
    chapter.set_content(f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="hu">
<head><title>{title}</title>
<link rel="stylesheet" type="text/css" href="style/default.css"/>
</head>
<body>
{html_body}
</body>
</html>""".encode('utf-8'))
    book.add_item(chapter)
    epub_chapters.append(chapter)
    toc_entries.append(epub.Link(safe_name, title, fname.replace(".md", "")))
    spine_entries.append(chapter)

# Table of contents
book.toc = toc_entries

# Add navigation files
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# Define spine
book.spine = spine_entries

# Output
out_path = os.path.join(book_dir, "AI-Agent-Book_HU.epub")
epub.write_epub(out_path, book, {})
size_kb = os.path.getsize(out_path) / 1024
print(f"✅ EPUB elkészült: {out_path}")
print(f"   Méret: {size_kb:.0f} KB")
print(f"   Fejezetek: {len(existing)}")
