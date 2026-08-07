"""Regression tests for Git dates in the assembled online-reading site."""

import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from site_source_paths import (  # noqa: E402
    git_commit_range,
    original_source_map,
    source_path_for_page,
)


def test_regular_page_maps_to_same_repository_path(tmp_path: Path):
    source = tmp_path / "book-en" / "chapter1.md"
    source.parent.mkdir(parents=True)
    source.touch()

    assert source_path_for_page("book-en/chapter1.md", tmp_path) == source


def test_promoted_chapter_index_maps_back_to_chapter_source(tmp_path: Path):
    source = tmp_path / "book" / "chapter10.md"
    source.parent.mkdir(parents=True)
    source.touch()

    assert source_path_for_page("book/chapter10/index.md", tmp_path) == source
def test_source_path_for_page_strips_leading_slashes(tmp_path: Path):
    """Contract: Leading slashes in page URIs must be normalized to relative repository paths.

    If a page URI carries a leading slash (e.g. /book/chapter1/index.md), source_path_for_page
    must strip it so path joining resolves under root instead of filesystem root /.
    """
    source = tmp_path / "book" / "chapter1.md"
    source.parent.mkdir(parents=True)
    source.touch()

    assert source_path_for_page("/book/chapter1/index.md", tmp_path) == source


def test_original_source_map_uses_tracked_sources_and_skips_missing_files(tmp_path: Path):
    chapter = tmp_path / "book" / "chapter1.md"
    readme = tmp_path / "chapter1" / "README.md"
    chapter.parent.mkdir(parents=True)
    readme.parent.mkdir(parents=True)
    chapter.touch()
    readme.touch()

    files = [
        SimpleNamespace(
            src_uri="book/chapter1/index.md",
            abs_src_path="/staging/book/chapter1/index.md",
        ),
        SimpleNamespace(
            src_uri="chapter1/README.md",
            abs_src_path="/staging/chapter1/README.md",
        ),
        SimpleNamespace(
            src_uri="generated/missing.md",
            abs_src_path="/staging/generated/missing.md",
        ),
    ]

    assert original_source_map(files, tmp_path) == {
        "/staging/book/chapter1/index.md": str(chapter),
        "/staging/chapter1/README.md": str(readme),
    }


def test_git_commit_range_returns_distinct_creation_and_update_dates(tmp_path: Path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
        check=True,
    )

    page = tmp_path / "page.md"
    page.write_text("created\n", encoding="utf-8")
    _commit(tmp_path, "create", "1704067200 +0000")
    page.write_text("updated\n", encoding="utf-8")
    _commit(tmp_path, "update", "1706745600 +0000")

    latest, created = git_commit_range(page, tmp_path)

    assert latest[1] == 1706745600
    assert created[1] == 1704067200
    assert latest[0] != created[0]

def test_git_commit_range_ignores_commits_for_creation_date(tmp_path: Path):
    """Verify git_commit_range filters ignored_commits when determining creation date.

    Contract: If the initial creation commit of a file matches an ignored commit hash,
    git_commit_range must ignore it and return the earliest non-ignored commit date.
    Locks out returning an ignored commit as the file creation date.
    """
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
        check=True,
    )

    page = tmp_path / "page.md"
    page.write_text("created\n", encoding="utf-8")
    _commit(tmp_path, "create", "1704067200 +0000")

    creation_hash = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    page.write_text("updated\n", encoding="utf-8")
    _commit(tmp_path, "update", "1706745600 +0000")

    latest_hash = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    latest, created = git_commit_range(
        page, tmp_path, ignored_commits=(creation_hash,)
    )

    assert created[0] == latest_hash
    assert created[0] != creation_hash
    assert created[1] == 1706745600

def test_git_commit_range_handles_all_ignored_commits(tmp_path: Path):
    """Contract: If all commits for a file are ignored, git_commit_range must return fallback commit."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
        check=True,
    )

    page = tmp_path / "page.md"
    page.write_text("created\n", encoding="utf-8")
    _commit(tmp_path, "create", "1704067200 +0000")

    commit_hash = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    latest, created = git_commit_range(
        page, tmp_path, ignored_commits=(commit_hash,)
    )

    assert latest[0] == ""
    assert created[0] == ""
def _commit(repository: Path, message: str, date: str) -> None:
    subprocess.run(["git", "-C", str(repository), "add", "page.md"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-qm", message],
        check=True,
        env={
            **os.environ,
            "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_DATE": date,
        },
    )
