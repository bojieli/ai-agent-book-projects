"""Tests for scripts/split_search_index.py (the per-edition search index hook)."""

import importlib.util
import json
from pathlib import Path

import pytest


def _load_hook():
    path = Path(__file__).parents[1] / "scripts" / "split_search_index.py"
    spec = importlib.util.spec_from_file_location("split_search_index", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hook = _load_hook()


# A trimmed copy of mkdocs.yml's `extra.languages`, covering each shape that
# matters: the default edition, an edition with a `readmeSuffix` that differs
# from its code (zh-TW), and plain editions.
LANGUAGES = {
    "zh": {"label": "中文", "prefix": "book/", "default": True},
    "zhtw": {"label": "繁體中文", "prefix": "book-zhtw/", "readmeSuffix": "zh-TW"},
    "en": {"label": "English", "prefix": "book-en/", "readmeSuffix": "en"},
    "ta": {"label": "தமிழ்", "prefix": "book-ta/", "readmeSuffix": "ta"},
    "ko": {"label": "한국어", "prefix": "book-ko/", "readmeSuffix": "ko"},
    "he": {"label": "עברית", "prefix": "book-he/", "suffix": ".he"},
}

CONFIG = {"extra": {"languages": LANGUAGES}}


@pytest.mark.parametrize(
    "location, expected",
    [
        # Chapter prose lives under the edition's own directory.
        ("book/chapter1/", "book"),
        ("book-en/chapter1/#the-agent-loop", "book-en"),
        # `book-*` must win over the default `book/` prefix.
        ("book-zhtw/chapter2/", "book-zhtw"),
        # Per-language experiment indexes live outside the book-*/ tree.
        ("chapter1/README.en/", "book-en"),
        ("chapter7/README.zh-TW/#setup", "book-zhtw"),
        ("chapter3/README.ta/", "book-ta"),
        # Translated homepages carry their locale in the slug.
        ("index.ko/", "book-ko"),
        ("book-he/chapter1.he/", "book-he"),
        ("index.he/", "book-he"),
        # Language-agnostic pages stay shared.
        ("chapter6/agent-loop/", hook.SHARED),
        ("chapter1/README/", hook.SHARED),
        ("", hook.SHARED),
        # An unknown suffix must not be guessed into an edition.
        ("chapter1/README.pl/", hook.SHARED),
    ],
)
def test_edition_of(location, expected):
    prefixes, suffixes = hook._edition_tables(CONFIG)
    assert hook.edition_of(location, prefixes, suffixes) == expected


def test_default_slug():
    assert hook._default_slug(CONFIG) == "book"


def _write_index(site: Path, locations):
    search = site / "search"
    search.mkdir(parents=True)
    payload = {
        "config": {"lang": ["zh"]},
        "docs": [{"location": loc, "title": loc, "text": f"body {loc}"} for loc in locations],
    }
    (search / "search_index.json").write_text(json.dumps(payload), encoding="utf-8")
    return search


def test_on_post_build_splits_by_edition(tmp_path):
    site = tmp_path / "site"
    search = _write_index(
        site,
        [
            "",                      # shared: site root
            "chapter6/agent-loop/",  # shared: experiment page
            "book/chapter1/",
            "book-en/chapter1/",
            "chapter1/README.en/",
            "book-ta/chapter1/",
            "index.ko/",
            "book-he/chapter1.he/",
            "index.he/",
        ],
    )

    hook.on_post_build({"site_dir": str(site), **CONFIG})

    def locations(name):
        data = json.loads((search / name).read_text(encoding="utf-8"))
        return sorted(doc["location"] for doc in data["docs"])

    shared = ["", "chapter6/agent-loop/"]
    # Every edition keeps the shared pages so the companion experiments stay
    # searchable from any edition.
    assert locations("search_index.book-en.json") == sorted(
        shared + ["book-en/chapter1/", "chapter1/README.en/"]
    )
    assert locations("search_index.book-ta.json") == sorted(shared + ["book-ta/chapter1/"])
    assert locations("search_index.book-ko.json") == sorted(shared + ["index.ko/"])
    assert locations("search_index.book-he.json") == sorted(
        shared + ["book-he/chapter1.he/", "index.he/"]
    )
    # The canonical filename keeps serving the default edition, so a client
    # that never runs the router still gets a working index.
    assert locations("search_index.json") == sorted(shared + ["book/chapter1/"])
    assert locations("search_index.book.json") == sorted(shared + ["book/chapter1/"])

    # No edition may leak another edition's prose.
    assert "book-ta/chapter1/" not in locations("search_index.book-en.json")

    # The `config` block the search worker needs must survive the split.
    data = json.loads((search / "search_index.book-en.json").read_text(encoding="utf-8"))
    assert data["config"] == {"lang": ["zh"]}


def test_on_post_build_is_a_noop_without_an_index(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    hook.on_post_build({"site_dir": str(site), **CONFIG})
    assert not (site / "search").exists()


def test_on_post_build_leaves_index_alone_without_edition_pages(tmp_path):
    """A build with no book editions (e.g. a docs-only preview) must not lose search."""
    site = tmp_path / "site"
    search = _write_index(site, ["", "chapter6/agent-loop/"])
    before = (search / "search_index.json").read_text(encoding="utf-8")

    hook.on_post_build({"site_dir": str(site), **CONFIG})

    assert (search / "search_index.json").read_text(encoding="utf-8") == before
    assert list(search.glob("search_index.*.json")) == []
