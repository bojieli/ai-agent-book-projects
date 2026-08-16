// Behaviour tests for extras/auto-translate.js (tier-3 machine translation).
//
// Not wired into CI: the repo has no JavaScript test harness, and adding npm to
// the pipeline is a bigger decision than this feature warrants. Run manually:
//
//     npm install jsdom            # once, anywhere on NODE_PATH
//     node tests/js/auto-translate.test.js
//
// Exits non-zero on failure.
const fs = require("fs");
const assert = require("assert");
const { JSDOM, VirtualConsole } = require("jsdom");

const path = require("path");
const SRC = fs.readFileSync(
  path.join(__dirname, "..", "..", "extras", "auto-translate.js"),
  "utf8"
);

const CONF = {
  label: "机器翻译 / Machine translation",
  source: "en",
  sourceLanguage: "english",
  service: "giteeAI",
  listener: false,
  failureTimeoutMs: 60,
  cdn: "https://cdn.example.test/translate.js",
  integrity: "sha384-TESTHASH",
  languages: [
    { name: "french", label: "Français", locale: "fr" },
    { name: "hebrew", label: "עברית", locale: "he", dir: "rtl" },
  ],
};

// A stand-in for translate.js with the same API surface the script touches,
// including the lifecycle hooks the notice's state machine subscribes to.
// Nothing fires on its own: each test drives the pass it wants to describe.
function fakeTranslate({ lifecycle = true } = {}) {
  const t = {
    to: "",
    selectLanguageTag: { show: true },
    service: { used: null, use(n) { this.used = n; } },
    language: { local: null, setLocal(n) { this.local = n; } },
    ignore: { tag: ["style", "script", "link", "pre", "code"], class: ["ignore"], id: [] },
    listener: { started: false, start() { this.started = true; } },
    calls: [],
    changeLanguage(n) { this.to = n; this.calls.push(["changeLanguage", n]); this.pass && this.pass.start(); },
    execute() { this.calls.push(["execute"]); this.pass && this.pass.start(); },
  };
  if (!lifecycle) return t;

  t.lifecycle = {
    execute: { start: [], translateNetworkAfter: [], renderFinish: [], finally: [] },
  };
  const fire = (name, ...args) => t.lifecycle.execute[name].forEach((f) => f(...args));
  let uuid = 0;
  // Mirrors what translate.js emits for one translate.execute() call.
  t.pass = {
    uuid: null,
    start() { this.uuid = "uuid-" + ++uuid; fire("start", { uuid: this.uuid, to: t.to }); },
    batch(from, result) {
      fire("translateNetworkAfter", { uuid: this.uuid, from, to: t.to, result });
    },
    renderFinish() { fire("renderFinish", this.uuid, t.to); },
    finally(state) { fire("finally", { uuid: this.uuid, to: t.to, state }); },
  };
  return t;
}

const stateOf = (w) => {
  const n = w.document.querySelector(".auto-translate-notice");
  return n && n.getAttribute("data-state");
};

async function setup({
  path = "/ai-agent-book/book-en/chapter1/",
  stored = null,
  urlFor = () => null,
  lifecycle = true,
} = {}) {
  const navErrors = [];
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => navErrors.push(e.message));
  const dom = new JSDOM(
    `<!doctype html><html><head></head><body>
       <button id="lang-selector" aria-expanded="false"><span data-lang-label>English</span></button>
       <div id="lang-menu">
         <button class="lang-menu__option" data-lang-code="zh"><span class="lang-menu__label">中文</span></button>
         <button class="lang-menu__option" data-lang-code="en"><span class="lang-menu__label">English</span></button>
       </div>
       <div class="md-content__inner"><h1>Chapter 1</h1></div>
     </body></html>`,
    { url: "https://example.test" + path, runScripts: "outside-only", virtualConsole: vc }
  );
  const w = dom.window;
  w.AUTO_TRANSLATE_CONFIG = CONF;
  w.langSwitcher = { current: () => "en", urlFor };
  if (stored) w.localStorage.setItem("auto-translate", JSON.stringify(stored));

  // Capture script injection instead of hitting the network.
  const injected = [];
  const realAppend = w.document.head.appendChild.bind(w.document.head);
  w.document.head.appendChild = (node) => {
    if (node.tagName === "SCRIPT") {
      injected.push(node);
      setTimeout(() => { w.translate = w.__fakeTranslate; node.onload && node.onload(); }, 0);
      return node;
    }
    return realAppend(node);
  };
  w.__fakeTranslate = fakeTranslate({ lifecycle });

  const replaced = [];
  try { w.location.replace = (u) => replaced.push(u); } catch (_) {}
  w.eval(SRC);
  // jsdom fires DOMContentLoaded asynchronously; the script waits for it.
  await new Promise((r) => setTimeout(r, 5));
  return { w, dom, injected, replaced, navErrors };
}

const tick = () => new Promise((r) => setTimeout(r, 5));
const tests = [];
const test = (name, fn) => tests.push([name, fn]);

test("appends a labelled group with one option per tier-3 language", async () => {
  const { w } = await setup();
  const menu = w.document.getElementById("lang-menu");
  const group = menu.querySelector(".lang-menu__group");
  assert.ok(group, "group heading missing");
  assert.strictEqual(group.textContent, CONF.label);
  const options = menu.querySelectorAll(".lang-menu__option--auto");
  assert.strictEqual(options.length, 2);
  assert.strictEqual(options[0].getAttribute("data-auto-lang"), "french");
  // Must not carry data-lang-code, or lang-switcher.js would try to navigate.
  assert.strictEqual(options[0].getAttribute("data-lang-code"), null);
  // Built editions still come first.
  assert.ok(menu.children[0].getAttribute("data-lang-code"));
});

test("is inert when no config is present", async () => {
  const { w } = await setup();
  delete w.AUTO_TRANSLATE_CONFIG;
  const menu = w.document.getElementById("lang-menu");
  const before = menu.children.length;
  w.document.dispatchEvent(new w.Event("DOMContentLoaded"));
  assert.strictEqual(menu.children.length, before);
});

test("does not build the group twice", async () => {
  const { w } = await setup();
  w.document.dispatchEvent(new w.Event("DOMContentLoaded"));
  assert.strictEqual(w.document.querySelectorAll(".lang-menu__group").length, 1);
  assert.strictEqual(w.document.querySelectorAll(".lang-menu__option--auto").length, 2);
});

test("selecting a language off the English edition routes there first", async () => {
  const target = "https://example.test/ai-agent-book/book-en/chapter1/";
  const asked = [];
  const { w, injected, navErrors } = await setup({
    path: "/ai-agent-book/book/chapter1/",
    urlFor: (code) => { asked.push(code); return code === "en" ? target : null; },
  });
  w.document.querySelector('[data-auto-lang="french"]').click();
  assert.deepStrictEqual(asked, ["en"], "should ask for the English edition URL");
  assert.ok(navErrors.some((m) => /navigation/i.test(m)), "should navigate away");
  assert.strictEqual(injected.length, 0, "must not load translate.js before navigating");
  assert.strictEqual(JSON.parse(w.localStorage.getItem("auto-translate")).name, "french");
});

test("on the English edition it loads, configures and translates", async () => {
  const { w, injected } = await setup();
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();

  assert.strictEqual(injected.length, 1);
  assert.strictEqual(injected[0].src, CONF.cdn);
  assert.strictEqual(injected[0].integrity, CONF.integrity);
  assert.strictEqual(injected[0].crossOrigin, "anonymous");

  const t = w.translate;
  assert.strictEqual(t.service.used, "giteeAI");
  assert.strictEqual(t.language.local, "english");
  assert.strictEqual(t.selectLanguageTag.show, false);
  assert.strictEqual(t.listener.started, false, "MutationObserver must stay off by default");
  assert.ok(t.ignore.tag.includes("mjx-container"), "MathJax output must be ignored");
  assert.ok(t.ignore.tag.includes("pre") && t.ignore.tag.includes("code"), "defaults kept");
  for (const c of ["mermaid", "arithmatex", "highlight", "md-source"]) {
    assert.ok(t.ignore.class.includes(c), `${c} must be ignored`);
  }
  // The language menu lists every edition under its own endonym; translating
  // those is both wrong and one API request per script.
  for (const id of ["lang-menu", "lang-selector"]) {
    assert.ok(t.ignore.id.includes(id), `#${id} must be ignored`);
  }
  assert.deepStrictEqual(t.calls, [["changeLanguage", "french"]]);
});

test("shows a labelled notice carrying every state's wording", async () => {
  const { w } = await setup();
  w.document.querySelector('[data-auto-lang="hebrew"]').click();
  await tick();
  const notice = w.document.querySelector(".auto-translate-notice");
  assert.ok(notice, "notice missing");
  // All three are in the DOM so one translation pass covers them; CSS shows one.
  assert.match(notice.textContent, /Machine-translating this page/);
  assert.match(notice.textContent, /Machine-translated from the English edition/);
  assert.match(notice.textContent, /not reviewed/);
  assert.match(notice.textContent, /Figures and code stay in English/);
  assert.match(notice.textContent, /unavailable/);
  assert.strictEqual(w.document.querySelectorAll(".auto-translate-notice__text").length, 3);
});

test("reports progress while the pass runs, then that it is translated", async () => {
  const { w } = await setup();
  w.document.querySelector('[data-auto-lang="hebrew"]').click();
  await tick();

  // Mid-flight: the text on screen is still English, so neither the "done"
  // wording nor the Hebrew locale may be claimed yet.
  assert.strictEqual(stateOf(w), "pending");
  assert.strictEqual(w.document.documentElement.lang, "en");
  assert.strictEqual(w.document.documentElement.dir, "ltr");

  w.translate.pass.batch("english", 1);
  w.translate.pass.renderFinish();
  assert.strictEqual(stateOf(w), "ok");
  assert.strictEqual(w.document.documentElement.lang, "he");
  assert.strictEqual(w.document.documentElement.dir, "rtl");
});

test("a pass that renders without any request counts as translated", async () => {
  // Everything came out of translate.js' local cache — no network, no failure.
  const { w } = await setup();
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  w.translate.pass.renderFinish();
  assert.strictEqual(stateOf(w), "ok");
});

test("a failed batch in another source language does not mask a translated page", async () => {
  const { w } = await setup();
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  w.translate.pass.batch("english", 1); // the book's prose
  w.translate.pass.batch("chinese_simplified", 0); // a stray string elsewhere
  w.translate.pass.renderFinish();
  assert.strictEqual(stateOf(w), "ok");
});

test("a failed source-language batch is reported as unavailable", async () => {
  const { w } = await setup();
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  w.translate.pass.batch("english", 0);
  w.translate.pass.renderFinish();
  assert.strictEqual(stateOf(w), "failed");
  assert.strictEqual(w.document.documentElement.lang, "en", "must not claim the target locale");
});

test("a stored selection is re-applied on the next page load", async () => {
  const { w, injected } = await setup({ stored: { name: "french", label: "Français", locale: "fr" } });
  await tick();
  assert.strictEqual(injected.length, 1, "should load the library on its own");
  assert.deepStrictEqual(w.translate.calls, [["changeLanguage", "french"]]);
  assert.ok(w.document.querySelector(".auto-translate-notice"));
  // The trigger must advertise the machine-translated language, not "English".
  assert.strictEqual(w.document.querySelector("[data-lang-label]").textContent, "Français");
  assert.strictEqual(
    w.document.querySelector('[data-auto-lang="french"]').getAttribute("aria-checked"),
    "true"
  );
});

test("no library request happens for a reader who never opts in", async () => {
  const { w, injected } = await setup();
  await tick();
  assert.strictEqual(injected.length, 0);
  assert.strictEqual(w.translate, undefined);
});

test("choosing a built edition clears the selection", async () => {
  const { w } = await setup({ stored: { name: "french", label: "Français", locale: "fr" } });
  w.document.querySelector('[data-lang-code="zh"]').click();
  assert.strictEqual(w.localStorage.getItem("auto-translate"), null);
});

test("'Turn off' clears the selection and reloads", async () => {
  const { w, navErrors } = await setup({ stored: { name: "french", label: "Français", locale: "fr" } });
  await tick();
  const before = navErrors.length;
  w.document.querySelector(".auto-translate-notice__off").click();
  assert.strictEqual(w.localStorage.getItem("auto-translate"), null);
  assert.ok(navErrors.length > before, "should reload the page");
});

test("a failed library load degrades to a visible warning", async () => {
  const { w } = await setup();
  // Make the injected script fail instead of loading.
  w.document.head.appendChild = (node) => {
    if (node.tagName === "SCRIPT") { setTimeout(() => node.onerror && node.onerror(), 0); return node; }
    return node;
  };
  w.console.warn = () => {};
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  assert.strictEqual(stateOf(w), "failed");
  assert.ok(w.document.querySelector(".auto-translate-notice--failed"), "failure class missing");
});

test("corrupt storage is ignored rather than throwing", async () => {
  const { w, injected } = await setup();
  w.localStorage.setItem("auto-translate", "{not json");
  w.document.dispatchEvent(new w.Event("DOMContentLoaded"));
  await tick();
  assert.strictEqual(injected.length, 0);
});

test("starts translate.js' listener only when explicitly enabled", async () => {
  const { w } = await setup();
  w.AUTO_TRANSLATE_CONFIG = { ...CONF, listener: true };
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  assert.strictEqual(w.translate.listener.started, true);
});

test("warns when a pass stalls with nothing coming back", async () => {
  const { w } = await setup();
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  const notice = w.document.querySelector(".auto-translate-notice");
  await new Promise((r) => setTimeout(r, 120)); // past failureTimeoutMs
  assert.strictEqual(stateOf(w), "failed");
  // Same node, not a replacement — an in-flight pass may hold a reference.
  assert.strictEqual(w.document.querySelector(".auto-translate-notice"), notice);
});

test("a batch coming back keeps a slow pass from being called dead", async () => {
  const { w } = await setup();
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  // The free channel retries against backup hosts, so batches can trickle in
  // for well past one timeout window. Progress restarts the clock, not trips it.
  for (let i = 0; i < 4; i++) {
    await new Promise((r) => setTimeout(r, 40));
    w.translate.pass.batch("english", 1);
  }
  assert.strictEqual(stateOf(w), "pending", "must not cry wolf while batches land");
  w.translate.pass.renderFinish();
  assert.strictEqual(stateOf(w), "ok");
});

test("a late pass corrects a notice that already gave up", async () => {
  // The reported bug: the page ends up translated, yet the notice still says
  // the service is unavailable because nothing ever looked again.
  const { w } = await setup();
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  await new Promise((r) => setTimeout(r, 120));
  assert.strictEqual(stateOf(w), "failed");

  w.translate.pass.batch("english", 1);
  w.translate.pass.renderFinish();
  assert.strictEqual(stateOf(w), "ok", "a translation that lands late must clear the warning");
  assert.strictEqual(w.document.documentElement.lang, "fr");
});

test("a page already in the target language is not a failure", async () => {
  const { w } = await setup();
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  w.translate.pass.finally(5); // local language == target: no render pass follows
  await new Promise((r) => setTimeout(r, 120));
  assert.strictEqual(stateOf(w), "ok");
});

test("without lifecycle hooks an untouched notice still warns", async () => {
  const { w } = await setup({ lifecycle: false });
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  await new Promise((r) => setTimeout(r, 120));
  assert.strictEqual(stateOf(w), "failed");
});

test("without lifecycle hooks it falls back to watching its own text", async () => {
  const { w } = await setup({ lifecycle: false });
  w.document.querySelector('[data-auto-lang="french"]').click();
  await tick();
  assert.strictEqual(stateOf(w), "pending");
  // Simulate translate.js rewriting the page (including our notice).
  w.document.querySelector(".auto-translate-notice__text--ok").textContent =
    "Traduit automatiquement de l'\u00e9dition anglaise";
  await new Promise((r) => setTimeout(r, 120));
  assert.strictEqual(stateOf(w), "ok");
});

(async () => {
  let failed = 0;
  for (const [name, fn] of tests) {
    try { await fn(); console.log("PASS  " + name); }
    catch (e) { failed++; console.log("FAIL  " + name + "\n      " + e.message); }
  }
  console.log(failed ? `\n${failed} FAILURES` : `\nALL ${tests.length} PASS`);
  process.exit(failed ? 1 : 0);
})();
