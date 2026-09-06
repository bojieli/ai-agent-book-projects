import { readFile, mkdir, copyFile } from 'node:fs/promises';

const root = new URL('../../', import.meta.url);
const markdown = await readFile(new URL('book-en/chapter1.md', root), 'utf8');
const images = new Set(
  [...markdown.matchAll(/!\[[^\]]*\]\((images\/[^)]+)\)/g)].map(
    (match) => match[1],
  ),
);
for (const image of images) {
  const destination = new URL(`../public/book-en/${image}`, import.meta.url);
  await mkdir(new URL('./', destination), { recursive: true });
  await copyFile(new URL(`book-en/${image}`, root), destination);
}
console.log(
  `Prepared ${images.size} chapter figures from the original sources.`,
);
