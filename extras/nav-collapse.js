/**
 * Desktop navigation controls for Material's primary sidebar.
 *
 * Background: with `navigation.sections` + `navigation.indexes`, each
 * chapter renders as
 *
 *   <li class="md-nav__item--section md-nav__item--nested">
 *     <input class="md-toggle" id="__nav_N">
 *     <div class="md-nav__link md-nav__container">
 *       <a href="…/chapterN/">chapter title</a>   ← navigates
 *       <label for="__nav_N">chevron</label>      ← toggles
 *     </div>
 *     <nav class="md-nav">…配套实验…</nav>
 *   </li>
 *
 * Material only honours the checkbox on mobile; on desktop the section
 * subtree is always visible and the chevron is hidden. We inject CSS so
 * that on desktop, too, the subtree follows the checkbox and the chevron
 * is visible/clickable. Material checks the active chapter's checkbox at
 * render time, so the default state (active chapter open, rest closed)
 * comes for free.
 *
 * One case needs JS: on pages Material doesn't consider "active" — the
 * translated editions (sidebar links are rewritten client-side by
 * lang-switcher.js) and the per-experiment pages, which aren't in the
 * nav — no checkbox is checked. There we match the current URL against
 * each section's chapter number and open the matching section.
 *
 * The header also contains a desktop-only button for hiding the entire
 * primary sidebar. Its state is persisted locally and restored across full
 * reloads as well as Material's instant page swaps.
 *
 * Re-runs on every Material page swap (navigation.instant) via document$.
 */
(function () {
  "use strict";

  var SIDEBAR_STORAGE_KEY = "ai-agent-book.primary-sidebar-collapsed";

  function ensureStyle() {
    if (document.getElementById("nav-collapse-style")) return;
    var s = document.createElement("style");
    s.id = "nav-collapse-style";
    s.textContent = [
      "@media screen and (min-width: 76.25em) {",
      // Collapse the subtree when the checkbox is unchecked (Material
      // keeps section subtrees always-visible on desktop by default).
      "  .md-sidebar--primary .md-nav__item--nested > .md-toggle:not(:checked) ~ .md-nav {",
      "    display: none !important;",
      "  }",
      // Material hides the section chevron on desktop; bring it back and
      // make it clickable.
      "  .md-sidebar--primary .md-nav__item--nested > .md-nav__container > label.md-nav__link {",
      "    display: flex;",
      "    align-items: center;",
      "    cursor: pointer;",
      "    pointer-events: auto !important;",
      "    margin: 0;",
      // 4px top padding centres the 1.2rem icon on the title's FIRST line
      // (6px link padding + ~1.3 line-height): the container aligns
      // flex-start (book-theme.css) so wrapped two-line titles don't pull
      // the chevron down between the lines.
      "    padding: 4px 0.2rem 0 0.4rem;",
      "  }",
      // Material's own stylesheet already rotates the chevron's ::after
      // by 90° when the checkbox is checked — no extra transform here.
      "  .md-sidebar--primary .md-nav__item--nested > .md-nav__container > label.md-nav__link .md-nav__icon {",
      "    display: block;",
      "  }",
      "}",
    ].join("\n");
    document.head.appendChild(s);
  }

  function applyDefaultState() {
    var sidebar = document.querySelector(".md-sidebar--primary");
    if (!sidebar) return;

    // Material already checked a section's checkbox? Then its render-time
    // active detection worked — nothing to fix up.
    if (sidebar.querySelector(".md-nav__item--nested > .md-toggle:checked")) return;

    // Otherwise (translated edition or a page outside the nav), derive the
    // chapter from the URL and open the matching section.
    var m = location.pathname.match(/chapter(\d+)/);
    if (!m) return;
    var wanted = m[1];
    var sections = sidebar.querySelectorAll(".md-nav__item--nested");
    for (var i = 0; i < sections.length; i++) {
      var link = sections[i].querySelector(":scope > .md-nav__container > a.md-nav__link");
      var checkbox = sections[i].querySelector(":scope > .md-toggle");
      if (!link || !checkbox) continue;
      var lm = (link.getAttribute("href") || "").match(/chapter(\d+)/);
      if (lm && lm[1] === wanted) {
        checkbox.checked = true;
        break;
      }
    }
  }

  function readSidebarPreference() {
    try {
      var value = window.localStorage.getItem(SIDEBAR_STORAGE_KEY);
      return value === null ? null : value === "true";
    } catch (_) {
      // Storage may be disabled by the browser. The control still works for
      // the current page, and the root class survives Material page swaps.
      return null;
    }
  }

  function writeSidebarPreference(collapsed) {
    try {
      window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(collapsed));
    } catch (_) {
      // A blocked localStorage must not prevent readers from using the
      // collapse control for the current page.
    }
  }

  function setSidebarCollapsed(collapsed, remember) {
    document.documentElement.classList.toggle("sidebar-nav-collapsed", collapsed);

    var button = document.querySelector("[data-sidebar-toggle]");
    if (button) {
      var label = collapsed ? "展开侧边栏" : "隐藏侧边栏";
      button.setAttribute("aria-expanded", String(!collapsed));
      button.setAttribute("aria-label", label);
      button.setAttribute("title", label);
    }

    if (remember) writeSidebarPreference(collapsed);
  }

  function initSidebarToggle() {
    var button = document.querySelector("[data-sidebar-toggle]");
    var sidebar = document.querySelector(".md-sidebar--primary");
    if (!button || !sidebar || sidebar.hidden) {
      if (button) button.hidden = true;
      return;
    }

    // Connect aria-controls to the sidebar generated by Material. The id is
    // re-applied because navigation.instant replaces page content in place.
    sidebar.id = "primary-navigation";
    button.hidden = false;

    var preference = readSidebarPreference();
    var collapsed = preference === null
      ? document.documentElement.classList.contains("sidebar-nav-collapsed")
      : preference;
    setSidebarCollapsed(collapsed, false);

    if (button.getAttribute("data-sidebar-toggle-bound") !== "true") {
      button.setAttribute("data-sidebar-toggle-bound", "true");
      button.addEventListener("click", function () {
        var next = !document.documentElement.classList.contains("sidebar-nav-collapsed");
        setSidebarCollapsed(next, true);
      });
    }
  }

  function init() {
    ensureStyle();
    applyDefaultState();
    initSidebarToggle();
  }

  document.addEventListener("DOMContentLoaded", init);
  if (window.document$) window.document$.subscribe(init);
})();
