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

type TStorageValidators<T, TMetadata> = {
  isValidData: (data: unknown) => data is T;
  isValidMetadata: (metadata: unknown) => metadata is TMetadata;
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const isStoredField = (field: unknown): field is IExtraField => isRecord(field) && typeof field.apiName === 'string';

const isStoredFields = (data: unknown): data is IExtraField[] => Array.isArray(data) && data.every(isStoredField);

const isStoredFieldsets = (data: unknown): data is IFieldsetRuntime[] =>
  Array.isArray(data) &&
  data.every(
    (fieldset) => isRecord(fieldset) && typeof fieldset.apiNameBinding === 'string' && isStoredFields(fieldset.fields),
  );

const isDraftMetadata = (metadata: unknown): metadata is { dateStarted: string | null; fieldFingerprints: unknown } =>
  isRecord(metadata) &&
  (typeof metadata.dateStarted === 'string' || metadata.dateStarted === null) &&
  isRecord(metadata.fieldFingerprints);

const isOutputDraftMetadata = (metadata: unknown): metadata is TOutputDraftMetadata => isDraftMetadata(metadata);

const isFieldsetDraftMetadata = (metadata: unknown): metadata is TFieldsetDraftMetadata =>
  isDraftMetadata(metadata) && Object.values(metadata.fieldFingerprints as Record<string, unknown>).every(isRecord);

function createTaskStorage<T, TMetadata>(
  storageKey: string,
  { isValidData, isValidMetadata }: TStorageValidators<T, TMetadata>,
) {
  function getAll(): TStorageEntry<T, TMetadata>[] {
    try {
      const savedDataString = localStorage.getItem(storageKey);

      if (!savedDataString) {
        return [];
      }

      const savedData: unknown = JSON.parse(savedDataString);

      if (!Array.isArray(savedData)) {
        return [];
      }

      return savedData.flatMap((entry: unknown) => {
        if (!isRecord(entry) || typeof entry.taskId !== 'number') return [];

        const { taskId, data, output, metadata } = entry as TRawStorageEntry<unknown, unknown>;
        const entryData = data ?? output;

        if (!isValidData(entryData)) return [];
        if (metadata === undefined) return [{ taskId, data: entryData }];

        return isValidMetadata(metadata) ? [{ taskId, data: entryData, metadata }] : [];
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

export const outputStorage = createTaskStorage<IExtraField[], TOutputDraftMetadata>('tasks_outputs', {
  isValidData: isStoredFields,
  isValidMetadata: isOutputDraftMetadata,
});

export const fieldsetsStorage = createTaskStorage<IFieldsetRuntime[], TFieldsetDraftMetadata>(
  'tasks_fieldsets_outputs',
  {
    isValidData: isStoredFieldsets,
    isValidMetadata: isFieldsetDraftMetadata,
  },
);

export const addOrUpdateStorageOutput = outputStorage.save;
export const getOutputFromStorage = outputStorage.get;
export const removeOutputFromLocalStorage = outputStorage.remove;
export const removeOutputsFromLocalStorage = outputStorage.removeMany;
