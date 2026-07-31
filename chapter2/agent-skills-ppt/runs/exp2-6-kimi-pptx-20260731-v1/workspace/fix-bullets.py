#!/usr/bin/env python3
"""Post-process deck: remove duplicate mid-paragraph <a:pPr> elements that
pptxgenjs emits when list items contain multiple inline-formatting runs.
The duplicate (later) pPr carries buNone, which makes LibreOffice drop the
bullet glyph. Keeping only the first pPr per <a:p> restores uniform bullets."""
import re, glob, sys

pattern = re.compile(r'(</a:r>)\s*<a:pPr\b.*?</a:pPr>', re.S)
total = 0
for path in glob.glob('deckbuild/ppt/slides/slide*.xml'):
    xml = open(path, encoding='utf-8').read()
    fixed, n = pattern.subn(r'\1', xml)
    if n:
        open(path, 'w', encoding='utf-8').write(fixed)
        total += n
        print(f'{path}: removed {n} duplicate pPr')
print(f'total removed: {total}')
