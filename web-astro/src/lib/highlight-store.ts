import { chapterKey, mergeBackup, type Annotation } from './annotations';

export function openHighlights(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ai-agent-book-reader', 1);
    request.onupgradeneeded = () => {
      const store = request.result.createObjectStore('highlights', {
        keyPath: 'id',
      });
      store.createIndex('chapter', 'chapter');
    };
    request.onerror = () => reject(request.error);
    request.onblocked = () =>
      reject(
        new Error('Close other book tabs and reload to enable highlights.'),
      );
    request.onsuccess = () => {
      const db = request.result;
      db.onversionchange = () => db.close();
      resolve(db);
    };
  });
}

export function readHighlights(db: IDBDatabase): Promise<Annotation[]> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('highlights', 'readonly');
    const request = tx
      .objectStore('highlights')
      .index('chapter')
      .getAll(chapterKey);
    tx.oncomplete = () => resolve(request.result);
    tx.onabort = () => reject(tx.error);
    tx.onerror = () => reject(tx.error);
  });
}

// Report saved only after the whole transaction commits, including batch imports.
export function writeHighlights(
  db: IDBDatabase,
  items: Annotation[],
  remove?: string,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('highlights', 'readwrite');
    const store = tx.objectStore('highlights');
    for (const item of items) store.put(item);
    if (remove) store.delete(remove);
    tx.oncomplete = () => resolve();
    tx.onabort = () => reject(tx.error);
    tx.onerror = () => reject(tx.error);
  });
}

// Read and patch in one transaction so a note edit cannot overwrite unrelated annotation fields.
export function updateNote(
  db: IDBDatabase,
  id: string,
  patch: Pick<Annotation, 'note' | 'noteDraft'>,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('highlights', 'readwrite');
    const store = tx.objectStore('highlights');
    const request = store.get(id);
    request.onsuccess = () => {
      if (!request.result) {
        tx.abort();
        return;
      }
      store.put({ ...request.result, ...patch });
    };
    tx.oncomplete = () => resolve();
    tx.onabort = () =>
      reject(tx.error ?? new Error('This highlight no longer exists.'));
    tx.onerror = () => reject(tx.error);
  });
}

export function importHighlights(
  db: IDBDatabase,
  imported: Annotation[],
): Promise<void> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('highlights', 'readwrite');
    const store = tx.objectStore('highlights');
    const request = store.index('chapter').getAll(chapterKey);
    request.onsuccess = () => {
      for (const record of mergeBackup(request.result, imported, () =>
        crypto.randomUUID(),
      ))
        store.put(record);
    };
    tx.oncomplete = () => resolve();
    tx.onabort = () => reject(tx.error);
    tx.onerror = () => reject(tx.error);
  });
}
