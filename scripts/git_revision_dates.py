"""Use tracked source files for revision dates in the assembled MkDocs site.

``scripts/build_site.sh`` copies documentation into the ignored ``_web/``
directory before MkDocs runs.  The git revision-date plugin would otherwise
query those generated paths, find no history, and give every page the build
time.  This hook primes the plugin's timestamp cache with the corresponding
tracked source paths before the plugin's own ``on_files`` handler runs.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
from typing import Any, Iterable

from mkdocs.plugins import event_priority

from site_source_paths import REPO_ROOT, git_commit_range, original_source_map

_PLUGIN_NAME = "git-revision-date-localized"


@event_priority(100)
def on_files(files: Iterable[Any], config: Any, **_: Any) -> None:
    """Populate the revision plugin's caches before its default-priority hook."""
    plugin = config.plugins.get(_PLUGIN_NAME)
    if plugin is None:
        return

    sources = original_source_map(files)
    tracked = _tracked_paths()
    jobs = [
        (staged, source)
        for staged, source in sources.items()
        if _relative_source(source) in tracked
    ]

    ignored = tuple(getattr(plugin.util, "ignored_commits", ()))
    follow = bool(plugin.config.get("enable_git_follow"))
    include_creation = bool(plugin.config.get("enable_creation_date"))

    def read_dates(job: tuple[str, str]):
        staged, source = job
        dates = git_commit_range(
            Path(source),
            ignored_commits=ignored,
            follow=follow,
            include_creation=include_creation,
        )
        return staged, dates

    plugin.last_revision_commits.clear()
    plugin.created_commits.clear()

    # Cache under the staged path because that is the key the plugin looks up
    # while rendering. Doing this at priority 100 also makes its default
    # on_files handler see a populated cache and skip querying `_web/` itself.
    with ThreadPoolExecutor(max_workers=10) as executor:
        for staged, (latest, created) in executor.map(read_dates, jobs):
            plugin.last_revision_commits[staged] = latest
            if include_creation:
                plugin.created_commits[staged] = created


def _relative_source(source: str) -> str:
    return Path(source).resolve().relative_to(REPO_ROOT).as_posix()


def _tracked_paths() -> set[str]:
    output = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    ).stdout
    return {path.decode() for path in output.split(b"\0") if path}
