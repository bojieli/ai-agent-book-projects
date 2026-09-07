import assert from 'node:assert/strict';
import test from 'node:test';
import {
  anchor,
  chapterKey,
  parseBackup,
  mergeBackup,
} from '../src/lib/annotations.ts';
const item = {
  id: 'test',
  chapter: chapterKey,
  quote: 'the model',
  prefix: 'Ask ',
  suffix: ' to act.',
  start: 4,
  end: 13,
  createdAt: '2026-09-07T00:00:00Z',
};
test('quotes survive insertions before their original location', () => {
  assert.deepEqual(anchor('New introduction. Ask the model to act.', item), {
    start: 22,
    end: 31,
  });
});
test('context selects the right repeated quote, ambiguous or deleted quotes stay unmatched', () => {
  assert.deepEqual(anchor('Use the model. Ask the model to act.', item), {
    start: 19,
    end: 28,
  });
  assert.equal(anchor('the model or the model', item), null);
  assert.equal(anchor('Ask a tool to act.', item), null);
});
test('unique quotes survive nearby edits', () => {
  assert.deepEqual(anchor('Tell the model to answer.', item), {
    start: 5,
    end: 14,
  });
});
test('backup validates all records before import and strips unrecognized fields', () => {
  const backup = (highlights) => ({
    format: 'ai-agent-book-highlights',
    version: 1,
    highlights,
  });
  assert.deepEqual(
    parseBackup(backup([{ ...item, html: '<script>bad</script>' }])),
    [item],
  );
  for (const invalid of [
    { ...item, chapter: 'other-book' },
    { ...item, quote: '' },
    { ...item, end: 99 },
    { ...item, start: -1 },
    { ...item, prefix: 'x'.repeat(65) },
    { ...item, createdAt: 'invalid' },
  ]) {
    assert.throws(() => parseBackup(backup([item, invalid])));
  }
  assert.throws(() => parseBackup({ ...backup([item]), version: 3 }));
  assert.equal(parseBackup(backup(Array(2001).fill(item))).length, 2001);
});

test('note backups preserve saved text and empty drafts; old highlights still import', () => {
  const note = {
    ...item,
    note: '<b>Plain text</b>\nTry this next.',
    noteDraft: '',
  };
  assert.deepEqual(
    parseBackup({
      format: 'ai-agent-book-highlights',
      version: 2,
      highlights: [note],
    }),
    [note],
  );
  for (const invalid of [
    { ...item, note: 7 },
    { ...item, noteDraft: null },
    { ...item, note: 'x'.repeat(10001) },
  ]) {
    assert.throws(() =>
      parseBackup({
        format: 'ai-agent-book-highlights',
        version: 2,
        highlights: [invalid],
      }),
    );
  }
});
test('imports enrich bare highlights without losing notes or drafts', () => {
  const note = { ...item, id: 'import', note: 'Remember this' };
  assert.deepEqual(
    mergeBackup([item], [note], () => 'new'),
    [{ ...note, id: item.id }],
  );
  assert.deepEqual(
    mergeBackup([note], [item], () => 'new'),
    [],
  );
  assert.deepEqual(
    mergeBackup([note], [note], () => 'new'),
    [],
  );
  const different = { ...note, note: 'Another idea' };
  assert.deepEqual(
    mergeBackup([note], [different], () => 'new'),
    [{ ...different, id: 'new' }],
  );
  const draft = { ...item, noteDraft: '' };
  assert.deepEqual(
    mergeBackup([draft], [note], () => 'new'),
    [{ ...note, id: 'new' }],
  );
  assert.deepEqual(
    mergeBackup([], [item, note, note], () => 'new'),
    [{ ...note, id: 'new' }],
  );
});

test('edition backups reject other languages and never merge identical text across editions', () => {
  const chinese = {
    ...item,
    id: 'zh-note',
    chapter: 'ai-agents-in-depth:zh-CN:chapter1',
    note: '中文笔记',
  };
  const backup = {
    format: 'ai-agent-book-highlights',
    version: 2,
    highlights: [chinese],
  };
  assert.deepEqual(parseBackup(backup, chinese.chapter), [chinese]);
  assert.throws(() => parseBackup(backup), /different chapter/);
  assert.throws(
    () => parseBackup(backup, 'ai-agents-in-depth:zh-TW:chapter1'),
    /different chapter/,
  );
  const merged = mergeBackup([item], [chinese], () => 'new-id');
  assert.equal(merged.length, 1);
  assert.equal(merged[0].id, 'new-id');
  assert.equal(merged[0].chapter, chinese.chapter);
  assert.equal(merged[0].note, '中文笔记');
});
