export const chapterKey = 'ai-agents-in-depth:en:chapter1';
export interface Annotation {
  id: string;
  chapter: string;
  quote: string;
  prefix: string;
  suffix: string;
  start: number;
  end: number;
  createdAt: string;
  note?: string;
  noteDraft?: string;
}

export function anchor(
  text: string,
  item: Annotation,
): { start: number; end: number } | null {
  const matches: number[] = [];
  let index = text.indexOf(item.quote);
  while (index !== -1) {
    matches.push(index);
    index = text.indexOf(item.quote, index + 1);
  }
  // Nearby text disambiguates repeated phrases; never silently choose a different occurrence.
  const contextual = matches.filter(
    (start) =>
      text.slice(0, start).endsWith(item.prefix) &&
      text.slice(start + item.quote.length).startsWith(item.suffix),
  );
  const start =
    contextual.length === 1
      ? contextual[0]
      : matches.length === 1
        ? matches[0]
        : undefined;
  return start === undefined ? null : { start, end: start + item.quote.length };
}

export function parseBackup(
  value: unknown,
  expectedChapter = chapterKey,
): Annotation[] {
  const data = value as {
    format?: unknown;
    version?: unknown;
    highlights?: unknown;
  } | null;
  if (
    !data ||
    data.format !== 'ai-agent-book-highlights' ||
    (data.version !== 1 && data.version !== 2) ||
    !Array.isArray(data.highlights)
  ) {
    throw new Error('Choose a highlights backup exported from this book.');
  }
  return data.highlights.map((item: unknown) => {
    const a = item as Annotation | null;
    if (
      !a ||
      typeof a.id !== 'string' ||
      !a.id.length ||
      a.id.length > 100 ||
      a.chapter !== expectedChapter ||
      typeof a.quote !== 'string' ||
      !a.quote.trim() ||
      a.quote.length > 10000 ||
      typeof a.prefix !== 'string' ||
      a.prefix.length > 64 ||
      typeof a.suffix !== 'string' ||
      a.suffix.length > 64 ||
      !Number.isSafeInteger(a.start) ||
      a.start < 0 ||
      !Number.isSafeInteger(a.end) ||
      a.end - a.start !== a.quote.length ||
      typeof a.createdAt !== 'string' ||
      !Number.isFinite(Date.parse(a.createdAt)) ||
      (a.note !== undefined &&
        (typeof a.note !== 'string' || a.note.length > 10000)) ||
      (a.noteDraft !== undefined &&
        (typeof a.noteDraft !== 'string' || a.noteDraft.length > 10000))
    ) {
      throw new Error(
        'This backup contains an invalid highlight or a different chapter. Nothing was imported.',
      );
    }
    return {
      id: a.id,
      chapter: a.chapter,
      quote: a.quote,
      prefix: a.prefix,
      suffix: a.suffix,
      start: a.start,
      end: a.end,
      createdAt: a.createdAt,
      ...(a.note !== undefined ? { note: a.note } : {}),
      ...(a.noteDraft !== undefined ? { noteDraft: a.noteDraft } : {}),
    };
  });
}

export function samePassage(a: Annotation, b: Annotation) {
  return (
    a.chapter === b.chapter &&
    a.quote === b.quote &&
    a.prefix === b.prefix &&
    a.suffix === b.suffix
  );
}

// Enrich empty highlights, but keep conflicting notes as separate entries instead of overwriting either.
export function mergeBackup(
  existing: Annotation[],
  imported: Annotation[],
  makeId: () => string,
): Annotation[] {
  const all = [...existing];
  const changes = new Map<string, Annotation>();
  for (const item of imported) {
    const matches = all.filter((record) => samePassage(record, item));
    if (
      matches.some(
        (record) =>
          (record.note ?? '') === (item.note ?? '') &&
          record.noteDraft === item.noteDraft,
      )
    )
      continue;
    if (matches.length && !item.note && item.noteDraft === undefined) continue;
    const empty = matches.find(
      (record) => !record.note && record.noteDraft === undefined,
    );
    const merged = { ...item, id: empty?.id ?? makeId() };
    if (empty) all.splice(all.indexOf(empty), 1, merged);
    else all.push(merged);
    changes.set(merged.id, merged);
  }
  return [...changes.values()];
}
