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

test('Both generated pages resolve their local assets, links, and fragments', () => {
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
