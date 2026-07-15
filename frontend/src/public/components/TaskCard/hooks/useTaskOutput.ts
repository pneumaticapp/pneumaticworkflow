import { useEffect, useMemo, useRef, useState } from 'react';
import { debounce } from 'throttle-debounce';

import { IExtraField } from '../../../types/template';
import { sortFieldsByOrder } from '../../../utils/workflows';
import { ExtraFieldsHelper } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
import { getEditedFields } from '../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { ITask } from '../../../types/tasks';
import {
  addOrUpdateStorageOutput,
  getOutputFromStorage,
  removeOutputFromLocalStorage,
} from '../utils/storageOutputs';
import { getTaskOutputFingerprint } from '../utils/getTaskOutputFingerprint';

export function useTaskOutput(task: ITask) {
  const [outputValues, setOutputValues] = useState<IExtraField[]>([]);
  const saveOutputsToStorageDebounced = useMemo(
    () => debounce(300, addOrUpdateStorageOutput),
    [],
  );
  const outputSyncStateRef = useRef({
    taskId: null as number | null,
    dateStarted: null as string | null,
    outputFingerprint: '',
  });
  const taskOutputFingerprint = useMemo(
    () => getTaskOutputFingerprint(task.output),
    [task.output],
  );

  useEffect(() => {
    const { output, id, dateStarted } = task;
    const syncState = outputSyncStateRef.current;
    const isNewTask = syncState.taskId !== id;
    const isTaskRestarted = syncState.taskId === id && syncState.dateStarted !== dateStarted;
    const isServerOutputChanged = syncState.taskId === id && syncState.outputFingerprint !== taskOutputFingerprint;

    if (!isNewTask && !isTaskRestarted && !isServerOutputChanged) {
      return;
    }

    saveOutputsToStorageDebounced.cancel();

    if (isTaskRestarted || isServerOutputChanged) {
      removeOutputFromLocalStorage(id);
    }

    const storageOutput = isNewTask ? getOutputFromStorage(id) : undefined;
    const outputFieldsWithValues = sortFieldsByOrder(
      new ExtraFieldsHelper(output, storageOutput).getFieldsWithValues(),
    );

    setOutputValues(outputFieldsWithValues);
    syncState.taskId = id;
    syncState.dateStarted = dateStarted;
    syncState.outputFingerprint = taskOutputFingerprint;
  }, [task.id, task.dateStarted, taskOutputFingerprint, saveOutputsToStorageDebounced]);

  const editField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    setOutputValues((previousOutputFields) => {
      const newFields = getEditedFields(previousOutputFields, apiName, changedProps);

      saveOutputsToStorageDebounced(task.id, newFields);

      return newFields;
    });
  };

  return { outputValues, editField };
}
