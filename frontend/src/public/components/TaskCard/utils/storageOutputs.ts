import produce from 'immer';

import { IFieldsetRuntime } from '../../../types/fieldset';
import { IExtraField } from '../../../types/template';

const OUTPUT_LOCALSTORAGE_KEY = 'tasks_outputs';
const FIELDSETS_LOCALSTORAGE_KEY = 'tasks_fieldsets_outputs';

type TLocalStorageOutput = {
  taskId: number;
  output: IExtraField[];
};

export function addOrUpdateStorageOutput(taskId: number, output: IExtraField[]) {
  const currentOutput: TLocalStorageOutput = { taskId, output };
  const savedOutputs = getOutputsFromStorage();

  const newOutputs = produce(savedOutputs, (draftOutputs) => {
    const savedOutputIndex = draftOutputs.findIndex((savedOutput) => savedOutput.taskId === taskId);

    if (savedOutputIndex === -1) {
      draftOutputs.push(currentOutput);

      return;
    }

    draftOutputs[savedOutputIndex] = currentOutput;
  });

  saveOutputsToStorage(newOutputs);
}

export function getOutputFromStorage(taskId: number) {
  const savedOutputs = getOutputsFromStorage();

  return savedOutputs.find((output) => output.taskId === taskId)?.output;
}

export function removeOutputFromLocalStorage(taskId: number) {
  removeOutputsFromLocalStorage([taskId]);
}

export function removeOutputsFromLocalStorage(taskIds: number[]) {
  if (taskIds.length === 0) {
    return;
  }

  const taskIdsSet = new Set(taskIds);
  const savedOutputs = getOutputsFromStorage();
  const newOutputs = savedOutputs.filter((output) => !taskIdsSet.has(output.taskId));
  saveOutputsToStorage(newOutputs);
}

function getOutputsFromStorage(): TLocalStorageOutput[] {
  try {
    const savedOutputsString = localStorage.getItem(OUTPUT_LOCALSTORAGE_KEY);

    if (!savedOutputsString) {
      throw new Error('no saved outputs');
    }

    const savedOutputs = JSON.parse(savedOutputsString) as TLocalStorageOutput[];

    if (!Array.isArray(savedOutputs)) {
      throw new Error('saved outputs are invalid');
    }

    return savedOutputs;
  } catch (error) {
    return [];
  }
}

function saveOutputsToStorage(outputs: TLocalStorageOutput[]) {
  if (outputs.length === 0) {
    localStorage.removeItem(OUTPUT_LOCALSTORAGE_KEY);

    return;
  }

  localStorage.setItem(OUTPUT_LOCALSTORAGE_KEY, JSON.stringify(outputs));
}

function getStoredFieldsets(): { taskId: number; data: IFieldsetRuntime[] }[] {
  try {
    const stored = JSON.parse(localStorage.getItem(FIELDSETS_LOCALSTORAGE_KEY) || '[]');
    return Array.isArray(stored) ? stored : [];
  } catch {
    return [];
  }
}

export const outputStorage = {
  save: addOrUpdateStorageOutput,
  get: getOutputFromStorage,
  remove: removeOutputFromLocalStorage,
};

export const fieldsetsStorage = {
  save(taskId: number, data: IFieldsetRuntime[]) {
    const entries = getStoredFieldsets().filter((entry) => entry.taskId !== taskId);
    localStorage.setItem(FIELDSETS_LOCALSTORAGE_KEY, JSON.stringify([...entries, { taskId, data }]));
  },
  get(taskId: number) {
    return getStoredFieldsets().find((entry) => entry.taskId === taskId)?.data;
  },
  remove(taskId: number) {
    const entries = getStoredFieldsets().filter((entry) => entry.taskId !== taskId);
    if (entries.length) localStorage.setItem(FIELDSETS_LOCALSTORAGE_KEY, JSON.stringify(entries));
    else localStorage.removeItem(FIELDSETS_LOCALSTORAGE_KEY);
  },
};
