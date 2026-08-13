// Point Material's search at this edition's slice of the search index.
//
// scripts/split_search_index.py splits the one 55 MB search_index.json the
// search plugin emits into `search/search_index.<slug>.json`, one per book
// edition (slug = the edition's URL directory: `book`, `book-en`, ...), each
// carrying that edition plus the shared experiment pages. This script decides
// which slice the current page needs and rewrites the request for it.
//
// Why an XHR patch rather than configuration: Material builds the index URL
// as `new URL("search/search_index.json", config.base)` and requests it via
// XMLHttpRequest while bundle.js initialises. There is no config seam for the
// path, and `extra_javascript` files load *after* bundle.js — too late. So
// overrides/main.html loads this file inside the `config` block, which base.html
// renders immediately before bundle.js, and we intercept the one request.
//
// If anything here fails to identify an edition we simply leave the URL alone:
// search_index.json still holds the default edition plus the shared pages, so
// search degrades to its previous behaviour rather than breaking.

(function () {
  "use strict";

  var INDEX_RE = /\/search\/search_index\.json$/;

  // `chapterN/README.<readmeSuffix>/` and `index.<code>/` — pages that belong
  // to an edition but live outside its book-*/ directory.
  var README_RE = /\/chapter\d+\/README\.([A-Za-z-]+)\/?(?:index\.html)?$/;
  var HOMEPAGE_RE = /\/index\.([A-Za-z-]+)\/?(?:index\.html)?$/;

  // Mirrors edition_of() in scripts/split_search_index.py — keep the two in
  // step, or a reader gets an index that omits the edition they are reading.
  function slugForPath(path, cfg) {
    var code, entry;

    // 1. An explicit book-*/ path segment. Exact segment matches only, so the
    //    `/ai-agent-book/` site subpath can never be mistaken for an edition.
    var slugs = {};
    for (code in cfg) {
      if (cfg.hasOwnProperty(code) && cfg[code].prefix) {
        slugs[cfg[code].prefix.replace(/\/$/, "")] = true;
      }
    }
    var segments = path.split("/");
    for (var i = 0; i < segments.length; i++) {
      if (slugs[segments[i]]) return segments[i];
    }

    // 2. Translated experiment indexes and homepages, keyed by their suffix.
    var match = path.match(README_RE) || path.match(HOMEPAGE_RE);
    if (match) {
      for (code in cfg) {
        if (!cfg.hasOwnProperty(code)) continue;
        entry = cfg[code];
        if (!entry.prefix) continue;
        if (entry.readmeSuffix === match[1] || code === match[1]) {
          return entry.prefix.replace(/\/$/, "");
        }
      }
    }

    // 3. Language-agnostic pages (the `chapterN/` experiments, the site root).
    //    Reuse the switcher's remembered locale so a reader who came from an
    //    edition keeps searching it; lang-switcher.js writes the same key.
    var remembered = null;
    try {
      remembered = sessionStorage.getItem("lang-switcher-active");
    } catch (_) {}
    if (remembered && cfg[remembered] && cfg[remembered].prefix) {
      return cfg[remembered].prefix.replace(/\/$/, "");
    }

    return null;
  }

  var cfg = window.LANG_CONFIG;
  if (!cfg) return; // header.html emits it before this script; nothing to do.

  var slug = slugForPath(location.pathname, cfg);
  if (!slug) return;

  var open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    var args = Array.prototype.slice.call(arguments);
    if (typeof url === "string" && INDEX_RE.test(url)) {
      args[1] = url.replace(INDEX_RE, "/search/search_index." + slug + ".json");
    }
    return open.apply(this, args);
  };
})();
