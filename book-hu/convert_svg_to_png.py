#! /usr/bin/env python3
"""Convert all SVG images to PNG for better e-book reader compatibility"""

import os
import re

book_dir = os.path.dirname(os.path.abspath(__file__))
img_dir = os.path.join(book_dir, "images")

# Convert SVG files to PNG
import cairosvg

converted = 0
for fname in sorted(os.listdir(img_dir)):
    if not fname.lower().endswith('.svg'):
        continue

    svg_path = os.path.join(img_dir, fname)
    png_name = fname.replace('.svg', '.png')
    png_path = os.path.join(img_dir, png_name)

    with open(svg_path, 'rb') as f:
        svg_data = f.read()

    # Convert SVG to PNG
    cairosvg.svg2png(bytestring=svg_data, write_to=png_path, output_width=1200)
    converted += 1
    if converted % 20 == 0:
        print(f"  {converted} SVG konvertálva...")

print(f"✅ {converted} SVG → PNG konvertálva")

# Now update all chapter files to use .png instead of .svg
chapters = [
    "introduction.md", "chapter1.md", "chapter2.md", "chapter3.md",
    "chapter4.md", "chapter5.md", "chapter6.md", "chapter7.md",
    "chapter8.md", "chapter9.md", "chapter10.md", "afterword.md",
    "reference-answers.md"
]

total_fixes = 0
for fname in chapters:
    fpath = os.path.join(book_dir, fname)
    if not os.path.exists(fpath):
        continue

    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace image references: images/fig*.svg → images/fig*.png
    new_content = re.sub(r'(images/[a-zA-Z0-9_-]+)\.svg', r'\1.png', content)

    if new_content != content:
        fixes = len(re.findall(r'\.png', new_content)) - len(re.findall(r'\.png', content))
        total_fixes += fixes
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  {fname}: {fixes} SVG hivatkozás → PNG")

print(f"\n✅ Összesen {total_fixes} hivatkozás frissítve")
