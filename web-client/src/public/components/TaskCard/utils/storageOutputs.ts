/* eslint-disable */
/* prettier-ignore */
import produce from 'immer';

import { IExtraField } from '../../../types/template';

const OUTPUT_LOCALSTORAGE_KEY = 'tasks_outputs';

type TLocalStorageOutput = {
  taskId: number;
  output: IExtraField[];
};

export function addOrUpdateStorageOutput(taskId: number, output: IExtraField[]) {
  const currentOutput: TLocalStorageOutput = { taskId, output };
  const savedOutputs = getOutputsFromStorage();

  const newOutputs = produce(savedOutputs, draftOutputs => {
    const savedOutputIndex = draftOutputs.findIndex(output => output.taskId === taskId);

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

  return savedOutputs.find(output => output.taskId === taskId)?.output;
}

export function removeOutputFromLocalStorage(taskId: number) {
  const savedOutputs = getOutputsFromStorage();
  const newOutputs = savedOutputs.filter(output => output.taskId !== taskId);
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
  const ouputsJSON = JSON.stringify(outputs);

  localStorage.setItem(OUTPUT_LOCALSTORAGE_KEY, ouputsJSON);
}
