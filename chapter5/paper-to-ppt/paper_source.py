"""Pinned real-paper preparation for Experiment 5-4.

The canonical campaign uses the published PDF, extracts its text directly, and
renders three original paper figures from declared PDF page rectangles.  The
resulting manifest makes it possible to prove that the images in the Slidev
deck came from the source PDF rather than from programmatic stand-ins.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

import fitz
from PIL import Image


PAPER = {
    "title": "Attention Is All You Need",
    "authors": "Ashish Vaswani et al.",
    "arxiv_id": "1706.03762",
    "pdf_url": "https://arxiv.org/pdf/1706.03762",
    "pdf_sha256": "bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697",
}

# Coordinates are in PDF points and were registered against the pinned PDF.
# They isolate the published figure itself (rather than surrounding body text)
# so labels remain legible after a 16:9 slide render. Provenance does not rely
# on pixels from the caption: the manifest records the source page, crop
# rectangle, published figure label/caption, PDF hash, and extracted hash.
VISUALS = [
    {
        "filename": "paper_figure_1_transformer.png",
        "pdf_page": 3,
        "source_label": "Figure 1",
        "caption": "The Transformer model architecture.",
        "rect": [92, 60, 520, 405],
        "rotation_degrees": 0,
    },
    {
        "filename": "paper_figure_3_long_distance.png",
        "pdf_page": 13,
        "source_label": "Figure 3 (long-distance dependency focus)",
        "caption": "Published encoder attention linking 'making' to 'more difficult'.",
        "rect": [190, 88, 425, 311],
        "rotation_degrees": 90,
    },
    {
        "filename": "paper_figure_4_anaphora.png",
        "pdf_page": 14,
        "source_label": "Figure 4 (lower panel, anaphora focus)",
        "caption": "Published attention from 'its' to 'Law' and 'application'.",
        "rect": [92, 360, 310, 610],
        "rotation_degrees": 90,
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "ai-agent-book/5-4"})
    with urllib.request.urlopen(request, timeout=120) as response:
        destination.write_bytes(response.read())


def prepare_real_paper(run_dir: str | Path, public_dir: str | Path) -> dict:
    run_dir = Path(run_dir)
    public_dir = Path(public_dir)
    source_dir = run_dir / "source"
    visual_dir = source_dir / "source_visuals"
    source_dir.mkdir(parents=True, exist_ok=True)
    visual_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = source_dir / "1706.03762.pdf"
    if not pdf_path.exists():
        _download(PAPER["pdf_url"], pdf_path)
    observed_pdf_hash = sha256(pdf_path)
    if observed_pdf_hash != PAPER["pdf_sha256"]:
        raise ValueError(
            f"source PDF hash mismatch: expected {PAPER['pdf_sha256']}, "
            f"observed {observed_pdf_hash}"
        )

    document = fitz.open(pdf_path)
    page_text = []
    for page_index, page in enumerate(document):
        page_text.append(f"\n\n## PDF page {page_index + 1}\n\n{page.get_text('text')}")
    text_path = source_dir / "paper_text.md"
    text_path.write_text(
        f"# {PAPER['title']}\n\nAuthors: {PAPER['authors']}\n" + "".join(page_text),
        encoding="utf-8",
    )

    manifest_rows = []
    figure_descriptions = {}
    for visual in VISUALS:
        page = document[visual["pdf_page"] - 1]
        rect = fitz.Rect(visual["rect"])
        if not page.rect.contains(rect):
            raise ValueError(f"visual crop is outside page bounds: {visual}")
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=rect, alpha=False)
        extracted_path = visual_dir / visual["filename"]
        pixmap.save(extracted_path)
        if visual.get("rotation_degrees"):
            # The published attention labels run vertically. A lossless
            # quarter-turn makes those original pixels audience-readable on a
            # landscape slide; the transform is explicit in the manifest.
            with Image.open(extracted_path) as source_image:
                rotated = source_image.rotate(
                    -int(visual["rotation_degrees"]), expand=True
                )
                rotated.save(extracted_path)
        public_path = public_dir / visual["filename"]
        shutil.copyfile(extracted_path, public_path)
        row = {
            **visual,
            "sha256": sha256(extracted_path),
            "bytes": extracted_path.stat().st_size,
            "public_copy_sha256": sha256(public_path),
        }
        manifest_rows.append(row)
        figure_descriptions[visual["filename"]] = (
            f"{visual['source_label']} from PDF page {visual['pdf_page']}: "
            f"{visual['caption']}"
        )
    document.close()

    manifest = {
        "paper": {**PAPER, "observed_pdf_sha256": observed_pdf_hash},
        "paper_text": {
            "path": str(text_path),
            "sha256": sha256(text_path),
            "characters": len(text_path.read_text(encoding="utf-8")),
        },
        "visuals": manifest_rows,
    }
    manifest_path = visual_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "paper_text": text_path.read_text(encoding="utf-8"),
        "figures": figure_descriptions,
        "manifest": manifest,
        "manifest_path": str(manifest_path),
        "pdf_path": str(pdf_path),
    }
