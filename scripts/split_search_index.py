#!/usr/bin/env python3
"""Split Material's monolithic search index into one file per book edition.

MkDocs' search plugin emits a single ``search/search_index.json`` covering
every page in the build. This site ships all 14 book editions plus the ~94
companion-experiment pages from one build, so that file had grown to ~55 MB:
every reader who opens search downloads the full prose of 13 editions they
cannot read.

This hook rewrites the search plugin's output into:

* ``search/search_index.json`` — the default edition plus shared pages, kept
  at the canonical name so any client that does not run the router (or a
  stale cached page) still gets a working index; and
* ``search/search_index.<slug>.json`` — one file per edition, where ``slug``
  is the edition's URL directory (``book``, ``book-en``, ``book-ta``, ...).

Every file also carries the *shared* pages — the language-agnostic experiment
pages under ``chapterN/`` and the site root — so searching from any edition
still reaches the companion experiments, exactly as it does today.

``extras/search-index-router.js`` selects the matching file in the browser.
The two sides must agree on how a URL maps to an edition slug; see
``edition_of()`` here and ``slugForPath()`` there.

Ordering: MkDocs appends ``hooks:`` entries to the plugin list
(``config_options.Hooks.post_validation``), so this ``on_post_build`` runs
after the search plugin has written the index it consumes.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

log = logging.getLogger("mkdocs.hooks.split_search_index")

# `chapterN/README.<readmeSuffix>/` — the per-language experiment index pages.
# They live outside the book-*/ tree but belong to a specific edition.
README_RE = re.compile(r"^chapter\d+/README\.([A-Za-z-]+)/")
# `index.<code>/` — translated homepages (e.g. index.ko.md -> index.ko/).
HOMEPAGE_RE = re.compile(r"^index\.([A-Za-z-]+)/")

SHARED = "__shared__"


def _edition_tables(config: Any) -> tuple[list[tuple[str, str]], dict[str, str]]:
    """Return (prefix table, suffix->slug map) derived from `extra.languages`.

    The prefix table is sorted longest-first so `book-en/` wins over `book/`
    when both would match.
    """
    languages = (config.get("extra") or {}).get("languages") or {}

    prefixes: list[tuple[str, str]] = []
    suffixes: dict[str, str] = {}
    for code, entry in languages.items():
        prefix = (entry or {}).get("prefix")
        if not prefix:
            continue
        slug = prefix.rstrip("/")
        prefixes.append((prefix, slug))
        # `readmeSuffix` keys the experiment index pages; the default edition
        # has none (its pages are `chapterN/README/`, which stay shared).
        readme_suffix = (entry or {}).get("readmeSuffix")
        if readme_suffix:
            suffixes[readme_suffix] = slug
        # Translated homepages are keyed by the language code itself.
        suffixes.setdefault(code, slug)

    prefixes.sort(key=lambda pair: len(pair[0]), reverse=True)
    return prefixes, suffixes


def edition_of(location: str, prefixes: list[tuple[str, str]], suffixes: dict[str, str]) -> str:
    """Map a search-index location to an edition slug, or SHARED.

    Mirrors `slugForPath()` in extras/search-index-router.js.
    """
    for prefix, slug in prefixes:
        if location.startswith(prefix):
            return slug

    match = README_RE.match(location) or HOMEPAGE_RE.match(location)
    if match:
        slug = suffixes.get(match.group(1))
        if slug:
            return slug

    return SHARED


def _default_slug(config: Any) -> str:
    languages = (config.get("extra") or {}).get("languages") or {}
    for entry in languages.values():
        if (entry or {}).get("default") and (entry or {}).get("prefix"):
            return entry["prefix"].rstrip("/")
    return "book"


def on_post_build(config: Any, **_: Any) -> None:
    index_path = Path(config["site_dir"]) / "search" / "search_index.json"
    if not index_path.exists():
        # `search_index_only` themes or a disabled search plugin.
        log.debug("no search index at %s; nothing to split", index_path)
        return

    data = json.loads(index_path.read_text(encoding="utf-8"))
    docs = data.get("docs")
    if not isinstance(docs, list):
        log.warning("unexpected search index shape; leaving it untouched")
        return

    prefixes, suffixes = _edition_tables(config)
    if not prefixes:
        log.warning("no `extra.languages` prefixes; leaving the index untouched")
        return

    buckets: dict[str, list[dict]] = {}
    for doc in docs:
        buckets.setdefault(edition_of(doc.get("location", ""), prefixes, suffixes), []).append(doc)

    shared = buckets.pop(SHARED, [])
    if not buckets:
        log.warning("no edition pages found in the search index; leaving it untouched")
        return

    def write(path: Path, entries: list[dict]) -> int:
        payload = dict(data)
        payload["docs"] = entries
        # `separators` matches what the search plugin emits; keeping the file
        # compact matters more here than diffability (it is build output).
        blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        path.write_text(blob, encoding="utf-8")
        return len(blob.encode("utf-8"))

    total_before = index_path.stat().st_size
    written = []
    for slug, entries in sorted(buckets.items()):
        size = write(index_path.with_name(f"search_index.{slug}.json"), shared + entries)
        written.append((slug, len(entries), size))

    # The canonical filename keeps serving the default edition, so a client
    # that never runs the router degrades to today's behaviour for that
    # edition instead of losing search entirely.
    default_slug = _default_slug(config)
    default_docs = buckets.get(default_slug, [])
    default_size = write(index_path, shared + default_docs)

    log.info(
        "split search index: %.1f MB -> %d per-edition files of %.1f-%.1f MB "
        "(%d shared docs in each; default `%s` kept at search_index.json, %.1f MB)",
        total_before / 1e6,
        len(written),
        min(size for _, _, size in written) / 1e6,
        max(size for _, _, size in written) / 1e6,
        len(shared),
        default_slug,
        default_size / 1e6,
    )
