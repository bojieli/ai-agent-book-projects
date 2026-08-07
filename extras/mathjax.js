/**
 * MathJax 3 configuration for MkDocs Material.
 *
 * This file MUST be loaded before the MathJax bundle
 * (`tex-mml-chtml.js`) in mkdocs.yml `extra_javascript` — MathJax reads
 * `window.MathJax` once at startup, so setting it afterwards has no effect.
 *
 * `pymdownx.arithmatex` (generic mode) rewrites the book's `$...$` and
 * `$$...$$` source math into `\(...\)` / `\[...\]` wrapped in
 * `<span class="arithmatex">` / `<div class="arithmatex">`. MathJax's
 * default delimiters are `$...$`/`$$...$$`, which no longer exist in the
 * rendered HTML, so without this config nothing is typeset at all.
 */
window.MathJax = {
  tex: {
    inlineMath: [['\\(', '\\)']],
    displayMath: [['\\[', '\\]']],
    processEscapes: true,
    processEnvironments: true,
  },
  options: {
    // Only typeset elements arithmatex marked as math; ignore everything
    // else (code blocks, search summaries, etc.).
    ignoreHtmlClass: '.*|',
    processHtmlClass: 'arithmatex',
  },
};

// Material's `navigation.instant` swaps page content without a full reload,
// so MathJax must re-typeset after every page swap (same pattern as
// extras/mermaid-init.js).
document$.subscribe(() => {
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});
