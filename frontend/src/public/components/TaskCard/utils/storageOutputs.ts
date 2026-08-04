import { IExtraField } from '../../../types/template';
import { IFieldsetRuntime } from '../../../types/fieldset';

type TStorageEntry<T, TMetadata> = {
  taskId: number;
  data: T;
  metadata?: TMetadata;
};

type TRawStorageEntry<T, TMetadata> = Omit<TStorageEntry<T, TMetadata>, 'data'> & {
  data?: T;
  output?: T;
};

export type TOutputDraftMetadata = {
  dateStarted: string | null;
  fieldFingerprints: Record<string, string>;
};

export type TFieldsetDraftMetadata = {
  dateStarted: string | null;
  fieldFingerprints: Record<string, Record<string, string>>;
};

function createTaskStorage<T, TMetadata>(storageKey: string) {
  function getAll(): TStorageEntry<T, TMetadata>[] {
    try {
      const savedDataString = localStorage.getItem(storageKey);

      if (!savedDataString) {
        return [];
      }

      const savedData = JSON.parse(savedDataString) as TRawStorageEntry<T, TMetadata>[];

      if (!Array.isArray(savedData)) {
        return [];
      }

      return savedData.flatMap(({ taskId, data, output, metadata }) => {
        const entryData = data ?? output;
        return entryData === undefined ? [] : [{ taskId, data: entryData, metadata }];
      });
    } catch {
      return [];
    }
  }

  function saveAll(entries: TStorageEntry<T, TMetadata>[]) {
    if (entries.length === 0) {
      localStorage.removeItem(storageKey);
      return;
    }

    localStorage.setItem(storageKey, JSON.stringify(entries));
  }

  return {
    save(taskId: number, data: T, metadata?: TMetadata) {
      const currentEntry: TStorageEntry<T, TMetadata> = { taskId, data, metadata };
      const savedEntries = getAll();
      const savedEntryIndex = savedEntries.findIndex((entry) => entry.taskId === taskId);

      if (savedEntryIndex === -1) {
        saveAll([...savedEntries, currentEntry]);
        return;
      }

      const newEntries = [...savedEntries];
      newEntries[savedEntryIndex] = currentEntry;
      saveAll(newEntries);
    },

    get(taskId: number): T | undefined {
      return getAll().find((entry) => entry.taskId === taskId)?.data;
    },

    getEntry(taskId: number): TStorageEntry<T, TMetadata> | undefined {
      return getAll().find((entry) => entry.taskId === taskId);
    },

    remove(taskId: number) {
      saveAll(getAll().filter((entry) => entry.taskId !== taskId));
    },

    removeMany(taskIds: number[]) {
      if (taskIds.length === 0) return;

      const taskIdsSet = new Set(taskIds);
      saveAll(getAll().filter((entry) => !taskIdsSet.has(entry.taskId)));
    },
  };
}

export const outputStorage = createTaskStorage<IExtraField[], TOutputDraftMetadata>('tasks_outputs');

export const fieldsetsStorage = createTaskStorage<IFieldsetRuntime[], TFieldsetDraftMetadata>(
  'tasks_fieldsets_outputs',
);

export const addOrUpdateStorageOutput = outputStorage.save;
export const getOutputFromStorage = outputStorage.get;
export const removeOutputFromLocalStorage = outputStorage.remove;
export const removeOutputsFromLocalStorage = outputStorage.removeMany;
