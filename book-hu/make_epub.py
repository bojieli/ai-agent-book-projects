#! /usr/bin/env python3
"""Generate EPUB from the Hungarian introduction.md - simpler approach"""

import os
import re
from ebooklib import epub, ITEM_IMAGE
import markdown

book_dir = os.path.dirname(os.path.abspath(__file__))

# Read the markdown
md_path = os.path.join(book_dir, "introduction.md")
with open(md_path, "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert markdown to HTML
md_extras = ["extra", "codehilite", "tables", "fenced_code"]
html_body = markdown.markdown(md_content, extensions=md_extras)

# Create EPUB book
book = epub.EpubBook()

# Metadata
book.set_identifier("ai-agent-intro-hu-001")
book.set_title("AI Agent – Bevezetés (magyar)")
book.set_language("hu")
book.add_author("Li Bojie")
book.add_metadata("DC", "description", "A Bevezetés fejezet magyar fordítása az 'AI Agent: Tervezési elvek és gyakorlat' című könyvből.")

# CSS
style = """
body { font-family: 'Liberation Serif', Georgia, serif; line-height: 1.6; margin: 1em; }
h1, h2, h3, h4 { font-family: 'Liberation Sans', Arial, sans-serif; }
h1 { font-size: 1.6em; margin-top: 1.5em; }
h2 { font-size: 1.3em; margin-top: 1.2em; }
h3 { font-size: 1.1em; margin-top: 1em; }
p { margin: 0.5em 0; text-align: justify; }
pre { background: #f4f4f4; padding: 0.8em; border-radius: 4px; font-size: 0.85em; overflow-x: auto; white-space: pre-wrap; }
code { background: #f4f4f4; padding: 0.1em 0.3em; border-radius: 3px; font-size: 0.9em; }
blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 1em; color: #555; }
img { max-width: 100%; height: auto; display: block; margin: 1em auto; }
ul, ol { margin: 0.5em 0; }
strong { font-weight: bold; }
em { font-style: italic; }
"""

css = epub.EpubItem(uid="style", file_name="style/default.css", media_type="text/css", content=style)
book.add_item(css)

# Add images as EPUB items
img_dir = os.path.join(book_dir, "images")
img_map = {}
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

# Fix image paths in HTML
for old_name, new_path in img_map.items():
    html_body = html_body.replace(f'src="images/{old_name}"', f'src="{new_path}"')

# Create chapter
chapter = epub.EpubHtml(title="Bevezetés", file_name="introduction.xhtml", lang="hu")
chapter.set_content(f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="hu">
<head><title>Bevezetés</title>
<link rel="stylesheet" type="text/css" href="style/default.css"/>
</head>
<body>
{html_body}
</body>
</html>""".encode('utf-8'))
book.add_item(chapter)

# Table of contents
book.toc = [epub.Link("introduction.xhtml", "Bevezetés", "intro")]

# Add navigation files
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# Define spine
book.spine = ["nav", chapter]

# Output
out_path = os.path.join(book_dir, "AI-Agent-Book_Bevezetes.epub")
epub.write_epub(out_path, book, {})
print(f"✅ EPUB created: {out_path}")
print(f"   Size: {os.path.getsize(out_path):,} bytes")
