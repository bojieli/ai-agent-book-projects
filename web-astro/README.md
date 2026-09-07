# Astro reading prototype

A local design exploration for **AI Agents in Depth**, built with plain Astro.
The homepage and complete Chapter 1 are implemented in English, Simplified Chinese,
and Traditional Chinese. All other chapter
links lead to the existing online edition.

## Run locally

From the repository root, with Node.js 22.12 or newer:

```sh
cd web-astro
npm ci
npm run dev
```

Open the URL printed by Astro (normally `http://127.0.0.1:4321`). The chapter is
at `/book-en/chapter1/`, matching its existing online path. Use the header language
switcher to view Chinese homepages at `/zh-CN/` and `/zh-TW/`, and Chapter 1 at
`/book/chapter1/` and `/book-zhtw/chapter1.zhtw/`. Astro 7 runs the
server in the background; stop it with `npx astro dev stop` from this directory.

```sh
npm run check
npm run build
npm test
```

`npm test` checks the generated production pages, so run the build first.
`npm run format` formats the prototype's source.

## Design and reading features

- Language switcher keeps readers on the homepage or Chapter 1 in their chosen edition.
- Editorial homepage with an animated agent loop and all 10 chapters.
- The loop supports pause/play, manual steps, reduced motion, and off-screen suspension.
- Chapter reader with book navigation, an active section outline, and a mobile menu.
- Light/dark themes, adjustable text size, focus mode, and chapter progress.
- Expandable figures, captions, code copying, tables, and linked footnotes.
- Select a passage to highlight it; revisit or remove it in My highlights.
- Highlights and plain-text notes save in IndexedDB on this browser, with JSON backup export/import.
- Choose Add note on a selection or click a highlight to edit it. Save note commits
  the note; unfinished drafts are stored separately and restored after closing or reloading.
- Backups include notes and drafts for the current edition only. Import into the same language edition. Older highlight-only backups still import;
  conflicting notes are kept as separate entries rather than overwritten.
- Fonts are self-hosted. No accounts, external font requests, or AI services.

Theme and text-size preferences stay in the browser's local storage. The reader
does not save reading position yet. Highlights are scoped to this book, language,
and chapter; clearing site data removes them, and private browsing may discard
them on exit. They do not sync across devices or site origins. Export a backup
before switching browsers or moving from localhost to a hosted preview.

Highlight anchoring stores the selected quote and surrounding text. Ambiguous
or changed passages remain in My highlights as unmatched quotes. This first
version supports chapter prose (including inline emphasis and links), excluding
code blocks, figures, and footnotes. Essential content and links work without
JavaScript; enhanced controls are shown when their scripts initialize.

## Source boundaries

Each Chapter 1 route imports its tracked Markdown directly from `book-en/`,
`book/`, or `book-zhtw/`. Shared `Home.astro` and `Reader.astro` components render
the editions; `src/lib/i18n.ts` defines edition routes and `translations.json`
contains interface text. `src/lib/book.ts` reads chapter titles through Vite's raw imports.
There is no second editable copy of the book text.

`src/lib/book-markdown.mjs` adapts the web rendering: it removes the duplicated
chapter heading, adds figure captions from existing alt text, and resolves image
and relative page links. Astro's unified Markdown processor preserves GFM tables,
footnotes, and highlighted code. Only Chapter 1's syntax has been validated;
Pandoc attributes, math, and Mermaid in other chapters need migration work.

`npm run dev` and `npm run build` copy Chapter 1's seven referenced images
per edition (21 total) into ignored generated public directories. Rerun the
command when source images change. The original Markdown, assets, MkDocs
configuration, PDF pipeline, and root dependencies are untouched.

The existing repository license applies. The book is by Bojie Li; translation
credits and source history remain available in `docs/en/README.md` and Git.

## Prototype limits

- Three prototype editions; other chapters open the matching existing edition.
- The book has 15 editions; the remaining languages and search are not prototyped yet.
- Explicit language URLs are authoritative; no automatic language redirects.
- Chinese typography uses system fonts; it may vary across operating systems.
- No deployment configuration or publishing workflow; this preview is local only.
- Root hosting paths are assumed. A GitHub Pages subpath needs an explicit base
  URL migration before deployment.
- Preview pages use `noindex, nofollow` until a publishing decision is made.

## Figure review

The homepage diagram connects context, the model, tools, and the environment.
Its arrows show observations entering context, context informing the model, tool
selection, and actions returning to the environment. Animation follows those
arrows; there are no decorative orbits or unrelated activity indicators.

The original Chapter 1 figures are retained for specific teaching purposes:

| Figure | Purpose                                                                   |
| ------ | ------------------------------------------------------------------------- |
| 1-1    | Distinguish agent/environment and model/harness boundaries.               |
| 1-2    | Compare contextual adaptation, external artifacts, and parameter updates. |
| 1-3    | Explain the context ablation experiment.                                  |
| 1-4    | Follow a multi-step tool-calling trajectory.                              |
| 1-5    | Explain native tool calling and the surrounding architecture.             |
| 1-6    | Explain the execution loop of an autonomous agent.                        |
| 1-7    | Show an actual workflow editor connecting model, memory, and tools.       |

A source-content review found issues to reconcile separately before presenting
this as a revised edition. These are in the existing SVGs, which this prototype
copies unchanged:

- `book-en/images/fig1-3.svg` describes the reasoning-history ablation as
  “Inconsistent decisions.” The adjacent prose says dropping reconstructible
  reasoning history costs almost nothing.
- `book-en/images/fig1-4.svg` labels trajectory as the complete LLM input, while
  the prose defines context as static prefix plus trajectory. Its three-quarter
  example is also labeled annual revenue, and its displayed rounded arithmetic
  does not produce the precise reported total.
