import { IExtraField } from '../../../types/template';
import { IFieldsetRuntime } from '../../../types/fieldset';

type TStorageEntry<T, TMetadata> = {
  taskId: number;
  data: T;
  metadata?: TMetadata;
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
        throw new Error('no saved data');
      }

      const savedData = JSON.parse(savedDataString) as TStorageEntry<T, TMetadata>[];

      if (!Array.isArray(savedData)) {
        throw new Error('saved data is invalid');
      }

      return savedData;
    } catch (error) {
      return [];
    }
  }

  function saveAll(entries: TStorageEntry<T, TMetadata>[]) {
    const dataJSON = JSON.stringify(entries);

    localStorage.setItem(storageKey, dataJSON);
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
      const newEntries = getAll().filter(entry => entry.taskId !== taskId);
      saveAll(newEntries);
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