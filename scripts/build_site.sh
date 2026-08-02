#!/usr/bin/env bash
# Assemble the MkDocs docs directory (`_web/`) from the book Markdown sources.
# Reader-facing Markdown, images, frontend assets, and linked JSON evidence are
# copied; code, PDFs and LaTeX sources are left out so the generated site stays
# small. The original sources are never modified.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/_web"

rm -rf "$DEST"
mkdir -p "$DEST"

# Site homepage (root index.md).
cp "$ROOT/index.md" "$DEST/index.md"

# Translated site homepages (root index.<lang>.md), when present. The
# language switcher maps home <-> home for these editions (see
# scripts/site_i18n.py, which lists them in the generated catalog).
for home in "$ROOT"/index.*.md; do
  [ -f "$home" ] || continue
  cp "$home" "$DEST/$(basename "$home")"
done

# robots.txt at the site root (points crawlers at the auto-generated sitemap).
[ -f "$ROOT/robots.txt" ] && cp "$ROOT/robots.txt" "$DEST/robots.txt"

# The language editions, each with its images/ subfolder.
for lang in book book-en book-es book-id book-ru book-ta book-vi book-zhtw book-ja book-ar book-tr book-ko book-hu; do
  mkdir -p "$DEST/$lang"
  cp -R "$ROOT/$lang" "$DEST/"
done

# Promote each chapter of the default (zh) edition to a directory index
# (book/chapterN.md -> book/chapterN/index.md) so mkdocs.yml can use
# navigation.indexes to attach the chapter prose to its nav section —
# clicking a chapter title in the sidebar then opens the chapter directly.
# The rendered URL is unchanged (/book/chapterN/, thanks to directory
# URLs). The file now lives one directory deeper, so its relative image
# references need a ../ prefix. Translated editions stay flat files: they
# are not listed in the nav, so they gain nothing from the promotion.
for n in 1 2 3 4 5 6 7 8 9 10; do
  src="$DEST/book/chapter$n.md"
  [ -f "$src" ] || continue
  mkdir -p "$DEST/book/chapter$n"
  sed \
    -e 's|](images/|](../images/|g' \
    -e 's|](../chapter|](../../chapter|g' \
    "$src" > "$DEST/book/chapter$n/index.md"
  rm "$src"
done

# The companion experiment directories (chapterN/). Each chapter has a
# README.md (experiment index) plus one subfolder per experiment, also
# documented by its own README.md. These are exposed under /chapterN/ so
# readers can step from the chapter prose straight into runnable code.
for ch in chapter1 chapter2 chapter3 chapter4 chapter5 \
         chapter6 chapter7 chapter8 chapter9 chapter10; do
  if [ -d "$ROOT/$ch" ]; then
    cp -R "$ROOT/$ch" "$DEST/"
  fi
done

# Copy site-level assets (JS/CSS for the language switcher) that MkDocs
# resolves relative to docs_dir.
cp -R "$ROOT/extras" "$DEST/extras"

# Site-wide static assets — logo, favicon, social OG images. Referenced by
# mkdocs.yml as `assets/<file>` (relative to docs_dir).
if [ -d "$ROOT/assets" ]; then
  mkdir -p "$DEST/assets"
  cp -R "$ROOT/assets/." "$DEST/assets/"
fi

# Keep reader-facing site assets, including JSON experiment evidence linked
# from chapter documentation. The helper is tested independently so changes to
# the publication allowlist do not silently introduce broken links.
python3 "$ROOT/scripts/clean_site_files.py" "$DEST"

# Drop bulk data files that some experiments bundle as their dataset but
# that don't belong in the reading site (hundreds of legal-doc markdown
# files would also slow the git-revision-date plugin to a crawl).
rm -rf \
  "$DEST/chapter3/contextual-retrieval/laws" \
  "$DEST/chapter3/agentic-rag/laws" \
  2>/dev/null || true

# Vendored JavaScript dependencies can contain thousands of their own
# Markdown files. They are irrelevant to the book site and make MkDocs scan
# needlessly large directory trees after the file-type cleanup above.
find "$DEST" -type d -name node_modules -prune -exec rm -rf {} +

# Rewrite the relative links used inside the experiment READMEs so they
# resolve correctly in the MkDocs site. Source files are NOT modified —
# only the copies under _web/.
#
# The README source uses GitHub-style relative paths that don't survive
# MkDocs rendering. Two patterns appear in chapter index pages
# (`chapterN/README.md`):
#   ../book/chapter1.md   (point at the chapter prose)
#   ../README.md          (point at the repo root / homepage)
#
# MkDocs renders pages as directory URLs (`chapter1/`), so the `.md`
# suffix must be stripped. Keep the paths RELATIVE (no leading slash) so
# they keep working under the site's sub-path
# (`https://bojieli.github.io/ai-agent-book/`).
find "$DEST/chapter"* -type f -name '*.md' -print0 \
  | xargs -0 sed -i.bak \
      -e 's|\.\./book/\([a-zA-Z0-9_-]*\)\.md|../book/\1/|g' \
      -e 's|\.\./README\.md|../|g'
# macOS sed needs the backup suffix above; clean up the .bak files.
find "$DEST" -name '*.md.bak' -delete

# Per-language experiment index pages (chapterN/README.<lang>.md) contain
# relative links like [exp](local_llm_serving/) that resolve correctly on
# the Chinese URL /chapterN/ but break on the translated URL
# /chapterN/README.<lang>/ (they'd resolve to /chapterN/README.<lang>/exp/,
# which 404s). Rewrite those relative links to be relative to /chapterN/
# by prefixing ../ — this makes them resolve to /chapterN/<exp>/ in any
# language edition.
#
# Only touches README.<lang>.md (not README.md, where the links already work),
# and only relative links that don't start with . / # http or contain :
#
# The "back to main README" links ](../docs/<locale>/README.md) point into
# docs/, which is never copied into the site's docs_dir — MkDocs leaves the
# raw href and it 404s. Map them to ../../ (the site home) instead.
find "$DEST/chapter"* -type f -name 'README.[a-zA-Z-]*.md' -print0 \
  | xargs -0 sed -i.bak -E \
      -e 's|\]\(([a-zA-Z][a-zA-Z0-9_-]*)/\)|](../\1/)|g' \
      -e 's|\]\(\.\./docs/[a-zA-Z-]+/README\.md\)|](../../)|g'
find "$DEST" -name '*.md.bak' -delete

echo "Assembled docs into $DEST"
