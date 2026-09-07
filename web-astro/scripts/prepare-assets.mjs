import { readFile, mkdir, copyFile } from 'node:fs/promises';
const root = new URL('../../', import.meta.url);
let count = 0;
for (const [directory, suffix] of [
  ['book-en', ''],
  ['book', ''],
  ['book-zhtw', '.zhtw'],
]) {
  const markdown = await readFile(
    new URL(`${directory}/chapter1${suffix}.md`, root),
    'utf8',
  );
  const images = new Set(
    [...markdown.matchAll(/!\[[^\]]*\]\((images\/[^)]+)\)/g)].map(
      (match) => match[1],
    ),
  );
  for (const image of images) {
    const destination = new URL(
      `../public/${directory}/${image}`,
      import.meta.url,
    );
    await mkdir(new URL('./', destination), { recursive: true });
    await copyFile(new URL(`${directory}/${image}`, root), destination);
    count++;
  }
}
console.log(`Prepared ${count} chapter figures from the original sources.`);
