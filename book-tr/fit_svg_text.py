"""Repair text overflow in generated/static book SVGs (in place).

Most figures under images/ are produced by the gen_chN_figs.py scripts (which
now self-correct via svg_lib.SVG.render), but several sets — fig0-*, fig6-*,
fig7-*, the multimodal fig9-*, and fig10-* — are static SVGs with no live
generator. This tool applies the same width model (svg_lib.fit_overflow) to any
SVG on disk, shrinking only the font-size of text runs that spill outside their
containing rectangle or the canvas. It is safe (positions are never moved) and
idempotent (re-running makes no further changes).

Usage:
    python3 fit_svg_text.py                 # fix every images/*.svg
    python3 fit_svg_text.py images/fig6-3.svg ...   # fix specific files
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svg_lib import fit_overflow

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')


def process(path):
    with open(path, encoding='utf-8') as f:
        original = f.read()
    fixed = fit_overflow(original)
    if fixed != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fixed)
        return True
    return False


def main(argv):
    targets = argv[1:] or sorted(glob.glob(os.path.join(IMG, '*.svg')))
    changed = 0
    for path in targets:
        if process(path):
            changed += 1
            print(f'  fitted {os.path.basename(path)}')
    print(f'\nAdjusted {changed}/{len(targets)} SVG file(s).')


if __name__ == '__main__':
    main(sys.argv)
