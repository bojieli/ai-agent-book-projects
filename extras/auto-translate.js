// Tier 3: machine translation for languages the book is not translated into.
//
// The site ships 13 reviewed editions as static pages (tier 1/2). This adds an
// opt-in fallback for everything else: the reader picks a language from the
// "机器翻译" group in the language menu and translate.js
// (https://github.com/xnx3/translate, MIT) rewrites the page's text nodes in
// the browser against a machine-translation service.
//
// Deliberate constraints, because this tier is strictly worse than a built
// edition and must not be mistaken for one:
//
//   * Opt-in and lazy. The third-party script is fetched only after the reader
//     chooses one of these languages — a page view in a real edition makes no
//     request to it. It is pinned to a version and loaded with an SRI hash.
//   * Always labelled. An "auto-translated" notice sits above the content for
//     as long as the tier is active, and says what it cannot translate.
//   * Translated from the English edition, not the Chinese one: MT quality out
//     of English is better for most targets, and that edition is reviewed. So
//     selecting a tier-3 language first routes to the English page.
//   * Never indexed. This runs client-side only; crawlers receive the untouched
//     English source, so no machine-translated text enters search results.
//
// What it cannot do: figures. They are <img src="…svg">, a separate document
// that page scripts cannot reach, so diagrams stay in English. Code blocks are
// left alone on purpose (translate.js ignores <pre>/<code> by default).

(function () {
  "use strict";

  var STORAGE_KEY = "auto-translate";

  function config() {
    return window.AUTO_TRANSLATE_CONFIG || null;
  }

  // ── persisted selection ───────────────────────────────────

  function selected() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var value = JSON.parse(raw);
      return value && value.name ? value : null;
    } catch (_) {
      return null;
    }
  }

  function select(language) {
    try {
      if (language) localStorage.setItem(STORAGE_KEY, JSON.stringify(language));
      else localStorage.removeItem(STORAGE_KEY);
    } catch (_) {}
  }

  // ── translate.js ──────────────────────────────────────────

  var libraryPromise = null;
  var configured = false;

  function loadLibrary(conf) {
    if (libraryPromise) return libraryPromise;
    libraryPromise = new Promise(function (resolve, reject) {
      if (window.translate) return resolve(window.translate);
      var script = document.createElement("script");
      script.src = conf.cdn;
      if (conf.integrity) {
        // The library is third-party and loaded from a public CDN; pin the
        // exact bytes so a compromised or swapped file cannot execute here.
        script.integrity = conf.integrity;
        script.crossOrigin = "anonymous";
      }
      script.onload = function () {
        window.translate ? resolve(window.translate) : reject(new Error("translate.js absent"));
      };
      script.onerror = function () {
        reject(new Error("translate.js failed to load"));
      };
      document.head.appendChild(script);
    });
    return libraryPromise;
  }

  function push(list, values) {
    for (var i = 0; i < values.length; i++) {
      if (list.indexOf(values[i]) === -1) list.push(values[i]);
    }
  }

  function configure(translate, conf) {
    if (configured) return;
    configured = true;

    // We drive language choice from the site's own switcher.
    translate.selectLanguageTag.show = false;
    translate.service.use(conf.service || "client.edge");
    translate.language.setLocal(conf.sourceLanguage || "english");

    // translate.ignore.tag already holds style/script/link/pre/code, so code
    // blocks are safe out of the box. These are this site's additions.
    push(translate.ignore.tag, [
      "mjx-container", // MathJax output
    ]);
    push(translate.ignore.class, [
      "mermaid", // diagram source and rendered SVG
      "arithmatex", // inline/block math
      "highlight", // code block wrapper (line-number table sits outside <pre>)
      "md-source", // repository name + stars/forks in the header
    ]);

    // Re-translate content injected after load (search results, annotations).
    translate.listener.start();
  }

  function translatePage() {
    var language = selected();
    var conf = config();
    if (!language || !conf) return;

    loadLibrary(conf)
      .then(function (translate) {
        configure(translate, conf);
        if (translate.to !== language.name) translate.changeLanguage(language.name);
        else translate.execute();
      })
      .catch(function (error) {
        // Leave the English page readable rather than failing loudly.
        console.warn("[auto-translate]", error.message);
        showNotice(language, true);
      });
  }

  // ── notice ────────────────────────────────────────────────

  function showNotice(language, failed) {
    var host = document.querySelector(".md-content__inner");
    if (!host) return;

    var existing = host.querySelector(".auto-translate-notice");
    if (existing) existing.parentNode.removeChild(existing);

    var notice = document.createElement("div");
    notice.className = "auto-translate-notice";
    if (failed) notice.className += " auto-translate-notice--failed";
    // Written in the source language on purpose: translate.js picks it up with
    // the rest of the page, so the reader sees it in their own language.
    notice.setAttribute("role", "note");

    var text = document.createElement("span");
    text.className = "auto-translate-notice__text";
    text.textContent = failed
      ? "Machine translation is unavailable right now. Showing the English edition."
      : "Machine-translated from the English edition — not reviewed. " +
        "Figures and code stay in English.";

    var off = document.createElement("button");
    off.type = "button";
    off.className = "auto-translate-notice__off";
    off.textContent = "Turn off";
    off.addEventListener("click", function () {
      select(null);
      location.reload();
    });

    notice.appendChild(text);
    notice.appendChild(off);
    host.insertBefore(notice, host.firstChild);
  }

  function applyDocumentLocale(language) {
    if (!language) return;
    if (language.locale) document.documentElement.lang = language.locale;
    document.documentElement.dir = language.dir === "rtl" ? "rtl" : "ltr";
  }

  // ── language menu ─────────────────────────────────────────

  function buildMenuGroup(conf) {
    var menu = document.getElementById("lang-menu");
    // Wait for lang-switcher.js to build the real editions first, so the
    // machine-translated group always sorts below them.
    if (!menu || menu.children.length === 0) return;
    if (menu.querySelector(".lang-menu__group")) return;

    var group = document.createElement("div");
    group.className = "lang-menu__group";
    group.setAttribute("role", "presentation");
    group.textContent = conf.label || "机器翻译";
    menu.appendChild(group);

    for (var i = 0; i < conf.languages.length; i++) {
      var language = conf.languages[i];
      var option = document.createElement("button");
      option.type = "button";
      // Same class as a real edition so the switcher's keyboard navigation
      // includes these, but keyed by `data-auto-lang` rather than
      // `data-lang-code` so its click handler treats them as a no-op.
      option.className = "lang-menu__option lang-menu__option--auto";
      option.setAttribute("role", "menuitemradio");
      option.setAttribute("data-auto-lang", language.name);
      option.setAttribute("aria-checked", "false");
      option.setAttribute("tabindex", "-1");

      var check = document.createElement("span");
      check.className = "lang-menu__check";
      check.setAttribute("aria-hidden", "true");

      var label = document.createElement("span");
      label.className = "lang-menu__label";
      if (language.locale) label.setAttribute("lang", language.locale);
      label.setAttribute("dir", language.dir === "rtl" ? "rtl" : "auto");
      label.textContent = language.label;

      option.appendChild(check);
      option.appendChild(label);
      menu.appendChild(option);
    }
  }

  function syncMenuState(conf) {
    var active = selected();
    var options = document.querySelectorAll(".lang-menu__option--auto");
    for (var i = 0; i < options.length; i++) {
      options[i].setAttribute(
        "aria-checked",
        active && options[i].getAttribute("data-auto-lang") === active.name ? "true" : "false"
      );
    }
    if (!active) return;

    // lang-switcher.js has just set the trigger to the source edition's label
    // ("English"); the reader is looking at a machine translation, so say so.
    var labelNode = document.querySelector("#lang-selector [data-lang-label]");
    if (labelNode) {
      labelNode.textContent = active.label;
      if (active.locale) labelNode.setAttribute("lang", active.locale);
      labelNode.setAttribute("dir", active.dir === "rtl" ? "rtl" : "auto");
    }
  }

  function activate(name, conf) {
    var language = null;
    for (var i = 0; i < conf.languages.length; i++) {
      if (conf.languages[i].name === name) language = conf.languages[i];
    }
    if (!language) return;

    select(language);

    // Machine-translate the English edition, not whichever one the reader is
    // on. urlFor() returns null when we are already there.
    var url = window.langSwitcher && window.langSwitcher.urlFor(conf.source || "en");
    if (url) {
      window.location.replace(url);
      return;
    }

    applyDocumentLocale(language);
    showNotice(language, false);
    syncMenuState(conf);
    translatePage();
  }

  // ── bootstrap ─────────────────────────────────────────────

  function render() {
    var conf = config();
    if (!conf || !conf.languages || !conf.languages.length) return;
    buildMenuGroup(conf);
    syncMenuState(conf);

    var active = selected();
    if (!active) return;
    applyDocumentLocale(active);
    showNotice(active, false);
    translatePage();
  }

  function bind() {
    if (window.__autoTranslateBound) return;
    window.__autoTranslateBound = true;

    // Capture phase: lang-switcher.js listens on document during bubble, so
    // this runs first — early enough to claim our own options, and to clear
    // the selection before it navigates away to a real edition.
    document.addEventListener(
      "click",
      function (e) {
        if (!e.target || !e.target.closest) return;

        var auto = e.target.closest(".lang-menu__option--auto");
        if (auto) {
          e.stopPropagation();
          e.preventDefault();
          var conf = config();
          if (conf) activate(auto.getAttribute("data-auto-lang"), conf);
          return;
        }

        // Choosing a real edition leaves this tier.
        var edition = e.target.closest(".lang-menu__option[data-lang-code]");
        if (edition) select(null);
      },
      true
    );
  }

  bind();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }

  // Material swaps pages without a reload; re-add the notice and re-translate.
  // This file is listed after lang-switcher.js in mkdocs.yml, so its subscriber
  // runs first and the menu is already rebuilt by the time we sync it.
  if (window.document$) window.document$.subscribe(render);
})();
