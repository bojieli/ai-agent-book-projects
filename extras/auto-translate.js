// Tier 3: machine translation for languages the book is not translated into.
//
// The site ships 14 reviewed editions as static pages (tier 1/2). This adds an
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
//   * Always labelled, and honest about what is on screen. A notice sits above
//     the content for as long as the tier is active, tracking the translation
//     through three states — translating / translated / unavailable — off
//     translate.js' own lifecycle hooks, and says what it cannot translate.
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
    // The language switcher lists every edition under its own endonym — 中文,
    // 日本語, العربية, עברית … Translating those is wrong twice over: a reader
    // looking for their language wants to see its own name, and translate.js
    // batches by detected source language, so those labels alone cost one API
    // request per script. That burst (a dozen requests at once) is what the
    // free channel's "more than 2 requests in 2 seconds" guard rejects, taking
    // the page's own batch down with it.
    push(translate.ignore.id, ["lang-menu", "lang-selector"]);

    // translate.listener.start() installs a MutationObserver that re-translates
    // injected content. It is off by default: against Material's
    // navigation.instant swaps it throws "Cannot read properties of null
    // (reading 'nodeValue')" from its own callback, and queues a duplicate
    // translation pass per mutation. Material's `document$` already tells us
    // when a page swap finished, which is the only dynamic content that
    // matters here, so we drive re-translation from that instead.
    if (conf.listener) translate.listener.start();
  }

  function translatePage() {
    var language = selected();
    var conf = config();
    if (!language || !conf) return;

    // The page on screen is still English until a pass lands, so say that.
    setState("pending");

    loadLibrary(conf)
      .then(function (translate) {
        configure(translate, conf);
        if (hookLifecycle(translate, conf)) armStallTimer(conf);
        else watchNoticeText(conf);
        if (translate.to !== language.name) translate.changeLanguage(language.name);
        else translate.execute();
      })
      .catch(function (error) {
        // Leave the English page readable rather than failing loudly.
        console.warn("[auto-translate]", error.message);
        setState("failed");
      });
  }

  // ── translation progress ──────────────────────────────────
  //
  // translate.js reports a failed translation service only to the console, so
  // the notice has to work out for itself whether the page in front of the
  // reader is actually translated. translate.lifecycle is that signal:
  //
  //   execute.start                 a pass began       → "translating"
  //   execute.translateNetworkAfter one batch came back (result 1 ok / 0 failed)
  //   execute.renderFinish          every batch of the pass is rendered
  //
  // Watching them beats timing out on whether our own text changed. A pass can
  // legitimately run for tens of seconds — the free channel retries against two
  // backup hosts — and a fixed deadline declared those dead, then never looked
  // again, so a translation that landed late left the reader staring at
  // "unavailable" on a fully translated page. Here the deadline only fires when
  // nothing has moved for a whole window, and a later renderFinish still
  // corrects the notice.
  var passes = {};
  var stallTimer = null;
  var hooked = false;

  function armStallTimer(conf) {
    clearTimeout(stallTimer);
    stallTimer = setTimeout(function () {
      // Nothing moved for a whole window. Say so, but stay subscribed: if the
      // pass does come back, renderFinish flips the notice to "translated".
      if (noticeState === "pending") setState("failed");
    }, conf.failureTimeoutMs || 12000);
  }

  function hookLifecycle(translate, conf) {
    var cycle = translate.lifecycle && translate.lifecycle.execute;
    if (!cycle || !cycle.start || !cycle.renderFinish) return false;
    if (hooked) return true;
    hooked = true;

    // translate.js passes the legacy positional arguments to any handler
    // declared with exactly two parameters, and the object form to every other
    // arity — so `start` and `translateNetworkAfter` take one parameter here on
    // purpose, and `renderFinish` is positional-only in the library.
    cycle.start.push(function (data) {
      passes[data.uuid] = { requests: 0, done: 0, sourceSeen: false, sourceDone: false };
      setState("pending");
      armStallTimer(conf);
    });

    cycle.translateNetworkAfter.push(function (data) {
      var pass = passes[data.uuid];
      if (!pass) return;
      pass.requests++;
      if (data.result === 1) pass.done++;
      if (data.from === (conf.sourceLanguage || "english")) {
        pass.sourceSeen = true;
        if (data.result === 1) pass.sourceDone = true;
      }
      armStallTimer(conf); // a batch came back: the pass is alive
    });

    cycle.renderFinish.push(function (uuid) {
      var pass = passes[uuid];
      delete passes[uuid];
      clearTimeout(stallTimer);
      // No request at all means every string came out of the local cache.
      // Where there were requests, the one that decides this is the batch out
      // of the source language: that is the book's own prose. Other batches
      // are stray strings in other scripts, and one of those failing says
      // nothing about the page the reader is looking at.
      var failed =
        !!pass && pass.requests > 0 && (pass.sourceSeen ? !pass.sourceDone : pass.done === 0);
      setState(failed ? "failed" : "ok");
    });

    cycle.finally.push(function (data) {
      // 5: the page is already in the target language, so the pass returns
      // before renderFinish. Nothing to translate is not a failure.
      if (data.state === 5) {
        clearTimeout(stallTimer);
        setState("ok");
      }
    });

    return true;
  }

  // Fallback for a translate.js without lifecycle hooks (pre-3.18). The notice
  // sits inside the translated region, so a working service rewrites it.
  function watchNoticeText(conf) {
    var probe = document.querySelector(".auto-translate-notice__text--ok");
    if (!probe) return;
    var before = probe.textContent;
    clearTimeout(stallTimer);
    stallTimer = setTimeout(function () {
      var node = document.querySelector(".auto-translate-notice__text--ok");
      if (node) setState(node.textContent === before ? "failed" : "ok");
    }, conf.failureTimeoutMs || 12000);
  }

  // ── notice ────────────────────────────────────────────────

  var STATES = ["pending", "ok", "failed"];

  var NOTICE_TEXT = {
    pending: "Machine-translating this page in your browser — one moment.",
    ok:
      "Machine-translated from the English edition — not reviewed. " +
      "Figures and code stay in English.",
    failed: "Machine translation is unavailable right now. Showing the English edition.",
  };

  var noticeState = null;

  // Every state's wording is in the DOM from the start, with CSS showing one at
  // a time. That is what lets the notice speak the reader's language: a pass
  // translates all three at once, so switching states afterwards is a class
  // change rather than fresh English text that nothing will ever come back for.
  function buildNotice() {
    var host = document.querySelector(".md-content__inner");
    if (!host) return null;

    var existing = host.querySelector(".auto-translate-notice");
    if (existing) return existing;

    var notice = document.createElement("div");
    notice.className = "auto-translate-notice";
    notice.setAttribute("role", "note");

    for (var i = 0; i < STATES.length; i++) {
      var text = document.createElement("span");
      text.className = "auto-translate-notice__text auto-translate-notice__text--" + STATES[i];
      // Written in the source language on purpose: translate.js picks it up
      // with the rest of the page, so the reader sees it in their own language.
      text.textContent = NOTICE_TEXT[STATES[i]];
      notice.appendChild(text);
    }

    var off = document.createElement("button");
    off.type = "button";
    off.className = "auto-translate-notice__off";
    off.textContent = "Turn off";
    off.addEventListener("click", function () {
      select(null);
      location.reload();
    });

    notice.appendChild(off);
    host.insertBefore(notice, host.firstChild);
    return notice;
  }

  function setState(state) {
    noticeState = state;
    // Update in place: replacing the node would detach the text nodes that an
    // in-flight translation pass is holding references to.
    var notice = buildNotice();
    if (!notice) return;
    notice.className = "auto-translate-notice auto-translate-notice--" + state;
    notice.setAttribute("data-state", state);
    // Only claim the reader's locale once the page is actually in it. While a
    // pass is running, and after one failed, the text on screen is still
    // English — and an <html lang> that disagrees with it (or an RTL flip over
    // English prose) misleads screen readers and hyphenation both.
    applyDocumentLocale(state === "ok" ? selected() : null);
  }

  var SOURCE_LOCALE = document.documentElement.lang || "en";
  var SOURCE_DIR = document.documentElement.dir === "rtl" ? "rtl" : "ltr";

  function applyDocumentLocale(language) {
    var root = document.documentElement;
    if (!language) {
      root.lang = SOURCE_LOCALE;
      root.dir = SOURCE_DIR;
      return;
    }
    if (language.locale) root.lang = language.locale;
    root.dir = language.dir === "rtl" ? "rtl" : "ltr";
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

    syncMenuState(conf);
    translatePage();
  }

  // ── bootstrap ─────────────────────────────────────────────

  function render() {
    var conf = config();
    if (!conf || !conf.languages || !conf.languages.length) return;
    buildMenuGroup(conf);
    syncMenuState(conf);

    if (!selected()) return;
    // translatePage() puts up the notice; it owns which state it shows.
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
