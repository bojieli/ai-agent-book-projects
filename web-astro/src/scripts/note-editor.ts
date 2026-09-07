import type { Annotation } from '../lib/annotations';
import { readHighlights, updateNote } from '../lib/highlight-store';

export function createNoteEditor(
  db: IDBDatabase,
  refresh: () => Promise<void>,
  notify: (message: string) => void,
) {
  const get = <T extends HTMLElement>(id: string) =>
    document.getElementById(id) as T;
  const dialog = get<HTMLDialogElement>('note-dialog');
  const listDialog = get<HTMLDialogElement>('highlights-dialog');
  const text = get<HTMLTextAreaElement>('note-text');
  const status = get('note-draft-status');
  const save = get<HTMLButtonElement>('save-note');
  const discard = get<HTMLButtonElement>('discard-note-draft');
  const close = get<HTMLButtonElement>('close-note');
  const cache = new Map<string, { value: string }>();
  let editing: Annotation | undefined;
  let writes: Promise<void> = Promise.resolve();
  let pendingWrites = 0;
  const failedDrafts = new Set<string>();
  let saving = false;
  let returnToList = false;

  function draft(value: string) {
    if (!editing) return;
    const record = editing;
    const snapshot = { value };
    cache.set(record.id, snapshot);
    const noteDraft = value === (record.note ?? '') ? undefined : value;
    pendingWrites++;
    status.textContent = 'Saving draft…';
    writes = writes.then(async () => {
      try {
        await updateNote(db, record.id, { noteDraft });
        failedDrafts.delete(record.id);
        if (cache.get(record.id) === snapshot) cache.delete(record.id);
        if (editing?.id === record.id)
          status.textContent =
            'Draft saved in this browser. Choose Save note when you’re ready.';
      } catch {
        failedDrafts.add(record.id);
        status.textContent =
          'Draft could not be saved. Keep this page open and copy your text before leaving.';
      } finally {
        pendingWrites--;
      }
    });
  }
  text.addEventListener('input', () => draft(text.value));
  close.addEventListener('click', () => {
    if (!saving) dialog.close();
  });
  dialog.addEventListener('cancel', (event) => {
    if (saving) event.preventDefault();
  });
  dialog.addEventListener('close', async () => {
    editing = undefined;
    const reopen = returnToList;
    await writes;
    try {
      await refresh();
    } catch {
      notify(
        'Could not refresh your highlights. Please reload when your draft is saved.',
      );
    }
    if (!dialog.open) {
      if (reopen) {
        listDialog.showModal();
        get('close-highlights').focus();
      } else get('open-highlights').focus({ preventScroll: true });
      if (failedDrafts.size)
        notify(
          'Your draft is still in this tab, but browser storage failed. Reopen the note and copy it before leaving.',
        );
    }
  });
  async function commit(discardDraft: boolean) {
    if (!editing || saving) return;
    const record = editing;
    const value = text.value;
    saving = true;
    text.disabled = true;
    save.disabled = true;
    discard.disabled = true;
    close.disabled = true;
    await writes;
    try {
      await updateNote(
        db,
        record.id,
        discardDraft
          ? { noteDraft: undefined }
          : { note: value, noteDraft: undefined },
      );
      cache.delete(record.id);
      failedDrafts.delete(record.id);
      if (discardDraft) {
        text.value = record.note ?? '';
        status.textContent = 'Draft discarded. Your saved note is unchanged.';
      } else {
        dialog.close();
        notify(
          value
            ? 'Note saved in this browser.'
            : 'Note removed. The highlight is kept.',
        );
      }
    } catch {
      status.textContent =
        'Could not save this change. Your text is still here; copy it before leaving.';
    } finally {
      saving = false;
      text.disabled = false;
      save.disabled = false;
      discard.disabled = false;
      close.disabled = false;
    }
  }
  save.addEventListener('click', () => commit(false));
  discard.addEventListener('click', () => commit(true));
  // Only guard navigation while a write is unfinished or failed, not for a successfully stored draft.
  window.addEventListener('beforeunload', (event) => {
    if (pendingWrites || failedDrafts.size || saving) {
      event.preventDefault();
    }
  });
  return {
    isOpen: () => dialog.open,
    async open(record: Annotation) {
      await writes;
      try {
        const current = (await readHighlights(db)).find(
          (item) => item.id === record.id,
        );
        if (!current) {
          notify(
            'This highlight was removed. Select the passage again to add a note.',
          );
          return;
        }
        editing = current;
        returnToList = listDialog.open;
        if (returnToList) listDialog.close();
        get('note-title').textContent = current.note ? 'Edit note' : 'Add note';
        get('note-quote').textContent = current.quote;
        text.value =
          cache.get(current.id)?.value ??
          current.noteDraft ??
          current.note ??
          '';
        const recovered = text.value !== (current.note ?? '');
        status.textContent = recovered
          ? 'Draft restored. Choose Save note when you’re ready.'
          : 'Drafts stay in this browser. Choose Save note when you’re ready.';
        dialog.showModal();
        text.focus();
      } catch {
        notify('Could not open the note. Please try again.');
      }
    },
  };
}
