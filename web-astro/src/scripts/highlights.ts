import { createNoteEditor } from './note-editor';
import {
  anchor,
  chapterKey,
  parseBackup,
  samePassage,
  type Annotation,
} from '../lib/annotations';
import {
  openHighlights,
  importHighlights,
  readHighlights,
  writeHighlights,
} from '../lib/highlight-store';

export async function initHighlights() {
  const article = document.querySelector<HTMLElement>('#chapter-content');
  if (!article) return;
  const content = article;
  const element = <T extends HTMLElement>(id: string) =>
    document.getElementById(id) as T;
  const toggle = element<HTMLButtonElement>('open-highlights');
  const dialog = element<HTMLDialogElement>('highlights-dialog');
  const toolbar = element<HTMLDivElement>('highlight-selection');
  const save = element<HTMLButtonElement>('save-highlight');
  const list = element<HTMLOListElement>('highlights-list');
  const status = element<HTMLParagraphElement>('highlight-status');
  const dialogStatus = element<HTMLParagraphElement>('highlight-dialog-status');
  const exportButton = element<HTMLButtonElement>('export-highlights');
  const importInput = element<HTMLInputElement>('import-highlights');
  const excluded = 'pre, figure, button, script, style, .footnotes';
  let db: IDBDatabase | undefined;
  let records: Annotation[] = [];
  let noteEditor: ReturnType<typeof createNoteEditor> | undefined;
  let pending: Annotation | null = null;
  let busy = false;
  let selectionHandedOff = false;
  let messageTimer = 0;
  const notify = (message: string) => {
    if (dialog.open) dialogStatus.textContent = message;
    else {
      status.textContent = message;
      clearTimeout(messageTimer);
      messageTimer = window.setTimeout(() => {
        status.textContent = '';
      }, 6000);
    }
  };
  const hideSelection = () => {
    toolbar.hidden = true;
    pending = null;
  };
  function textMap() {
    const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) =>
        node.parentElement?.closest(excluded)
          ? NodeFilter.FILTER_REJECT
          : NodeFilter.FILTER_ACCEPT,
    });
    let text = '';
    const nodes: { node: Text; start: number; end: number }[] = [];
    let current: Node | null;
    while ((current = walker.nextNode())) {
      const node = current as Text;
      nodes.push({ node, start: text.length, end: text.length + node.length });
      text += node.data;
    }
    return { text, nodes };
  }
  function openNote(record: Annotation) {
    hideSelection();
    getSelection()?.removeAllRanges();
    void noteEditor?.open(record);
  }
  function render() {
    content
      .querySelectorAll('mark.reader-highlight')
      .forEach((mark) => mark.replaceWith(...mark.childNodes));
    content.normalize();
    const map = textMap();
    const located = records.map((record) => ({
      record,
      position: anchor(map.text, record),
    }));
    // Split text nodes without disturbing links or inline emphasis; overlaps share one visible mark.
    for (const entry of map.nodes) {
      const intervals = located.flatMap(({ position }) =>
        position && position.start < entry.end && position.end > entry.start
          ? [
              {
                start: Math.max(0, position.start - entry.start),
                end: Math.min(entry.node.length, position.end - entry.start),
              },
            ]
          : [],
      );
      if (!intervals.length) continue;
      const cuts = [
        ...new Set([
          0,
          entry.node.length,
          ...intervals.flatMap((i) => [i.start, i.end]),
        ]),
      ].sort((a, b) => a - b);
      const fragment = document.createDocumentFragment();
      for (let i = 0; i < cuts.length - 1; i++) {
        const text = document.createTextNode(
          entry.node.data.slice(cuts[i], cuts[i + 1]),
        );
        if (
          intervals.some(
            (interval) =>
              interval.start <= cuts[i] && interval.end >= cuts[i + 1],
          )
        ) {
          const mark = document.createElement('mark');
          mark.className = 'reader-highlight';
          const covering = located.filter(
            ({ position }) =>
              position &&
              position.start <= entry.start + cuts[i] &&
              position.end >= entry.start + cuts[i + 1],
          );
          mark.dataset.highlightIds = covering
            .map(({ record }) => record.id)
            .join(' ');
          const first = covering.find(
            ({ position }) => position?.start === entry.start + cuts[i],
          );
          mark.title = covering.some(({ record }) => record.note)
            ? 'Edit note'
            : 'Add note';
          if (first && !entry.node.parentElement?.closest('a')) {
            mark.tabIndex = 0;
            mark.setAttribute('role', 'button');
            mark.setAttribute('aria-haspopup', 'dialog');
            mark.setAttribute(
              'aria-label',
              `${mark.title}: ${first.record.quote.slice(0, 80)}`,
            );
          }
          if (
            covering.some(
              ({ record, position }) =>
                position?.start === entry.start + cuts[i] &&
                (record.note || record.noteDraft !== undefined),
            )
          )
            mark.classList.add('has-note');
          mark.append(text);
          fragment.append(mark);
        } else fragment.append(text);
      }
      entry.node.replaceWith(fragment);
    }
    element('highlight-count').textContent = String(records.length);
    element('highlights-empty').hidden = records.length > 0;
    exportButton.disabled = records.length === 0;
    list.replaceChildren();
    for (const { record, position } of located) {
      const li = document.createElement('li');
      const quote = document.createElement('blockquote');
      quote.textContent = record.quote;
      li.append(quote);
      if (record.note) {
        const note = document.createElement('p');
        note.className = 'saved-note';
        note.textContent = record.note;
        li.append(note);
      }
      if (record.noteDraft !== undefined) {
        const draftLabel = document.createElement('p');
        draftLabel.className = 'note-draft-label';
        draftLabel.textContent = 'Unfinished draft';
        li.append(draftLabel);
      }
      if (!position) {
        const message = document.createElement('p');
        message.className = 'unmatched';
        message.textContent =
          'Passage changed or could not be matched. Your saved quote is preserved.';
        li.append(message);
      }
      const actions = document.createElement('div');
      actions.className = 'highlight-actions';
      const jump = document.createElement('button');
      jump.type = 'button';
      jump.textContent = 'Go to passage';
      jump.disabled = !position;
      jump.addEventListener('click', () => {
        const current = textMap();
        const match = anchor(current.text, record);
        if (!match) return;
        const entry = current.nodes.find(
          (n) => n.start <= match.start && n.end > match.start,
        );
        const target = entry?.node.parentElement;
        if (!target) return;
        dialog.close();
        target.scrollIntoView({
          block: 'center',
          behavior: matchMedia('(prefers-reduced-motion: reduce)').matches
            ? 'instant'
            : 'smooth',
        });
        const hadTabindex = target.getAttribute('tabindex');
        target.tabIndex = -1;
        target.focus({ preventScroll: true });
        target.addEventListener(
          'blur',
          () =>
            hadTabindex === null
              ? target.removeAttribute('tabindex')
              : target.setAttribute('tabindex', hadTabindex),
          { once: true },
        );
      });
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.textContent = 'Remove';
      remove.setAttribute(
        'aria-label',
        `Remove highlight: ${record.quote.slice(0, 60)}`,
      );
      remove.addEventListener('click', async () => {
        const rowIndex = [...list.children].indexOf(li);
        await mutate(
          () => writeHighlights(db!, [], record.id),
          'Highlight removed.',
        );
        const nextRow =
          list.children[Math.min(rowIndex, list.children.length - 1)];
        (
          nextRow?.querySelector('button') ??
          element<HTMLButtonElement>('close-highlights')
        ).focus();
      });
      const edit = document.createElement('button');
      edit.type = 'button';
      edit.textContent =
        record.noteDraft !== undefined
          ? 'Resume draft'
          : record.note
            ? 'Edit note'
            : 'Add note';
      edit.addEventListener('click', () => openNote(record));
      actions.append(jump, edit, remove);
      li.append(actions);
      list.append(li);
    }
  }
  async function refresh() {
    if (!db) return;
    records = (await readHighlights(db)).sort((a, b) =>
      a.createdAt.localeCompare(b.createdAt),
    );
    render();
  }
  async function mutate(action: () => Promise<void>, message: string) {
    if (busy || !db) return;
    busy = true;
    save.disabled = true;
    try {
      await action();
      hideSelection();
      getSelection()?.removeAllRanges();
      await refresh();
      notify(message);
    } catch {
      notify(
        'Could not save this change. Browser storage may be unavailable or full. Please try again.',
      );
    } finally {
      busy = false;
      save.disabled = false;
    }
  }
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    hideSelection();
    dialogStatus.textContent = db
      ? ''
      : 'Highlight storage is unavailable. Allow site storage and reload to try again.';
    dialog.showModal();
  });
  element('close-highlights').addEventListener('click', () => dialog.close());
  exportButton.disabled = true;
  importInput.disabled = true;
  try {
    db = await openHighlights();
    await refresh();
    noteEditor = createNoteEditor(db, refresh, notify);
    importInput.disabled = false;
  } catch {
    db = undefined;
    notify(
      'Highlights could not load. Allow browser storage and reload to try again.',
    );
    return;
  }

  document.addEventListener('selectionchange', () => {
    if (
      busy ||
      dialog.open ||
      noteEditor?.isOpen() ||
      toolbar.contains(document.activeElement)
    )
      return;
    const selection = getSelection();
    if (!selection?.rangeCount || selection.isCollapsed) {
      hideSelection();
      return;
    }
    const range = selection.getRangeAt(0);
    if (
      !content.contains(range.startContainer) ||
      !content.contains(range.endContainer) ||
      [...content.querySelectorAll(excluded)].some((node) =>
        range.intersectsNode(node),
      )
    ) {
      hideSelection();
      return;
    }
    const map = textMap();
    const selected = map.nodes.filter(({ node }) => range.intersectsNode(node));
    const first = selected[0],
      last = selected.at(-1);
    if (!first || !last) {
      hideSelection();
      return;
    }
    let start =
      first.start +
      (range.startContainer === first.node ? range.startOffset : 0);
    let end =
      last.start +
      (range.endContainer === last.node ? range.endOffset : last.node.length);
    const raw = map.text.slice(start, end);
    start += raw.length - raw.trimStart().length;
    end -= raw.length - raw.trimEnd().length;
    const quote = map.text.slice(start, end);
    if (!quote.trim() || quote.length > 10000) {
      hideSelection();
      return;
    }
    if (!pending || pending.start !== start || pending.end !== end)
      selectionHandedOff = false;
    pending = {
      id: crypto.randomUUID(),
      chapter: chapterKey,
      quote,
      start,
      end,
      prefix: map.text.slice(Math.max(0, start - 64), start),
      suffix: map.text.slice(end, end + 64),
      createdAt: new Date().toISOString(),
    };
    const rect = range.getBoundingClientRect();
    toolbar.hidden = false;
    toolbar.style.left = `${Math.max(12, Math.min(innerWidth - toolbar.offsetWidth - 12, rect.left + rect.width / 2 - toolbar.offsetWidth / 2))}px`;
    toolbar.style.top = `${Math.max(12, Math.min(innerHeight - toolbar.offsetHeight - 12, rect.top > 140 ? rect.top - toolbar.offsetHeight - 10 : rect.bottom + 10))}px`;
  });
  toolbar.addEventListener('pointerdown', (event) => event.preventDefault());
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') hideSelection();
    if (
      event.key === 'Tab' &&
      !event.shiftKey &&
      !selectionHandedOff &&
      pending &&
      !toolbar.hidden &&
      !toolbar.contains(document.activeElement)
    ) {
      event.preventDefault();
      selectionHandedOff = true;
      save.focus();
    }
  });
  window.addEventListener('scroll', hideSelection, { passive: true });
  window.addEventListener('resize', hideSelection);
  save.addEventListener('click', () => {
    const item = pending;
    if (!item) return;
    mutate(async () => {
      const latest = await readHighlights(db!);
      if (
        !latest.some(
          (record) =>
            record.quote === item.quote &&
            record.prefix === item.prefix &&
            record.suffix === item.suffix,
        )
      )
        await writeHighlights(db!, [item]);
    }, 'Highlight saved in this browser.');
  });
  element('add-highlight-note').addEventListener('click', async () => {
    const item = pending;
    if (!item || !db || busy) return;
    let target: Annotation | undefined;
    await mutate(async () => {
      const latest = await readHighlights(db!);
      target = latest.find((record) => samePassage(record, item));
      if (!target) {
        await writeHighlights(db!, [item]);
        target = item;
      }
    }, 'Highlight saved.');
    if (target) openNote(target);
  });
  function activateMark(event: MouseEvent | KeyboardEvent) {
    if (!(event.target instanceof Element) || event.target.closest('a')) return;
    const mark = event.target.closest<HTMLElement>('mark.reader-highlight');
    if (!mark || (event instanceof MouseEvent && getSelection()?.toString()))
      return;
    if (
      event instanceof KeyboardEvent &&
      event.key !== 'Enter' &&
      event.key !== ' '
    )
      return;
    event.preventDefault();
    const ids = mark.dataset.highlightIds?.split(' ') ?? [];
    const matches = records.filter((record) => ids.includes(record.id));
    if (matches.length === 1) openNote(matches[0]);
    else if (matches.length > 1) {
      hideSelection();
      dialog.showModal();
      dialogStatus.textContent =
        'This passage has multiple highlights. Choose Add note or Edit note below.';
    }
  }
  content.addEventListener('click', activateMark);
  content.addEventListener('keydown', activateMark);
  element('copy-highlight-backup').addEventListener('click', async () => {
    const output = element<HTMLTextAreaElement>('highlight-backup-json');
    try {
      await navigator.clipboard.writeText(output.value);
      notify('Backup copied. Save it as a .json file.');
    } catch {
      output.focus();
      output.select();
      notify('Copy the selected backup text and save it as a .json file.');
    }
  });
  exportButton.addEventListener('click', () => {
    try {
      const highlights = records;
      const json = JSON.stringify(
        { format: 'ai-agent-book-highlights', version: 2, highlights },
        null,
        2,
      );
      element<HTMLTextAreaElement>('highlight-backup-json').value = json;
      element('highlight-backup-panel').hidden = false;
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'ai-agent-book-chapter1-highlights.json';
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch {
      notify('Could not export your highlights. Please try again.');
    }
  });
  importInput.addEventListener('change', async () => {
    const file = importInput.files?.[0];
    if (!file) return;
    try {
      const imported = parseBackup(JSON.parse(await file.text()));
      await mutate(async () => {
        await importHighlights(db!, imported);
      }, 'Backup imported. Existing highlights were kept.');
    } catch (error) {
      notify(
        error instanceof Error
          ? error.message
          : 'Could not import this backup.',
      );
    } finally {
      importInput.value = '';
    }
  });
  window.addEventListener('focus', () => {
    if (!busy && !pending && !dialog.open && !noteEditor?.isOpen())
      refresh().catch(() =>
        notify('Could not reload highlights. Please reload the page.'),
      );
  });
}
