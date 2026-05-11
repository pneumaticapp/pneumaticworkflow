/* eslint-disable */
/* prettier-ignore */
import { IExtraField, IFieldsetData } from '../../../types/template';

type TStorageEntry<T> = {
  taskId: number;
  data: T;
};

function createTaskStorage<T>(storageKey: string) {
  function getAll(): TStorageEntry<T>[] {
    try {
      const savedDataString = localStorage.getItem(storageKey);

      if (!savedDataString) {
        throw new Error('no saved data');
      }

      const savedData = JSON.parse(savedDataString) as TStorageEntry<T>[];

      if (!Array.isArray(savedData)) {
        throw new Error('saved data is invalid');
      }

      return savedData;
    } catch (error) {
      return [];
    }
  }

  function saveAll(entries: TStorageEntry<T>[]) {
    const dataJSON = JSON.stringify(entries);

    localStorage.setItem(storageKey, dataJSON);
  }

  return {
    save(taskId: number, data: T) {
      const currentEntry: TStorageEntry<T> = { taskId, data };
      const savedEntries = getAll();
      const savedEntryIndex = savedEntries.findIndex(entry => entry.taskId === taskId);

      if (savedEntryIndex === -1) {
        saveAll([...savedEntries, currentEntry]);

        return;
      }

      const newEntries = [...savedEntries];
      newEntries[savedEntryIndex] = currentEntry;
      saveAll(newEntries);
    },

    get(taskId: number): T | undefined {
      return getAll().find(entry => entry.taskId === taskId)?.data;
    },

    remove(taskId: number) {
      const newEntries = getAll().filter(entry => entry.taskId !== taskId);
      saveAll(newEntries);
    },
  };
}

export const outputStorage = createTaskStorage<IExtraField[]>('tasks_outputs');

export const fieldsetsStorage = createTaskStorage<IFieldsetData[]>('tasks_fieldsets_outputs');
