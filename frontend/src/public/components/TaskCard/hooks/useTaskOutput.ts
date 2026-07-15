import { useEffect, useMemo, useState } from 'react';

import { IExtraField } from '../../../types/template';
import { ITask } from '../../../types/tasks';
import { ExtraFieldsHelper } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
import { getEditedFields } from '../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { addOrUpdateStorageOutput, getOutputFromStorage } from '../utils/storageOutputs';
import { createFlushableDebounce } from '../utils/createFlushableDebounce';

export function useTaskOutput(task: ITask) {
  const [outputValues, setOutputValues] = useState<IExtraField[]>([]);
  const saveOutputsToStorageDebounced = useMemo(
    () => createFlushableDebounce(300, addOrUpdateStorageOutput),
    [],
  );
  const taskOutputSignature = useMemo(() => JSON.stringify(task.output), [task.output]);

  useEffect(() => {
    const storageOutput = getOutputFromStorage(task.id);
    setOutputValues(new ExtraFieldsHelper(task.output, storageOutput).getFieldsWithValues());

    return saveOutputsToStorageDebounced.flush;
  }, [task.id, task.dateStarted, taskOutputSignature, saveOutputsToStorageDebounced]);

  const editField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    setOutputValues((previousOutputFields) => {
      const newFields = getEditedFields(previousOutputFields, apiName, changedProps);
      saveOutputsToStorageDebounced(task.id, newFields);

      return newFields;
    });
  };

  return {
    editField,
    flushOutputs: saveOutputsToStorageDebounced.flush,
    outputValues,
  };
}
