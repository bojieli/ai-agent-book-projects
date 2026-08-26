"""Regression tests for the source links in the assembled online-reading site.

Issue #1019: the "edit this page" and "view source" buttons on every chapter
page pointed at `book/chapterN/index.md`, a path that only exists inside the
generated `_web/` tree, so both buttons 404'd on GitHub.
"""

from pathlib import Path
import sys

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File
from mkdocs.structure.pages import Page


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import site_edit_urls  # noqa: E402
from site_source_paths import repo_relative_source  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]


def _config(tmp_path: Path) -> MkDocsConfig:
    config = MkDocsConfig()
    config.load_dict(
        {
            "site_name": "test",
            "docs_dir": str(tmp_path),
            "repo_url": "https://github.com/bojieli/ai-agent-book",
            "edit_uri": "edit/main",
        }
    )
    assert not config.validate()[0]
    return config


def _page(src_uri: str, tmp_path: Path) -> Page:
    staged = tmp_path / src_uri
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.touch()
    config = _config(tmp_path)
    file = File(src_uri, str(tmp_path), str(tmp_path / "_site"), use_directory_urls=True)
    site_edit_urls.on_files([file], config)
    return Page(None, file, config)


def test_promoted_chapter_page_links_to_the_tracked_chapter_source(tmp_path: Path):
    page = _page("book/chapter9/index.md", tmp_path)

    assert page.edit_url == (
        "https://github.com/bojieli/ai-agent-book/edit/main/book/chapter9.md"
    )
    # Material derives the "view source" button from the same URL.
    assert page.edit_url.replace("edit", "raw") == (
        "https://github.com/bojieli/ai-agent-book/raw/main/book/chapter9.md"
    )


def test_regular_page_keeps_its_own_path(tmp_path: Path):
    page = _page("book-en/chapter9.md", tmp_path)

    assert page.edit_url == (
        "https://github.com/bojieli/ai-agent-book/edit/main/book-en/chapter9.md"
    )


def test_page_without_a_repository_source_gets_no_buttons(tmp_path: Path):
    page = _page("generated/nowhere.md", tmp_path)

    assert page.edit_url is None


def test_every_promoted_chapter_resolves_to_a_real_source():
    for chapter in range(1, 11):
        assert repo_relative_source(f"book/chapter{chapter}/index.md") == (
            f"book/chapter{chapter}.md"
        )
