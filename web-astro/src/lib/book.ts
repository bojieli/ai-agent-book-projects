const chapterSources = import.meta.glob<string>(
  '../../../book-en/chapter*.md',
  {
    query: '?raw',
    import: 'default',
    eager: true,
  },
);

export const repo = 'https://github.com/bojieli/ai-agent-book';
export const originalSite = 'https://bojieli.github.io/ai-agent-book';
export const chapterPath = '/book-en/chapter1/';
const descriptions = [
  'The model, the context, the tools—and the loop that brings them together.',
  'Build the working context that makes an agent effective.',
  'Connect agents to what they know and what they remember.',
  'Give agents reliable interfaces to act on the world.',
  'Use code as a tool for creating new capabilities.',
  'Extend agents across voice, vision, interfaces, and time.',
  'Measure behavior, compare systems, and learn from failures.',
  'Understand how supervised learning and reinforcement learning shape models.',
  'Turn execution experience into lasting improvements.',
  'Coordinate agents, share context, and divide complex work.',
];
export const chapters = Array.from({ length: 10 }, (_, index) => {
  const number = index + 1;
  const source = chapterSources[`../../../book-en/chapter${number}.md`];
  const title = source.match(/^#\s+(.+)$/m)?.[1] ?? `Chapter ${number}`;
  return {
    number,
    label: String(number).padStart(2, '0'),
    title,
    description: descriptions[index],
    href:
      number === 1 ? chapterPath : `${originalSite}/book-en/chapter${number}/`,
    external: number !== 1,
  };
});
const firstChapter = chapterSources['../../../book-en/chapter1.md'];
export const readingMinutes = Math.ceil(firstChapter.split(/\s+/).length / 220);
