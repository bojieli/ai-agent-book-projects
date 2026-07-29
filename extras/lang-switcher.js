// Language switcher: populates a <select> dropdown in the header bar.
// On change, navigates to the equivalent page in the target language and
// rewrites the left sidebar (links + text) to match the new edition.
//
// window.LANG_CONFIG = { zh: {label, prefix, default?}, ... }
// window.SITE_ROOT    = "https://bojieli.github.io/ai-agent-book"

(function () {
  "use strict";

  // Don't run if LANG_CONFIG hasn't been injected by header.html yet.
  // header.html emits the <script>window.LANG_CONFIG = ...</script> before
  // this file loads, so this is just defensive.
  function bindWhenReady() {
    var cfg = window.LANG_CONFIG;
    if (!cfg) {
      // Retry shortly — header.html may inject it after this script runs.
      setTimeout(bindWhenReady, 50);
      return;
    }
    init(cfg);
  }

  function init(cfg) {
    // ── nav label translations ────────────────────────────────
    // Keyed by the Chinese label in mkdocs.yml; values per target language.
    // When on a non-default language, sidebar text is replaced from this map.
    var NAV_I18N = {
      "首页":         { en: "Home",           ru: "Главная",    ta: "முகப்பு",       vi: "Trang chủ",     zhtw: "首頁", ja: "ホーム", ar: "الرئيسية", es: "Inicio" },
      "引言":         { en: "Introduction",   ru: "Введение",   ta: "அறிமுகம்",      vi: "Giới thiệu",    zhtw: "引言", ja: "はじめに", ar: "المقدمة", es: "Introducción" },
      "第1章 Agent基础知识": { en: "Chapter 1 · Getting Started with AI Agents", ru: "Глава 1 · Введение в ИИ-агенты",           ta: "அதி. 1 · AI ஏஜெண்ட் அடிப்படைகள்",     vi: "Chương 1 · Nền tảng AI Agent", zhtw: "第 1 章 · Agent 基礎知識", ja: "第1章 · Agent の基礎知識", ar: "الفصل 1 · أساسيات الوكلاء", es: "Capítulo 1 · Fundamentos de los Agentes de IA" },
      "第2章 上下文工程":     { en: "Chapter 2 · Context Engineering", ru: "Глава 2 · Инженерия контекста",    ta: "அதி. 2 · சூழல் பொறியியல்",          vi: "Chương 2 · Kỹ thuật ngữ cảnh", zhtw: "第 2 章 · 上下文工程", ja: "第2章 · コンテキストエンジニアリング", ar: "الفصل 2 · هندسة السياق", es: "Capítulo 2 · Ingeniería de Contexto" },
      "第3章 用户记忆和知识库": { en: "Chapter 3 · User Memory & Knowledge Base", ru: "Глава 3 · Память и база знаний",  ta: "அதி. 3 · பயனர் நினைவகம் & அறிவுத்தளம்", vi: "Chương 3 · Bộ nhớ & Cơ sở kiến thức", zhtw: "第 3 章 · 使用者記憶和知識庫", ja: "第3章 · ユーザーメモリと知識ベース", ar: "الفصل 3 · ذاكرة المستخدم وقاعدة المعرفة", es: "Capítulo 3 · Memoria de Usuario y Base de Conocimiento" },
      "第4章 工具":           { en: "Chapter 4 · Tools", ru: "Глава 4 · Инструменты",                  ta: "அதி. 4 · கருவிகள்",                vi: "Chương 4 · Công cụ",          zhtw: "第 4 章 · 工具", ja: "第4章 · ツール", ar: "الفصل 4 · الأدوات", es: "Capítulo 4 · Herramientas" },
      "第5章 CodingAgent与代码生成": { en: "Chapter 5 · Coding Agent & Code Generation", ru: "Глава 5 · Кодинг-агент и генерация кода",  ta: "அதி. 5 · குறியீட்டு ஏஜெண்ட் & குறியீடு உருவாக்கம்", vi: "Chương 5 · Coding Agent & Tạo mã", zhtw: "第 5 章 · Coding Agent 與程式碼生成", ja: "第5章 · Coding Agent とコード生成", ar: "الفصل 5 · وكيل البرمجة وتوليد الشيفرة", es: "Capítulo 5 · Agente de Código y Generación de Código" },
      "第6章 Agent的评估":    { en: "Chapter 6 · Evaluating Agents", ru: "Глава 6 · Оценка агентов",      ta: "அதி. 6 · ஏஜெண்ட் மதிப்பீடு",        vi: "Chương 6 · Đánh giá Agent",   zhtw: "第 6 章 · Agent 的評估", ja: "第6章 · Agent の評価", ar: "الفصل 6 · تقييم الوكلاء", es: "Capítulo 6 · Evaluación de Agentes" },
      "第7章 模型后训练":     { en: "Chapter 7 · Model Post-Training", ru: "Глава 7 · Постобучение модели",    ta: "அதி. 7 · மாதிரி பிந்தைய பயிற்சி",   vi: "Chương 7 · Post-training mô hình", zhtw: "第 7 章 · 模型後訓練", ja: "第7章 · モデルのポストトレーニング", ar: "الفصل 7 · ما بعد تدريب النموذج", es: "Capítulo 7 · Posentrenamiento de Modelos" },
      "第8章 Agent的持续进化": { en: "Chapter 8 · Continual Evolution of Agents", ru: "Глава 8 · Самоэволюция агента",   ta: "அதி. 8 · ஏஜெண்ட் சுய-பரிணாமம்",     vi: "Chương 8 · Tự tiến hóa của Agent", zhtw: "第 8 章 · Agent 的自我進化", ja: "第8章 · Agent の自己進化", ar: "الفصل 8 · التطور الذاتي للوكيل", es: "Capítulo 8 · Evolución Continua de los Agentes" },
      "第9章 多模态与实时交互": { en: "Chapter 9 · Multimodal & Real-Time Interaction", ru: "Глава 9 · Мультимодальность и реальное время",  ta: "அதி. 9 · பல்முக & நிகழ்நேரம்",       vi: "Chương 9 · Đa phương thức & Thời gian thực", zhtw: "第 9 章 · 多模態與即時互動", ja: "第9章 · マルチモーダルとリアルタイム対話", ar: "الفصل 9 · تعدد الوسائط والتفاعل الفوري", es: "Capítulo 9 · Multimodalidad e Interacción en Tiempo Real" },
      "第10章 多Agent协作":   { en: "Chapter 10 · Multi-Agent Collaboration", ru: "Глава 10 · Мультиагентное взаимодействие",  ta: "அதி. 10 · பல-ஏஜெண்ட் ஒத்துழைப்பு", vi: "Chương 10 · Đa Agent cộng tác", zhtw: "第 10 章 · 多 Agent 協作", ja: "第10章 · マルチ Agent 協調", ar: "الفصل 10 · تعاون متعدد الوكلاء", es: "Capítulo 10 · Colaboración Multiagente" },
      "后记":         { en: "Afterword", ru: "Послесловие",        ta: "பின்னுரை",       vi: "Lời bạt",         zhtw: "後記", ja: "あとがき", ar: "الخاتمة", es: "Epílogo" },
      "思考题参考答案": { en: "Reference Answers", ru: "Ответы к вопросам",  ta: "பதில் வழிகாட்டி", vi: "Đáp án tham khảo", zhtw: "思考題參考答案", ja: "演習問題の解答例", ar: "إجابات الأسئلة", es: "Respuestas de Referencia" },
      // Nested sub-entry under each chapter (the experiment index).
      "配套实验":     { en: "Experiments", ru: "Эксперименты",     ta: "சோதனைகள்",     vi: "Thí nghiệm",   zhtw: "配套實驗", ar: "التجارب", es: "Experimentos" },
    };

    // Right-sidebar TOC title ("目录"), fixed by theme.language at build
    // time — rewritten client-side on translated editions.
    var TOC_TITLE = {
      zh: "目录", zhtw: "目錄", en: "On this page",
      ta: "உள்ளடக்கம்", vi: "Mục lục", ru: "На этой странице",
      ar: "في هذه الصفحة", es: "En esta página",
    };

    var SEARCH_STRINGS = {
      zh:   { placeholder: "搜索",   searching: "正在初始化搜索引擎", input: "键入进行检索" },
      en:   { placeholder: "Search", searching: "Initializing search", input: "Type to search" },
      zhtw: { placeholder: "搜尋",   searching: "正在初始化搜尋引擎", input: "鍵入進行檢索" },
      ru:   { placeholder: "Поиск",  searching: "Инициализация поиска", input: "Введите запрос" },
      ta:   { placeholder: "தேடு",   searching: "தேடல் தொடங்கப்படுகிறது", input: "தட்டச்சு செய்து தேடவும்" },
      vi:   { placeholder: "Tìm kiếm", searching: "Đang khởi tạo",     input: "Gõ để tìm kiếm" },
      ar:   { placeholder: "بحث", searching: "جارٍ تهيئة البحث", input: "اكتب للبحث" },
      es:   { placeholder: "Buscar", searching: "Inicializando búsqueda", input: "Escriba para buscar" },
    };

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
    //   /                          → site home (per-language intro)
    //   /book[-lang]/chapterN[.suffix]/  → chapter prose
    //   /chapterN/                 → experiment index, Chinese (README.md)
    //   /chapterN/README.<readmeSuffix>/ → experiment index, translated
    //   /chapterN/<exp>/           → individual experiment, Chinese only
    //                                 (jump to target lang's chapter prose)
    function translatePath(cleanPath, fromCode, toCode) {
      if (toCode === fromCode) return null;
      var src = cfg[fromCode];
      var dst = cfg[toCode];

      // Site home → target language's introduction.
      if (cleanPath === "/" || cleanPath === "/index.html") {
        return "/" + dst.prefix + "introduction" + (dst.suffix || "") + "/";
      }

      var pp = cleanPath.replace(/^\//, "").replace(/\/$/, "");

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
        return toCode === "zh"
          ? "/" + pp + "/"
          : "/" + pp + "/README." + dst.readmeSuffix + "/";
      }
      var readmeMatch = pp.match(/^chapter(\d+)\/README\.([a-zA-Z-]+)$/);
      if (readmeMatch) {
        return toCode === "zh"
          ? "/chapter" + readmeMatch[1] + "/"
          : "/chapter" + readmeMatch[1] + "/README." + dst.readmeSuffix + "/";
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

    function siteBasePath() {
      try { return new URL(window.SITE_ROOT).pathname; } catch (_) {}
      var p = location.pathname;
      var idx = Math.max(p.indexOf("book-en/"), p.indexOf("book-ru/"), p.indexOf("book-ta/"),
                         p.indexOf("book-vi/"), p.indexOf("book-zhtw/"),
                         p.indexOf("book-ja/"), p.indexOf("book-ar/"),
                         p.indexOf("book-es/"), p.indexOf("book/"));
      if (idx === -1) return "/";
      return p.slice(0, idx);
    }

    // ── sidebar rewriting (links + text) ──────────────────────

    function rewriteSidebar(targetCode) {
      var target = cfg[targetCode];
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
                var translated = translatePath(linkRel, linkLang, targetCode);
                if (translated) {
                  el.setAttribute("href", base + translated.replace(/^\//, ""));
                }
              }
            }
          } catch (_) {}
        }

        if (navText && NAV_I18N[currentText] && NAV_I18N[currentText][targetCode]) {
          navText.textContent = NAV_I18N[currentText][targetCode];
        }
      }

      // Translate the drawer's per-chapter sub-nav headers. When a chapter
      // subtree is opened on mobile, Material shows the chapter title again
      // as <label class="md-nav__title">第2章 …</label>; those labels are
      // plain text (not .md-nav__link), so the loop above misses them. The
      // site-name title at the top is not in NAV_I18N and stays untouched.
      var subTitles = document.querySelectorAll(".md-sidebar--primary .md-nav__title");
      for (var st = 0; st < subTitles.length; st++) {
        var stNodes = subTitles[st].childNodes;
        for (var sn = 0; sn < stNodes.length; sn++) {
          var node = stNodes[sn];
          if (node.nodeType !== 3) continue;
          var key = node.textContent.trim();
          if (key && NAV_I18N[key] && NAV_I18N[key][targetCode]) {
            node.textContent = NAV_I18N[key][targetCode];
          }
        }
      }

      // Translate the right-sidebar TOC title. Only replace the text node —
      // the label also contains the (mobile-only) back-arrow icon span.
      if (TOC_TITLE[targetCode]) {
        var tocTitles = document.querySelectorAll(".md-nav--secondary > .md-nav__title");
        for (var t = 0; t < tocTitles.length; t++) {
          var nodes = tocTitles[t].childNodes;
          for (var n = 0; n < nodes.length; n++) {
            if (nodes[n].nodeType === 3 && nodes[n].textContent.trim()) {
              nodes[n].textContent = TOC_TITLE[targetCode];
            }
          }
        }
      }

      // Translate the search box placeholder + status text.
      var strings = SEARCH_STRINGS[targetCode] || SEARCH_STRINGS.en;
      var searchInput = document.querySelector(".md-search__input");
      if (searchInput) {
        searchInput.setAttribute("placeholder", strings.placeholder);
      }
    }

    // ── language switch (the actual navigation) ──────────────

    function applyDocumentLocale(code) {
      document.documentElement.lang = code === "zhtw" ? "zh-TW" : code;
      document.documentElement.dir = code === "ar" ? "rtl" : "ltr";
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

    // ── render the <select> options ──────────────────────────

    function render() {
      var rawPath = location.pathname;
      var basePath = siteBasePath();
      var cleanPath = "/" + rawPath.slice(basePath.length).replace(/^\//, "");
      var activeLang = detectLang(cleanPath);
      applyDocumentLocale(activeLang);

      var sel = document.getElementById("lang-selector");
      if (!sel) return;

      // Build options on first sight of an empty select.
      if (sel.children.length === 0) {
        var codes = Object.keys(cfg);
        for (var idx = 0; idx < codes.length; idx++) {
          var code = codes[idx];
          var opt = document.createElement("option");
          opt.value = code;
          opt.textContent = cfg[code].label;
          if (code === activeLang) opt.selected = true;
          sel.appendChild(opt);
        }
      } else {
        // Update which option is selected for the current page.
        sel.value = activeLang;
      }

      var defCode = null;
      for (var c in cfg) { if (cfg[c].default) { defCode = c; break; } }
      rememberLang(activeLang);
      if (activeLang !== (defCode || "zh")) {
        rewriteSidebar(activeLang);
      }
    }

    // ── bootstrap ────────────────────────────────────────────

    // Bind the change handler ONCE via event delegation. This way it keeps
    // working even if Material re-creates the <select> during SPA navigation.
    if (!window.__langSwitcherBound) {
      window.__langSwitcherBound = true;
      document.addEventListener("change", function (e) {
        if (!e.target || e.target.id !== "lang-selector") return;
        switchTo(e.target.value);
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
