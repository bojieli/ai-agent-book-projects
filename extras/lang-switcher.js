// Language switcher: populates the custom dropdown in the header bar.
// On selection, navigates to the equivalent page in the target language and
// rewrites the left sidebar (links + text) to match the new edition.
//
// window.LANG_CONFIG = { zh: {label, prefix, default?}, ... }
// window.SITE_I18N   = generated catalog from scripts/site_i18n.py
// window.SITE_ROOT   = "https://bojieli.github.io/ai-agent-book"

(function () {
  "use strict";

  // Don't run if LANG_CONFIG hasn't been injected by header.html yet.
  // header.html emits the <script>window.LANG_CONFIG = ...</script> before
  // this file loads, so this is just defensive.
  function bindWhenReady() {
    var cfg = window.LANG_CONFIG;
    var i18n = window.SITE_I18N;
    if (!cfg || !i18n) {
      // Retry shortly — header.html or the generated catalog may not have
      // loaded yet if a proxy changed script loading behavior.
      setTimeout(bindWhenReady, 50);
      return;
    }
    init(cfg, i18n);
  }

  function init(cfg, i18n) {

    // ── helpers ───────────────────────────────────────────────

    function detectLang(path) {
      // Match against prefix with trailing slash stripped, so both
      // "/book-en/" and "/book-en" map to "en".
      var p = path.replace(/\/$/, "");
      var codes = Object.keys(cfg).sort(function (a, b) {
        return cfg[b].prefix.length - cfg[a].prefix.length;
      });
      for (var i = 0; i < codes.length; i++) {
        var prefix = cfg[codes[i]].prefix.replace(/\/$/, "");
        if (p.indexOf(prefix) !== -1) return codes[i];
      }
      // Translated experiment indexes have no book prefix, but their
      // README suffix identifies the locale unambiguously. Detect it before
      // consulting sessionStorage so direct links work in a fresh session.
      var readmeMatch = p.match(/(?:^|\/)chapter\d+\/README\.([a-zA-Z-]+)$/);
      if (readmeMatch) {
        for (var r = 0; r < codes.length; r++) {
          if (cfg[codes[r]].readmeSuffix === readmeMatch[1]) return codes[r];
        }
      }
      // Translated homepages (/index.<code>/) carry their locale in the slug.
      var homeMatch = p.match(/(?:^|\/)index\.([a-zA-Z-]+)$/);
      if (homeMatch && cfg[homeMatch[1]]) return homeMatch[1];
      // The site root always serves the default-language homepage (translated
      // homepages are matched above), so don't let a remembered locale make
      // the Chinese homepage look pre-translated.
      if (p === "" || p === "index.html" || p === "/index.html") {
        for (var h in cfg) {
          if (cfg.hasOwnProperty(h) && cfg[h].default) return h;
        }
        return "zh";
      }
      // No language prefix matched. This happens on /chapterN/ experiment
      // index pages (experiments are language-agnostic, single copy).
      // Fall back to whatever the user last selected — stored in
      // sessionStorage so it survives SPA navigation and reloads.
      var remembered = null;
      try { remembered = sessionStorage.getItem("lang-switcher-active"); } catch (_) {}
      if (remembered && cfg[remembered]) return remembered;
      for (var c in cfg) {
        if (cfg.hasOwnProperty(c) && cfg[c].default) return c;
      }
      return "zh";
    }

    function rememberLang(code) {
      try { sessionStorage.setItem("lang-switcher-active", code); } catch (_) {}
    }

    // ── URL rewriting ────────────────────────────────────────
    // One function handles every URL case so there are no scattered patches.
    // Given the current path + target language, returns the new path under
    // the same site base, or null if no translation applies.
    //
    // URL shapes we have to handle:
    //   /                          → site home, default language
    //   /index.<code>/             → site home, translated (when the root
    //                                 file index.<code>.md exists)
    //   /book[-lang]/chapterN[.suffix]/  → chapter prose
    //   /chapterN/                 → experiment index, Chinese (README.md)
    //   /chapterN/README.<readmeSuffix>/ → experiment index, translated
    //   /chapterN/<exp>/           → individual experiment, Chinese only
    //                                 (jump to target lang's chapter prose)
    function translatePath(cleanPath, fromCode, toCode) {
      if (toCode === fromCode) return null;
      var src = cfg[fromCode];
      var dst = cfg[toCode];

      // Site home. Editions with a translated homepage (root index.<code>.md,
      // listed by scripts/site_i18n.py in the generated catalog) map
      // home → home; the rest keep the original fallback to their
      // introduction page, which every edition has.
      var homePages = i18n.homePages || [];
      if (cleanPath === "/" || cleanPath === "/index.html") {
        if (homePages.indexOf(toCode) !== -1) return "/index." + toCode + "/";
        return "/" + dst.prefix + "introduction" + (dst.suffix || "") + "/";
      }

      var pp = cleanPath.replace(/^\//, "").replace(/\/$/, "");

      // Translated homepage: /index.<code>/
      var homeMatch = pp.match(/^index\.([a-zA-Z-]+)$/);
      if (homeMatch) {
        if (dst.default) return "/";
        if (homePages.indexOf(toCode) !== -1) return "/index." + toCode + "/";
        return "/" + dst.prefix + "introduction" + (dst.suffix || "") + "/";
      }

      // Chapter prose: <srcPrefix>chapterN[<srcSuffix>]
      // E.g. /book/chapter1/  or  /book-zhtw/chapter1.zhtw/
      var proseRe = new RegExp("^" + escapeRe(src.prefix) + "chapter(\\d+)" + escapeRe(src.suffix || "") + "$");
      var proseMatch = pp.match(proseRe);
      if (proseMatch) {
        return "/" + dst.prefix + "chapter" + proseMatch[1] + (dst.suffix || "") + "/";
      }

      // Handling book pages that use a shared ASCII slug:
      // introduction, afterword, reference-answers, appendix, ...
      var bookPageRe = new RegExp(
        "^" +
          escapeRe(src.prefix) +
          "([a-z0-9-]+)" +
          escapeRe(src.suffix || "") +
          "$"
      );

      var bookPageMatch = pp.match(bookPageRe);

      if (bookPageMatch) {
        return (
          "/" +
          dst.prefix +
          bookPageMatch[1] +
          (dst.suffix || "") +
          "/"
        );
      }

      // Experiment index: /chapterN/ (Chinese default) or
      // /chapterN/README.<readmeSuffix>/ (translated variants).
      if (/^chapter\d+$/.test(pp)) {
        // Chinese experiment index. Switch to:
        //   zh → /chapterN/                (unchanged)
        //   other → /chapterN/README.<readmeSuffix>/
        if (toCode === "zh") return "/" + pp + "/";
        if (dst.readmeSuffix) return "/" + pp + "/README." + dst.readmeSuffix + "/";
        // An edition can launch before its companion experiment indexes are
        // translated. Keep the switch inside translated content instead of
        // manufacturing a README.undefined URL.
        return "/" + dst.prefix + pp + (dst.suffix || "") + "/";
      }
      var readmeMatch = pp.match(/^chapter(\d+)\/README\.([a-zA-Z-]+)$/);
      if (readmeMatch) {
        if (toCode === "zh") return "/chapter" + readmeMatch[1] + "/";
        if (dst.readmeSuffix) {
          return "/chapter" + readmeMatch[1] + "/README." + dst.readmeSuffix + "/";
        }
        return "/" + dst.prefix + "chapter" + readmeMatch[1] + (dst.suffix || "") + "/";
      }

      // Individual experiment page: /chapterN/<something>/ — Chinese only.
      // No translated copy exists, so jump to the target language's
      // chapter prose (the most useful nearby translated page).
      var expSubMatch = pp.match(/^(chapter\d+)\/[^?]+$/);
      if (expSubMatch && pp.indexOf("README.") === -1) {
        return "/" + dst.prefix + expSubMatch[1] + (dst.suffix || "") + "/";
      }

      return null;
    }

    function escapeRe(s) {
      return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    // ── generated theme chrome localization ──────────────────

    var CHROME_SELECTOR = [
      "[data-md-component='skip']",
      "[data-md-component='announce']",
      ".md-header",
      ".md-search",
      ".md-sidebar",
      ".md-content__button",
      ".md-source-file",
      ".md-top",
      ".md-footer",
      ".md-dialog",
      ".md-tooltip",
      ".md-clipboard",
    ].join(",");

    function translationPairs(targetCode) {
      var source = i18n.languages[i18n.default];
      var target = i18n.languages[targetCode];
      if (!source || !target) return [];
      var pairs = [];
      var key;
      for (key in source.ui) {
        if (source.ui.hasOwnProperty(key) && target.ui[key]) {
          pairs.push([source.ui[key], target.ui[key]]);
        }
      }
      ["sidebar", "palette"].forEach(function (group) {
        for (key in source[group]) {
          if (source[group].hasOwnProperty(key) && target[group][key]) {
            pairs.push([source[group][key], target[group][key]]);
          }
        }
      });
      // Prefer the most specific string when one translation is a substring
      // of another (for example, Search and Initializing search).
      return pairs.sort(function (a, b) { return b[0].length - a[0].length; });
    }

    function translateChromeValue(value, pairs) {
      var trimmed = value.trim();
      if (!trimmed) return value;
      for (var i = 0; i < pairs.length; i++) {
        var from = pairs[i][0];
        var to = pairs[i][1];
        if (trimmed === from) {
          return value.slice(0, value.indexOf(trimmed)) + to + value.slice(value.indexOf(trimmed) + trimmed.length);
        }
        if (from.indexOf("#") !== -1) {
          var match = trimmed.match(new RegExp("^" + escapeRe(from).replace("#", "(.+?)") + "$"));
          if (match) {
            var rendered = to.replace("#", match[1]);
            return value.slice(0, value.indexOf(trimmed)) + rendered + value.slice(value.indexOf(trimmed) + trimmed.length);
          }
        }
      }
      return value;
    }

    function localizeTree(root, pairs) {
      if (!root) return;
      var element = root.nodeType === 1 ? root : root.parentElement;
      if (!element) return;

      var attributed = [];
      if (element.matches && element.matches("[title],[aria-label],[placeholder]")) attributed.push(element);
      if (element.querySelectorAll) {
        attributed = attributed.concat(
          Array.prototype.slice.call(element.querySelectorAll("[title],[aria-label],[placeholder]"))
        );
      }
      for (var a = 0; a < attributed.length; a++) {
        ["title", "aria-label", "placeholder"].forEach(function (name) {
          if (!attributed[a].hasAttribute(name)) return;
          var before = attributed[a].getAttribute(name);
          var after = translateChromeValue(before, pairs);
          if (after !== before) attributed[a].setAttribute(name, after);
        });
      }

      var walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
      var textNode;
      while ((textNode = walker.nextNode())) {
        var translated = translateChromeValue(textNode.nodeValue, pairs);
        if (translated !== textNode.nodeValue) textNode.nodeValue = translated;
      }
    }

    function localizeRevisionDates(targetCode) {
      var strings = i18n.languages[targetCode];
      if (!strings || !window.Intl || !Intl.DateTimeFormat) return;
      var nodes = document.querySelectorAll(".git-revision-date-localized-plugin-date");
      var visibleFormat = new Intl.DateTimeFormat(strings.locale, {
        year: "numeric", month: "long", day: "numeric", timeZone: "UTC",
      });
      var titleFormat = new Intl.DateTimeFormat(strings.locale, {
        year: "numeric", month: "long", day: "numeric",
        hour: "2-digit", minute: "2-digit", second: "2-digit",
        timeZone: "UTC", timeZoneName: "short",
      });
      for (var d = 0; d < nodes.length; d++) {
        var original = nodes[d].getAttribute("title") || nodes[d].textContent;
        var match = original.match(/^(\d{4})年(\d{1,2})月(\d{1,2})日(?:\s+(\d{1,2}):(\d{2}):(\d{2}))?/);
        if (!match) continue;
        var date = new Date(Date.UTC(
          Number(match[1]), Number(match[2]) - 1, Number(match[3]),
          Number(match[4] || 0), Number(match[5] || 0), Number(match[6] || 0)
        ));
        nodes[d].textContent = visibleFormat.format(date);
        nodes[d].setAttribute("title", titleFormat.format(date));
      }
    }

    function localizeChrome(targetCode) {
      if (targetCode === i18n.default || !i18n.languages[targetCode]) return;
      var pairs = translationPairs(targetCode);
      var roots = document.querySelectorAll(CHROME_SELECTOR);
      for (var r = 0; r < roots.length; r++) localizeTree(roots[r], pairs);
      localizeRevisionDates(targetCode);

      // Search results, copy-button tooltips, and dialogs are populated after
      // load. Translate only newly-created theme chrome, never book content.
      if (!window.__siteI18nObserver && document.body) {
        window.__siteI18nObserver = new MutationObserver(function (mutations) {
          for (var m = 0; m < mutations.length; m++) {
            var changed = mutations[m].type === "characterData"
              ? mutations[m].target.parentElement
              : mutations[m].target;
            if (!changed || !changed.closest || !changed.closest(CHROME_SELECTOR)) continue;
            localizeTree(changed, pairs);
            if (changed.closest(".md-source-file")) localizeRevisionDates(targetCode);
          }
        });
        window.__siteI18nObserver.observe(document.body, {
          childList: true,
          characterData: true,
          attributes: true,
          attributeFilter: ["title", "aria-label", "placeholder"],
          subtree: true,
        });
      }
    }

    function siteBasePath() {
      var p = location.pathname;
      try {
        var configured = new URL(window.SITE_ROOT).pathname.replace(/\/$/, "");
        // Use the configured deployment subpath when it is actually present.
        // Local preview servers commonly mount at /, so they fall through to
        // prefix discovery below instead of inheriting the production path.
        if (configured && configured !== "/" &&
            (p === configured || p.indexOf(configured + "/") === 0)) {
          return configured;
        }
      } catch (_) {}
      var best = -1;
      for (var code in cfg) {
        if (!cfg.hasOwnProperty(code)) continue;
        var idx = p.indexOf(cfg[code].prefix);
        if (idx !== -1 && (best === -1 || idx < best)) best = idx;
      }
      if (best !== -1) return p.slice(0, best);
      return "/";
    }

    // ── sidebar rewriting (links + text) ──────────────────────

    function rewriteSidebar(targetCode) {
      var target = cfg[targetCode];
      var strings = i18n.languages[targetCode];
      var defCode = null;
      for (var c in cfg) { if (cfg[c].default) { defCode = c; break; } }
      defCode = defCode || "zh";

      var base = siteBasePath();
      if (base.charAt(base.length - 1) !== "/") base += "/";

      var links = document.querySelectorAll(".md-nav__link");
      for (var i = 0; i < links.length; i++) {
        var el = links[i];
        var href = el.getAttribute("href");
        var navText = el.querySelector(".md-ellipsis");
        var currentText = navText ? navText.textContent.trim() : "";

        if (href && href.charAt(0) !== "#") {
          // Resolve href to a clean path relative to docs root, then
          // translate it via the unified translatePath() function. This
          // handles prose links, experiment-index links, and the Chinese
          // default in one place — no scattered patches.
          try {
            var u = new URL(href, location.href);
            if (u.origin === location.origin) {
              var linkPath = u.pathname;
              if (linkPath.indexOf(base) === 0) {
                var linkRel = "/" + linkPath.slice(base.length).replace(/^\//, "");
                var linkLang = detectLang(linkRel);
                // The canonical sidebar is rendered from the default-language
                // nav, so an un-suffixed /chapterN/ link always starts as the
                // default experiment index. Do not let the remembered active
                // locale make it look pre-translated.
                if (/^\/chapter\d+\/?$/.test(linkRel)) {
                  linkLang = defCode;
                  if (targetCode !== defCode && !target.readmeSuffix) {
                    // Do not advertise a translated experiment index that
                    // does not exist yet. The chapter prose remains linked by
                    // the parent entry and every visible link stays valid.
                    var item = el.closest(".md-nav__item");
                    if (item) item.hidden = true;
                  }
                }
                var translated = translatePath(linkRel, linkLang, targetCode);
                if (translated) {
                  el.setAttribute("href", base + translated.replace(/^\//, ""));
                }
              }
            }
          } catch (_) {}
        }

        if (navText && strings.nav[currentText]) {
          navText.textContent = strings.nav[currentText];
        }
      }

      // Translate the drawer's per-chapter sub-nav headers. When a chapter
      // subtree is opened on mobile, Material shows the chapter title again
      // as <label class="md-nav__title">第2章 …</label>; those labels are
      // plain text (not .md-nav__link), so the loop above misses them. The
      // site-name title at the top is not in the nav catalog and stays untouched.
      var subTitles = document.querySelectorAll(".md-sidebar--primary .md-nav__title");
      for (var st = 0; st < subTitles.length; st++) {
        var stNodes = subTitles[st].childNodes;
        for (var sn = 0; sn < stNodes.length; sn++) {
          var node = stNodes[sn];
          if (node.nodeType !== 3) continue;
          var key = node.textContent.trim();
          if (key && strings.nav[key]) {
            node.textContent = strings.nav[key];
          }
        }
      }
      localizeChrome(targetCode);
    }

    // ── language switch (the actual navigation) ──────────────

    function applyDocumentLocale(code) {
      var strings = i18n.languages[code] || i18n.languages[i18n.default];
      document.documentElement.lang = strings.locale;
      document.documentElement.dir = strings.direction;
      if (document.body) document.body.setAttribute("dir", strings.direction);
      window.siteCurrentLanguage = code;
    }

    function switchTo(target) {
      var rawPath = location.pathname;
      var basePath = siteBasePath();
      var cleanPath = "/" + rawPath.slice(basePath.length).replace(/^\//, "");
      var activeLang = detectLang(cleanPath);
      applyDocumentLocale(activeLang);
      if (!target || target === activeLang) return;
      var rel = translatePath(cleanPath, activeLang, target);
      if (!rel) return;
      var siteRoot = window.SITE_ROOT.replace(/\/$/, "") + "/";
      var finalUrl = siteRoot + rel.replace(/^\//, "");
      // Force a full page reload (bypass Material's navigation.instant, which
      // intercepts location.href and may bounce the user back). We're moving
      // to a different language edition, which is a different "site" — full
      // reload is the right semantic anyway.
      window.location.replace(finalUrl);
    }

    // ── custom dropdown ─────────────────────────────────────

    function closeDropdown(returnFocus) {
      var trigger = document.getElementById("lang-selector");
      var menu = document.getElementById("lang-menu");
      if (!trigger || !menu) return;
      trigger.setAttribute("aria-expanded", "false");
      menu.hidden = true;
      if (returnFocus) trigger.focus();
    }

    function openDropdown(focusDirection) {
      var trigger = document.getElementById("lang-selector");
      var menu = document.getElementById("lang-menu");
      if (!trigger || !menu) return;
      trigger.setAttribute("aria-expanded", "true");
      menu.hidden = false;

      if (focusDirection) {
        var options = menu.querySelectorAll(".lang-menu__option");
        if (!options.length) return;
        var target = menu.querySelector('[aria-checked="true"]');
        if (focusDirection === "first") target = options[0];
        if (focusDirection === "last") target = options[options.length - 1];
        (target || options[0]).focus();
      }
    }

    function moveMenuFocus(current, amount) {
      var menu = document.getElementById("lang-menu");
      if (!menu) return;
      var options = Array.prototype.slice.call(
        menu.querySelectorAll(".lang-menu__option")
      );
      if (!options.length) return;
      var currentIndex = options.indexOf(current);
      var nextIndex = (currentIndex + amount + options.length) % options.length;
      options[nextIndex].focus();
    }

    function optionLocale(code) {
      return i18n.languages[code] ? i18n.languages[code].locale : code;
    }

    function render() {
      var rawPath = location.pathname;
      var basePath = siteBasePath();
      var cleanPath = "/" + rawPath.slice(basePath.length).replace(/^\//, "");
      var activeLang = detectLang(cleanPath);
      applyDocumentLocale(activeLang);

      var trigger = document.getElementById("lang-selector");
      var menu = document.getElementById("lang-menu");
      if (!trigger || !menu) {
        // Localization is useful even if a downstream theme override removes
        // the selector itself. Do not make translated navigation depend on
        // that optional header control.
        rememberLang(activeLang);
        if (activeLang !== i18n.default) rewriteSidebar(activeLang);
        return;
      }

      // Build menu items on first sight of an empty dropdown.
      if (menu.children.length === 0) {
        var codes = Object.keys(cfg);
        for (var idx = 0; idx < codes.length; idx++) {
          var code = codes[idx];
          var option = document.createElement("button");
          option.type = "button";
          option.className = "lang-menu__option";
          option.setAttribute("role", "menuitemradio");
          option.setAttribute("data-lang-code", code);
          option.setAttribute(
            "aria-checked",
            code === activeLang ? "true" : "false"
          );
          option.setAttribute("tabindex", "-1");

          var check = document.createElement("span");
          check.className = "lang-menu__check";
          check.setAttribute("aria-hidden", "true");

          var label = document.createElement("span");
          label.className = "lang-menu__label";
          label.setAttribute("lang", optionLocale(code));
          label.setAttribute("dir", code === "ar" ? "rtl" : "auto");
          label.textContent = cfg[code].label;

          option.appendChild(check);
          option.appendChild(label);
          menu.appendChild(option);
        }
      }

      // Keep the trigger and checked item in sync after SPA navigation.
      var currentLabel = cfg[activeLang].label;
      var labelNode = trigger.querySelector("[data-lang-label]");
      if (labelNode) {
        labelNode.textContent = currentLabel;
        labelNode.setAttribute("lang", optionLocale(activeLang));
        labelNode.setAttribute("dir", activeLang === "ar" ? "rtl" : "auto");
      }
      trigger.setAttribute(
        "aria-label",
        i18n.languages[activeLang].ui["select.language"] + ": " + currentLabel
      );

      var options = menu.querySelectorAll(".lang-menu__option");
      for (var optionIndex = 0; optionIndex < options.length; optionIndex++) {
        var isActive =
          options[optionIndex].getAttribute("data-lang-code") === activeLang;
        options[optionIndex].setAttribute("aria-checked", isActive ? "true" : "false");
      }
      closeDropdown(false);

      var defCode = null;
      for (var c in cfg) { if (cfg[c].default) { defCode = c; break; } }
      rememberLang(activeLang);
      if (activeLang !== (defCode || "zh")) {
        rewriteSidebar(activeLang);
      }
    }

    // ── bootstrap ────────────────────────────────────────────

    // Bind handlers once via event delegation so the dropdown keeps working
    // if Material re-creates the header during SPA navigation.
    if (!window.__langSwitcherBound) {
      window.__langSwitcherBound = true;
      document.addEventListener("click", function (e) {
        if (!e.target || !e.target.closest) return;

        var trigger = e.target.closest("#lang-selector");
        if (trigger) {
          var isOpen = trigger.getAttribute("aria-expanded") === "true";
          if (isOpen) closeDropdown(false);
          else openDropdown(false);
          return;
        }

        var option = e.target.closest(".lang-menu__option");
        if (option) {
          var targetCode = option.getAttribute("data-lang-code");
          closeDropdown(false);
          switchTo(targetCode);
          return;
        }

        if (!e.target.closest(".lang-switcher")) closeDropdown(false);
      });

      document.addEventListener("keydown", function (e) {
        if (!e.target || !e.target.closest) return;
        var trigger = e.target.closest("#lang-selector");
        if (trigger) {
          if (e.key === "ArrowDown" || e.key === "ArrowUp") {
            e.preventDefault();
            openDropdown(e.key === "ArrowDown" ? "first" : "last");
          } else if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            if (trigger.getAttribute("aria-expanded") === "true") {
              closeDropdown(false);
            } else {
              openDropdown("current");
            }
          } else if (e.key === "Escape") {
            closeDropdown(false);
          }
          return;
        }

        var option = e.target.closest(".lang-menu__option");
        if (!option) return;
        if (e.key === "ArrowDown" || e.key === "ArrowUp") {
          e.preventDefault();
          moveMenuFocus(option, e.key === "ArrowDown" ? 1 : -1);
        } else if (e.key === "Home" || e.key === "End") {
          e.preventDefault();
          openDropdown(e.key === "Home" ? "first" : "last");
        } else if (e.key === "Escape") {
          e.preventDefault();
          closeDropdown(true);
        } else if (e.key === "Tab") {
          closeDropdown(false);
        } else if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          option.click();
        }
      });
    }

    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", render);
    } else {
      render();
    }
    // Re-run on every Material SPA navigation. Material exposes document$
    // (a ReactiveSubscribable) that fires after each navigation.instant
    // page swap. Without this hook, the sidebar DOM gets re-rendered by
    // Material with the original (Chinese) nav text and we never get to
    // translate it for non-default languages.
    if (window.document$) {
      window.document$.subscribe(render);
    } else {
      // Fallback for older Material or other themes.
      document.addEventListener("locationchange", render);
      var _pushState = history.pushState;
      history.pushState = function () {
        _pushState.apply(this, arguments);
        setTimeout(render, 60);
      };
    }
  }

  bindWhenReady();
})();
