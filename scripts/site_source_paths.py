"""Map pages in the generated MkDocs tree to their repository sources."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import subprocess
import time
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
Commit = tuple[str, int]


def source_path_for_page(src_uri: str, root: Path = REPO_ROOT) -> Path:
    """Return the tracked source represented by an assembled page URI."""
    relative = PurePosixPath(src_uri)
    parts = [p for p in relative.parts if p != "/"]

    # build_site.sh promotes book/chapterN.md to book/chapterN/index.md so
    # navigation.indexes can make the chapter section itself clickable.
    if (
        len(parts) == 3
        and parts[0] == "book"
        and parts[1].startswith("chapter")
        and parts[1][7:].isdigit()
        and parts[2] == "index.md"
    ):
        return root / "book" / f"{parts[1]}.md"

    return root.joinpath(*parts)


def original_source_map(files: Iterable[Any], root: Path = REPO_ROOT) -> dict[str, str]:
    """Map staged absolute paths to existing source files in the repository."""
    sources: dict[str, str] = {}
    for file in files:
        abs_src_path = getattr(file, "abs_src_path", None)
        src_uri = getattr(file, "src_uri", None)
        if not abs_src_path or not src_uri:
            continue

        source = source_path_for_page(str(src_uri), root)
        if source.is_file():
            sources[str(abs_src_path)] = str(source)
    return sources


def git_commit_range(
    source: Path,
    root: Path = REPO_ROOT,
    *,
    ignored_commits: tuple[str, ...] = (),
    follow: bool = False,
    include_creation: bool = True,
) -> tuple[Commit, Commit]:
    """Return the latest and creation commits for one tracked source file."""
    relative = source.resolve().relative_to(root.resolve()).as_posix()
    common = ["git", "-C", str(root), "log", "--format=%H%x00%at"]
    if follow:
        common.append("--follow")

    latest_lines = _git_log(common + [f"-n{len(ignored_commits) + 1}", "--", relative])
    latest = next(
        (
            commit
            for commit in map(_parse_commit, latest_lines)
            if not any(commit[0].startswith(prefix) for prefix in ignored_commits)
        ),
        _fallback_commit(),
    )

    if not include_creation:
        return latest, latest

    creation_lines = _git_log(common + ["--diff-filter=A", "--", relative])
    valid_creation_commits = [
        commit
        for commit in map(_parse_commit, creation_lines)
        if not any(commit[0].startswith(prefix) for prefix in ignored_commits)
    ]
    created = valid_creation_commits[-1] if valid_creation_commits else latest
    return latest, created


def _git_log(command: list[str]) -> list[str]:
    output = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line for line in output.splitlines() if line]


def _parse_commit(line: str) -> Commit:
    commit_hash, timestamp = line.split("\0", 1)
    return commit_hash, int(timestamp)


def _fallback_commit() -> Commit:
    return "", int(time.time())
