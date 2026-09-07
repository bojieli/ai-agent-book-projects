import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const source = readFileSync(
  new URL('../../book-en/chapter1.md', import.meta.url),
  'utf8',
);
const pages = [
  { route: '/', html: readFileSync(join(dist, 'index.html'), 'utf8') },
  {
    route: '/book-en/chapter1/',
    html: readFileSync(join(dist, 'book-en/chapter1/index.html'), 'utf8'),
  },
];
const editions = [
  {
    lang: 'en',
    directory: 'book-en',
    suffix: '',
    home: '/',
    chapter: '/book-en/chapter1/',
  },
  {
    lang: 'zh-CN',
    directory: 'book',
    suffix: '',
    home: '/zh-CN/',
    chapter: '/book/chapter1/',
  },
  {
    lang: 'zh-TW',
    directory: 'book-zhtw',
    suffix: '.zhtw',
    home: '/zh-TW/',
    chapter: '/book-zhtw/chapter1.zhtw/',
  },
];
for (const edition of editions.slice(1)) {
  for (const route of [edition.home, edition.chapter]) {
    pages.push({
      route,
      html: readFileSync(join(dist, route, 'index.html'), 'utf8'),
    });
  }
}
const chapter = pages[1].html;
const article = chapter.match(/<article\b[^>]*>([\s\S]*?)<\/article>/)?.[1];
assert.ok(article, 'The complete chapter must be rendered in an article.');
const count = (html, tag) =>
  [...html.matchAll(new RegExp(`<${tag}\\b`, 'g'))].length;
const ids = (html) =>
  new Set([...html.matchAll(/\bid="([^"]+)"/g)].map((match) => match[1]));

test('Chapter 1 retains its sections, code, tables, figures, and footnotes', () => {
  assert.equal(count(chapter, 'h1'), 1);
  for (const level of [2, 3, 4]) {
    const headings = [...source.matchAll(new RegExp(`^#{${level}}\\s+`, 'gm'))]
      .length;
    // The renderer adds one h2 for the footnotes section.
    assert.equal(count(article, `h${level}`), headings + (level === 2 ? 1 : 0));
  }
  assert.equal(count(article, 'pre'), 4);
  assert.equal(count(article, 'table'), 5);
  assert.equal(count(article, 'figure'), 7);
  assert.equal(count(article, 'figcaption'), 7);
  const footnotes = [...source.matchAll(/^\s*(?:>\s*)?\[\^([^\]]+)\]:/gm)].map(
    (match) => match[1],
  );
  assert.equal(footnotes.length, 7);
  for (const note of footnotes)
    assert.ok(
      ids(article).has(`user-content-fn-${note}`),
      `Missing footnote ${note}`,
    );
  assert.match(article, /Thought Questions/);
  assert.match(article, /Contextual adaptation/);
});

test('All six generated pages resolve local assets, links, and fragments', () => {
  for (const page of pages) {
    const pageIds = [...page.html.matchAll(/\bid="([^"]+)"/g)].map(
      (match) => match[1],
    );
    assert.equal(
      new Set(pageIds).size,
      pageIds.length,
      `Duplicate IDs on ${page.route}`,
    );
    for (const [, ref] of page.html.matchAll(/\b(?:href|src)="([^"]+)"/g)) {
      const url = new URL(ref, `https://preview.example${page.route}`);
      if (url.origin !== 'https://preview.example') continue;
      const path = join(
        dist,
        decodeURIComponent(url.pathname),
        url.pathname.endsWith('/') ? 'index.html' : '',
      );
      assert.ok(
        existsSync(path),
        `Missing local asset or route: ${ref} on ${page.route}`,
      );
      if (url.hash && path.endsWith('.html')) {
        assert.ok(
          ids(readFileSync(path, 'utf8')).has(
            decodeURIComponent(url.hash.slice(1)),
          ),
          `Missing fragment: ${ref}`,
        );
      }
    }
  }
});

test('Every chapter figure is copied unchanged from the original book', () => {
  const images = [...source.matchAll(/!\[[^\]]*\]\((images\/[^)]+)\)/g)].map(
    (match) => match[1],
  );
  for (const image of images) {
    const original = readFileSync(
      new URL(`../../book-en/${image}`, import.meta.url),
    );
    const copied = readFileSync(join(dist, 'book-en', image));
    assert.deepEqual(copied, original, `Figure changed: ${image}`);
  }
});

test('Each edition renders its original content, figures, language links, and note scope', () => {
  for (const edition of editions) {
    const homepage = pages.find((page) => page.route === edition.home).html;
    const reader = pages.find((page) => page.route === edition.chapter).html;
    const source = readFileSync(
      new URL(
        `../../${edition.directory}/chapter1${edition.suffix}.md`,
        import.meta.url,
      ),
      'utf8',
    );
    const article = reader.match(/<article\b[^>]*>([\s\S]*?)<\/article>/)?.[1];
    assert.ok(article);
    assert.equal(count(reader, 'h1'), 1);
    assert.ok(reader.includes(source.match(/^#\s+(.+)$/m)[1]));
    for (const level of [2, 3, 4]) {
      const headings = [
        ...source.matchAll(new RegExp(`^#{${level}}\\s+`, 'gm')),
      ].length;
      assert.equal(
        count(article, `h${level}`),
        headings + (level === 2 ? 1 : 0),
      );
    }
    assert.equal(count(article, 'figure'), 7);
    assert.equal(count(article, 'table'), 5);
    assert.equal(count(article, 'pre'), 4);
    assert.ok(
      reader.includes(
        `data-chapter-key="ai-agents-in-depth:${edition.lang}:chapter1"`,
      ),
    );
    assert.ok(reader.includes(`href="${edition.home}#contents"`));
    assert.ok(
      reader.includes(
        `https://bojieli.github.io/ai-agent-book/${edition.directory}/chapter2${edition.suffix}/`,
      ),
    );
    for (const [html, kind] of [
      [homepage, 'home'],
      [reader, 'chapter'],
    ]) {
      assert.ok(html.includes(`lang="${edition.lang}"`));
      const picker = html.match(
        /<details class="language-picker"[\s\S]*?<\/details>/,
      )?.[0];
      assert.ok(picker);
      for (const target of editions)
        assert.ok(picker.includes(`href="${target[kind]}"`));
      if (edition.lang !== 'en') {
        assert.ok(!html.includes('>My highlights<'));
        assert.ok(!html.includes('>Text size<'));
        assert.ok(!html.includes('>Start reading'));
      }
    }
    for (const [, image] of source.matchAll(
      /!\[[^\]]*\]\((images\/[^)]+)\)/g,
    )) {
      assert.ok(article.includes(`src="/${edition.directory}/${image}"`));
      assert.deepEqual(
        readFileSync(join(dist, edition.directory, image)),
        readFileSync(
          new URL(`../../${edition.directory}/${image}`, import.meta.url),
        ),
      );
    }
  }
});

test('Chinese footnotes keep separate citation URLs and translated navigation', () => {
  for (const edition of editions.slice(1)) {
    const html = pages.find((page) => page.route === edition.chapter).html;
    assert.ok(!html.includes('>Footnotes<'));
    assert.ok(!html.includes('aria-label="Back to reference'));
    assert.ok(html.includes(edition.lang === 'zh-CN' ? '>注释<' : '>註釋<'));
    for (const [, href] of html.matchAll(/href="([^"]+)"/g)) {
      assert.ok(
        !decodeURI(href).match(/、https?:\/\/|。$/),
        `Merged or punctuated citation: ${href}`,
      );
    }
    for (const url of [
      'https://manus.im/blog/manus-sandbox',
      'https://manus.im/blog/manus-google-drive-connector',
      'https://manus.im/blog/manus-my-computer-desktop',
      'https://github.com/openclaw/openclaw',
      'https://docs.openclaw.ai/tools',
      'https://adk.dev/workflows/',
    ])
      assert.ok(html.includes(`href="${url}"`));
  }
});
