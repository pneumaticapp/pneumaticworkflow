import { useEffect, useMemo, useState } from 'react';

import { IFieldsetRuntime } from '../../../types/fieldset';
import { IExtraField } from '../../../types/template';
import { ITask } from '../../../types/tasks';
import { ExtraFieldsHelper } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
import { getEditedFields } from '../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { addOrUpdateStorageOutput, fieldsetsStorage, getOutputFromStorage } from '../utils/storageOutputs';
import { createFlushableDebounce } from '../utils/createFlushableDebounce';

export function useTaskOutput(task: ITask) {
  const [outputValues, setOutputValues] = useState<IExtraField[]>([]);
  const [fieldsetOutputValues, setFieldsetOutputValues] = useState<IFieldsetRuntime[]>([]);
  const saveOutputsToStorageDebounced = useMemo(
    () => createFlushableDebounce(300, addOrUpdateStorageOutput),
    [],
  );
  const saveFieldsetsToStorageDebounced = useMemo(
    () => createFlushableDebounce(300, fieldsetsStorage.save),
    [],
  );
  const taskOutputSignature = useMemo(() => JSON.stringify(task.output), [task.output]);
  const taskFieldsetsSignature = useMemo(() => JSON.stringify(task.fieldsets), [task.fieldsets]);

  useEffect(() => {
    const storageOutput = getOutputFromStorage(task.id);
    setOutputValues(new ExtraFieldsHelper(task.output, storageOutput).getFieldsWithValues());

    const storedFieldsetsByApiName = new Map(
      fieldsetsStorage.get(task.id)?.map((fieldset) => [fieldset.apiNameBinding, fieldset]) ?? [],
    );
    setFieldsetOutputValues(
      (task.fieldsets ?? []).map((fieldset) => ({
        ...fieldset,
        fields: new ExtraFieldsHelper(
          fieldset.fields,
          storedFieldsetsByApiName.get(fieldset.apiNameBinding)?.fields,
        ).getFieldsWithValues(),
      })),
    );

    return () => {
      saveOutputsToStorageDebounced.flush();
      saveFieldsetsToStorageDebounced.flush();
    };
  }, [
    task.id,
    task.dateStarted,
    taskOutputSignature,
    taskFieldsetsSignature,
    saveFieldsetsToStorageDebounced,
    saveOutputsToStorageDebounced,
  ]);

  const editField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    setOutputValues((previousOutputFields) => {
      const newFields = getEditedFields(previousOutputFields, apiName, changedProps);
      saveOutputsToStorageDebounced(task.id, newFields);

      return newFields;
    });
  };

  const editFieldsetField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    setFieldsetOutputValues((previousFieldsets) => {
      const nextFieldsets = previousFieldsets.map((fieldset) => ({
        ...fieldset,
        fields: getEditedFields(fieldset.fields, apiName, changedProps),
      }));
      saveFieldsetsToStorageDebounced(task.id, nextFieldsets);

      return nextFieldsets;
    });
  };

  const flushOutputs = () => {
    saveOutputsToStorageDebounced.flush();
    saveFieldsetsToStorageDebounced.flush();
  };

  return {
    editField,
    editFieldsetField,
    fieldsetOutputValues,
    flushOutputs,
    outputValues,
  };
}
