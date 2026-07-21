import { useEffect, useMemo, useRef, useState } from 'react';
import { debounce } from 'throttle-debounce';

import { IFieldsetRuntime } from '../../../types/fieldset';
import { IExtraField } from '../../../types/template';
import { sortFieldsByOrder } from '../../../utils/workflows';
import { ExtraFieldsHelper } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
import { getEditedFields } from '../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { ITask } from '../../../types/tasks';
import {
  addOrUpdateStorageOutput,
  getOutputFromStorage,
  removeOutputFromLocalStorage,
  fieldsetsStorage,
} from '../utils/storageOutputs';
import { getTaskOutputFingerprint } from '../utils/getTaskOutputFingerprint';

export function useTaskOutput(task: ITask) {
  const [outputValues, setOutputValues] = useState<IExtraField[]>([]);
  const [fieldsetOutputValues, setFieldsetOutputValues] = useState<IFieldsetRuntime[]>([]);
  const pendingStorageOutputRef = useRef<{
    taskId: number;
    output: IExtraField[];
  } | null>(null);
  const pendingStorageFieldsetsRef = useRef<{
    taskId: number;
    fieldsets: IFieldsetRuntime[];
  } | null>(null);
  const saveOutputsToStorageDebounced = useMemo(
    () =>
      debounce(300, () => {
        const pendingStorageOutput = pendingStorageOutputRef.current;

        if (!pendingStorageOutput) {
          return;
        }

        addOrUpdateStorageOutput(pendingStorageOutput.taskId, pendingStorageOutput.output);
        pendingStorageOutputRef.current = null;
      }),
    [],
  );
  const saveFieldsetsToStorageDebounced = useMemo(
    () => debounce(300, () => {
      const pendingStorageFieldsets = pendingStorageFieldsetsRef.current;

      if (!pendingStorageFieldsets) return;

      fieldsetsStorage.save(pendingStorageFieldsets.taskId, pendingStorageFieldsets.fieldsets);
      pendingStorageFieldsetsRef.current = null;
    }),
    [],
  );
  const outputSyncStateRef = useRef({
    taskId: null as number | null,
    dateStarted: null as string | null,
    outputFingerprint: '',
    fieldFingerprints: {} as Record<string, string>,
  });
  const fieldsetSyncStateRef = useRef({
    taskId: null as number | null,
    dateStarted: null as string | null,
    fieldsetsFingerprint: '',
    fieldsetFingerprints: {} as Record<string, string>,
  });
  const taskOutputFingerprint = useMemo(
    () => getTaskOutputFingerprint(task.output),
    [task.output],
  );
  const taskFieldsetsFingerprint = useMemo(
    () => JSON.stringify(task.fieldsets ?? []),
    [task.fieldsets],
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

    const fieldFingerprints = Object.fromEntries(
      output.map((field) => [field.apiName, getTaskOutputFingerprint([field])]),
    );
    let storageOutput: IExtraField[] | undefined;

    if (isNewTask) {
      const pendingStorageOutput = pendingStorageOutputRef.current;

      if (pendingStorageOutput) {
        addOrUpdateStorageOutput(pendingStorageOutput.taskId, pendingStorageOutput.output);
        pendingStorageOutputRef.current = null;
      }

      storageOutput = getOutputFromStorage(id);
    } else if (isTaskRestarted) {
      pendingStorageOutputRef.current = null;
      removeOutputFromLocalStorage(id);
    } else if (isServerOutputChanged) {
      const pendingStorageOutput = pendingStorageOutputRef.current;
      const savedOutput = pendingStorageOutput?.taskId === id
        ? pendingStorageOutput.output
        : getOutputFromStorage(id);

      storageOutput = savedOutput?.filter(
        (field) => syncState.fieldFingerprints[field.apiName] === fieldFingerprints[field.apiName],
      );

      if (savedOutput) {
        addOrUpdateStorageOutput(id, storageOutput ?? []);
        pendingStorageOutputRef.current = null;
      }
    }

    const outputFieldsWithValues = sortFieldsByOrder(
      new ExtraFieldsHelper(output, storageOutput).getFieldsWithValues(),
    );

    setOutputValues(outputFieldsWithValues);
    syncState.taskId = id;
    syncState.dateStarted = dateStarted;
    syncState.outputFingerprint = taskOutputFingerprint;
    syncState.fieldFingerprints = fieldFingerprints;
  }, [task.id, task.dateStarted, taskOutputFingerprint, saveOutputsToStorageDebounced]);

  useEffect(() => {
    const { id, dateStarted, fieldsets = [] } = task;
    const syncState = fieldsetSyncStateRef.current;
    const isNewTask = syncState.taskId !== id;
    const isTaskRestarted = syncState.taskId === id && syncState.dateStarted !== dateStarted;
    const isServerFieldsetsChanged = syncState.taskId === id
      && syncState.fieldsetsFingerprint !== taskFieldsetsFingerprint;

    if (!isNewTask && !isTaskRestarted && !isServerFieldsetsChanged) return;

    const fieldsetFingerprints = Object.fromEntries(
      fieldsets.map((fieldset) => [fieldset.apiNameBinding, JSON.stringify(fieldset)]),
    );
    let savedFieldsets: IFieldsetRuntime[] | undefined;

    if (isNewTask) {
      const pendingStorageFieldsets = pendingStorageFieldsetsRef.current;
      if (pendingStorageFieldsets) {
        fieldsetsStorage.save(pendingStorageFieldsets.taskId, pendingStorageFieldsets.fieldsets);
        pendingStorageFieldsetsRef.current = null;
      }
      savedFieldsets = fieldsetsStorage.get(id);
    } else if (isTaskRestarted) {
      saveFieldsetsToStorageDebounced.cancel();
      pendingStorageFieldsetsRef.current = null;
      fieldsetsStorage.remove(id);
    } else {
      const pendingStorageFieldsets = pendingStorageFieldsetsRef.current;
      savedFieldsets = pendingStorageFieldsets?.taskId === id
        ? pendingStorageFieldsets.fieldsets
        : fieldsetsStorage.get(id);

      if (savedFieldsets) {
        savedFieldsets = savedFieldsets.filter(
          (fieldset) => syncState.fieldsetFingerprints[fieldset.apiNameBinding]
            === fieldsetFingerprints[fieldset.apiNameBinding],
        );
        saveFieldsetsToStorageDebounced.cancel();
        fieldsetsStorage.save(id, savedFieldsets);
        pendingStorageFieldsetsRef.current = null;
      }
    }

    const savedFieldsetsByApiName = new Map(
      savedFieldsets?.map((fieldset) => [fieldset.apiNameBinding, fieldset]) ?? [],
    );
    setFieldsetOutputValues(
      fieldsets.map((fieldset) => ({
        ...fieldset,
        fields: new ExtraFieldsHelper(
          fieldset.fields,
          savedFieldsetsByApiName.get(fieldset.apiNameBinding)?.fields,
        ).getFieldsWithValues(),
      })),
    );

    syncState.taskId = id;
    syncState.dateStarted = dateStarted;
    syncState.fieldsetsFingerprint = taskFieldsetsFingerprint;
    syncState.fieldsetFingerprints = fieldsetFingerprints;
  }, [
    task.id,
    task.dateStarted,
    taskFieldsetsFingerprint,
    saveFieldsetsToStorageDebounced,
  ]);

  useEffect(
    () => () => {
      const pendingStorageFieldsets = pendingStorageFieldsetsRef.current;
      if (pendingStorageFieldsets) {
        fieldsetsStorage.save(pendingStorageFieldsets.taskId, pendingStorageFieldsets.fieldsets);
      }

      saveOutputsToStorageDebounced.cancel();
      saveFieldsetsToStorageDebounced.cancel();
      pendingStorageOutputRef.current = null;
      pendingStorageFieldsetsRef.current = null;
    },
    [saveFieldsetsToStorageDebounced, saveOutputsToStorageDebounced],
  );

  const editField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    setOutputValues((previousOutputFields) => {
      const newFields = getEditedFields(previousOutputFields, apiName, changedProps);

      pendingStorageOutputRef.current = { taskId: task.id, output: newFields };
      saveOutputsToStorageDebounced();

      return newFields;
    });
  };

  const editFieldsetField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    setFieldsetOutputValues((previousFieldsets) => {
      const nextFieldsets = previousFieldsets.map((fieldset) => ({
        ...fieldset,
        fields: getEditedFields(fieldset.fields, apiName, changedProps),
      }));

      pendingStorageFieldsetsRef.current = { taskId: task.id, fieldsets: nextFieldsets };
      saveFieldsetsToStorageDebounced();
      return nextFieldsets;
    });
  };

  return { outputValues, fieldsetOutputValues, editField, editFieldsetField };
}
