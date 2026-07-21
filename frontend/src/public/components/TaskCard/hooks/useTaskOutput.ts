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
  outputStorage,
  TFieldsetDraftMetadata,
  TOutputDraftMetadata,
} from '../utils/storageOutputs';
import { getTaskOutputFingerprint } from '../utils/getTaskOutputFingerprint';

export function useTaskOutput(task: ITask) {
  const [outputValues, setOutputValues] = useState<IExtraField[]>([]);
  const [fieldsetOutputValues, setFieldsetOutputValues] = useState<IFieldsetRuntime[]>([]);
  const pendingStorageOutputRef = useRef<{
    taskId: number;
    output: IExtraField[];
    metadata: TOutputDraftMetadata;
  } | null>(null);
  const pendingStorageFieldsetsRef = useRef<{
    taskId: number;
    fieldsets: IFieldsetRuntime[];
    metadata: TFieldsetDraftMetadata;
  } | null>(null);
  const saveOutputsToStorageDebounced = useMemo(
    () =>
      debounce(300, () => {
        const pendingStorageOutput = pendingStorageOutputRef.current;

        if (!pendingStorageOutput) {
          return;
        }

        addOrUpdateStorageOutput(
          pendingStorageOutput.taskId,
          pendingStorageOutput.output,
          pendingStorageOutput.metadata,
        );
        pendingStorageOutputRef.current = null;
      }),
    [],
  );
  const saveFieldsetsToStorageDebounced = useMemo(
    () => debounce(300, () => {
      const pendingStorageFieldsets = pendingStorageFieldsetsRef.current;

      if (!pendingStorageFieldsets) return;

      fieldsetsStorage.save(
        pendingStorageFieldsets.taskId,
        pendingStorageFieldsets.fieldsets,
        pendingStorageFieldsets.metadata,
      );
      pendingStorageFieldsetsRef.current = null;
    }),
    [],
  );
  const outputSyncStateRef = useRef({
    taskId: null as number | null,
    dateStarted: null as string | null,
    outputFingerprint: '',
    outputDefinitionSignature: '',
    fieldFingerprints: {} as Record<string, string>,
  });
  const fieldsetSyncStateRef = useRef({
    taskId: null as number | null,
    dateStarted: null as string | null,
    fieldsetsFingerprint: '',
    fieldFingerprints: {} as Record<string, Record<string, string>>,
  });
  const taskOutputFingerprint = useMemo(
    () => getTaskOutputFingerprint(task.output),
    [task.output],
  );
  const taskOutputDefinitionSignature = useMemo(
    () => JSON.stringify(task.output),
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
    const isServerOutputDefinitionChanged = syncState.taskId === id
      && syncState.outputDefinitionSignature !== taskOutputDefinitionSignature;

    if (!isNewTask && !isTaskRestarted && !isServerOutputDefinitionChanged) {
      return;
    }

    const fieldFingerprints = Object.fromEntries(
      output.map((field) => [field.apiName, getTaskOutputFingerprint([field])]),
    );
    let storageOutput: IExtraField[] | undefined;

    if (isNewTask) {
      const pendingStorageOutput = pendingStorageOutputRef.current;

      if (pendingStorageOutput) {
        addOrUpdateStorageOutput(
          pendingStorageOutput.taskId,
          pendingStorageOutput.output,
          pendingStorageOutput.metadata,
        );
        pendingStorageOutputRef.current = null;
      }

      const storedEntry = outputStorage.getEntry(id);
      if (storedEntry?.metadata) {
        if (storedEntry.metadata.dateStarted !== dateStarted) {
          removeOutputFromLocalStorage(id);
        } else {
          storageOutput = storedEntry.data.filter(
            (field) => storedEntry.metadata?.fieldFingerprints[field.apiName]
              === fieldFingerprints[field.apiName],
          );
          addOrUpdateStorageOutput(id, storageOutput, { dateStarted, fieldFingerprints });
        }
      } else {
        storageOutput = storedEntry?.data;
        if (storageOutput) {
          addOrUpdateStorageOutput(id, storageOutput, { dateStarted, fieldFingerprints });
        }
      }
    } else if (isTaskRestarted) {
      saveOutputsToStorageDebounced.cancel();
      pendingStorageOutputRef.current = null;
      removeOutputFromLocalStorage(id);
    } else if (isServerOutputChanged) {
      saveOutputsToStorageDebounced.cancel();
      const pendingStorageOutput = pendingStorageOutputRef.current;
      const savedOutput = pendingStorageOutput?.taskId === id
        ? pendingStorageOutput.output
        : getOutputFromStorage(id);

      storageOutput = savedOutput?.filter(
        (field) => syncState.fieldFingerprints[field.apiName] === fieldFingerprints[field.apiName],
      );

      if (savedOutput) {
        addOrUpdateStorageOutput(
          id,
          storageOutput ?? [],
          { dateStarted, fieldFingerprints },
        );
        pendingStorageOutputRef.current = null;
      }
    } else if (isServerOutputDefinitionChanged) {
      const pendingStorageOutput = pendingStorageOutputRef.current;
      storageOutput = pendingStorageOutput?.taskId === id
        ? pendingStorageOutput.output
        : getOutputFromStorage(id);
    }

    const outputFieldsWithValues = sortFieldsByOrder(
      new ExtraFieldsHelper(output, storageOutput).getFieldsWithValues(),
    );

    setOutputValues(outputFieldsWithValues);
    syncState.taskId = id;
    syncState.dateStarted = dateStarted;
    syncState.outputFingerprint = taskOutputFingerprint;
    syncState.outputDefinitionSignature = taskOutputDefinitionSignature;
    syncState.fieldFingerprints = fieldFingerprints;
  }, [
    task.id,
    task.dateStarted,
    taskOutputDefinitionSignature,
    taskOutputFingerprint,
    saveOutputsToStorageDebounced,
  ]);

  useEffect(() => {
    const { id, dateStarted, fieldsets = [] } = task;
    const syncState = fieldsetSyncStateRef.current;
    const isNewTask = syncState.taskId !== id;
    const isTaskRestarted = syncState.taskId === id && syncState.dateStarted !== dateStarted;
    const isServerFieldsetsChanged = syncState.taskId === id
      && syncState.fieldsetsFingerprint !== taskFieldsetsFingerprint;

    if (!isNewTask && !isTaskRestarted && !isServerFieldsetsChanged) return;

    const fieldFingerprints = Object.fromEntries(
      fieldsets.map((fieldset) => [
        fieldset.apiNameBinding,
        Object.fromEntries(
          fieldset.fields.map((field) => [field.apiName, getTaskOutputFingerprint([field])]),
        ),
      ]),
    );
    let savedFieldsets: IFieldsetRuntime[] | undefined;

    if (isNewTask) {
      const pendingStorageFieldsets = pendingStorageFieldsetsRef.current;
      if (pendingStorageFieldsets) {
        fieldsetsStorage.save(
          pendingStorageFieldsets.taskId,
          pendingStorageFieldsets.fieldsets,
          pendingStorageFieldsets.metadata,
        );
        pendingStorageFieldsetsRef.current = null;
      }

      const storedEntry = fieldsetsStorage.getEntry(id);
      if (storedEntry?.metadata) {
        if (storedEntry.metadata.dateStarted !== dateStarted) {
          fieldsetsStorage.remove(id);
        } else {
          savedFieldsets = storedEntry.data
            .map((fieldset) => ({
              ...fieldset,
              fields: fieldset.fields.filter((field) =>
                storedEntry.metadata?.fieldFingerprints[fieldset.apiNameBinding]?.[field.apiName]
                  === fieldFingerprints[fieldset.apiNameBinding]?.[field.apiName]),
            }))
            .filter((fieldset) => fieldset.fields.length > 0);
          fieldsetsStorage.save(id, savedFieldsets, { dateStarted, fieldFingerprints });
        }
      } else {
        savedFieldsets = storedEntry?.data;
        if (savedFieldsets) {
          fieldsetsStorage.save(id, savedFieldsets, { dateStarted, fieldFingerprints });
        }
      }
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
        savedFieldsets = savedFieldsets
          .map((fieldset) => ({
            ...fieldset,
            fields: fieldset.fields.filter((field) =>
              syncState.fieldFingerprints[fieldset.apiNameBinding]?.[field.apiName]
                === fieldFingerprints[fieldset.apiNameBinding]?.[field.apiName]),
          }))
          .filter((fieldset) => fieldset.fields.length > 0);
        saveFieldsetsToStorageDebounced.cancel();
        fieldsetsStorage.save(id, savedFieldsets, { dateStarted, fieldFingerprints });
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
    syncState.fieldFingerprints = fieldFingerprints;
  }, [
    task.id,
    task.dateStarted,
    taskFieldsetsFingerprint,
    saveFieldsetsToStorageDebounced,
  ]);

  const flushOutputs = () => {
    saveOutputsToStorageDebounced.cancel();
    saveFieldsetsToStorageDebounced.cancel();

    const pendingStorageOutput = pendingStorageOutputRef.current;
    if (pendingStorageOutput) {
      addOrUpdateStorageOutput(
        pendingStorageOutput.taskId,
        pendingStorageOutput.output,
        pendingStorageOutput.metadata,
      );
    }

    const pendingStorageFieldsets = pendingStorageFieldsetsRef.current;
    if (pendingStorageFieldsets) {
      fieldsetsStorage.save(
        pendingStorageFieldsets.taskId,
        pendingStorageFieldsets.fieldsets,
        pendingStorageFieldsets.metadata,
      );
    }

    pendingStorageOutputRef.current = null;
    pendingStorageFieldsetsRef.current = null;
  };

  useEffect(
    () => () => flushOutputs(),
    [saveFieldsetsToStorageDebounced, saveOutputsToStorageDebounced],
  );

  const editField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    setOutputValues((previousOutputFields) => {
      const newFields = getEditedFields(previousOutputFields, apiName, changedProps);

      pendingStorageOutputRef.current = {
        taskId: task.id,
        output: newFields,
        metadata: {
          dateStarted: task.dateStarted,
          fieldFingerprints: { ...outputSyncStateRef.current.fieldFingerprints },
        },
      };
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

      pendingStorageFieldsetsRef.current = {
        taskId: task.id,
        fieldsets: nextFieldsets,
        metadata: {
          dateStarted: task.dateStarted,
          fieldFingerprints: { ...fieldsetSyncStateRef.current.fieldFingerprints },
        },
      };
      saveFieldsetsToStorageDebounced();
      return nextFieldsets;
    });
  };

  return { outputValues, fieldsetOutputValues, editField, editFieldsetField, flushOutputs };
}
