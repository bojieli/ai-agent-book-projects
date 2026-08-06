#!/usr/bin/env python3
"""Keep reader-facing site assets and JSON files linked from rendered Markdown."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import markdown

ALWAYS_PUBLISHED_SUFFIXES = {
    ".css",
    ".jpeg",
    ".jpg",
    ".js",
    ".md",
    ".png",
    ".svg",
    ".txt",
}


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attribute = (
            "src"
            if tag in ("img", "script", "iframe", "source", "embed", "audio", "video")
            else "href"
            if tag in ("a", "link")
            else None
        )
        if attribute is None:
            return
        values = dict(attrs)
        if values.get(attribute):
            self.targets.append(values[attribute] or "")


def rendered_links(text: str) -> list[str]:
    collector = LinkCollector()
    collector.feed(markdown.markdown(text, extensions=["fenced_code"]))
    return collector.targets


def safe_regular_file(path: Path, root: Path) -> Path | None:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, RuntimeError, ValueError):
        return None
    return resolved if resolved.is_file() else None


def linked_json_files(root: Path) -> set[Path]:
    linked: set[Path] = set()
    for source in root.rglob("*.md"):
        markdown_file = safe_regular_file(source, root)
        if markdown_file is None:
            continue
        text = markdown_file.read_text(encoding="utf-8", errors="replace")
        for target in rendered_links(text):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue
            decoded = unquote(parsed.path)
            if not decoded.lower().endswith(".json"):
                continue
            candidate = root / decoded.lstrip("/") if decoded.startswith("/") else source.parent / decoded
            resolved = safe_regular_file(candidate, root)
            if resolved is not None:
                linked.add(resolved)
    return linked


def clean(root: Path) -> None:
    root = root.resolve(strict=True)
    keep_json = linked_json_files(root)
    for path in root.rglob("*"):
        if not (path.is_file() or path.is_symlink()):
            continue
        resolved = safe_regular_file(path, root)
        keep_regular_asset = resolved is not None and path.suffix.lower() in ALWAYS_PUBLISHED_SUFFIXES
        if keep_regular_asset or resolved in keep_json:
            continue
        path.unlink()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: clean_site_files.py DEST")
    clean(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
