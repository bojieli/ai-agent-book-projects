"""Point the "edit this page" / "view source" buttons at the tracked source.

``scripts/build_site.sh`` assembles the site into the ignored ``_web/``
directory, and promotes ``book/chapterN.md`` to ``book/chapterN/index.md`` so
``navigation.indexes`` can attach the chapter prose to its nav section.  MkDocs
derives the header buttons from the *staged* path, so both buttons on every
chapter page pointed at ``book/chapterN/index.md`` — a path that does not exist
in the repository, hence a 404 (issue #1019).

Rewriting ``File.edit_uri`` (documented as overwritable) is enough: Material
builds the "view source" link from ``page.edit_url`` too, so both buttons
follow.  Pages with no counterpart in the repository get ``None``, which drops
the buttons instead of rendering a link that cannot resolve.
"""

from __future__ import annotations

from typing import Any, Iterable

from mkdocs.plugins import event_priority

from site_source_paths import repo_relative_source


@event_priority(100)
def on_files(files: Iterable[Any], config: Any, **_: Any) -> None:
    """Retarget every documentation page at its repository source."""
    for file in files:
        if not getattr(file, "is_documentation_page", None) or not file.is_documentation_page():
            continue
        src_uri = getattr(file, "src_uri", None)
        if not src_uri:
            continue
        file.edit_uri = repo_relative_source(str(src_uri))
