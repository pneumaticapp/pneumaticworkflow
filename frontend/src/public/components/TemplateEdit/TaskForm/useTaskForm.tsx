import * as React from 'react';
import { useCallback, useEffect, useRef } from 'react';
import { useFormikContext } from 'formik';

import { ITemplateTask } from '../../../types/template';
import { TPatchTaskPayload } from '../../../redux/actions';

type TPatchTaskFn = (payload: TPatchTaskPayload) => void;

interface ITaskFormPersistProviderProps {
  patchTask: TPatchTaskFn;
  task: ITemplateTask;
  children: React.ReactNode;
}

export function TaskFormPersistProvider({ patchTask, task, children }: ITaskFormPersistProviderProps) {
  const { values } = useFormikContext<ITemplateTask>();
  const previousValuesRef = useRef<ITemplateTask>(values);
  const externalTaskRef = useRef<ITemplateTask>(task);

  useEffect(() => {
    // The task prop changed from the store (reinitialize): adopt the new
    // Formik values as the baseline instead of echoing them back as a patch.
    if (externalTaskRef.current !== task) {
      externalTaskRef.current = task;
      previousValuesRef.current = values;

      return;
    }

    if (previousValuesRef.current === values) {
      return;
    }

    const changedFields = getChangedFields(previousValuesRef.current, values);
    previousValuesRef.current = values;

    if (Object.keys(changedFields).length > 0) {
      patchTask({ taskUUID: task.uuid, changedFields });
    }
  }, [values, task, patchTask]);

  return children;
}

function getChangedFields(previous: ITemplateTask, next: ITemplateTask): Partial<ITemplateTask> {
  const changedFields: Partial<ITemplateTask> = {};

  (Object.keys(next) as (keyof ITemplateTask)[]).forEach((key) => {
    if (previous[key] !== next[key]) {
      (changedFields[key] as ITemplateTask[keyof ITemplateTask]) = next[key];
    }
  });

  return changedFields;
}

export function useTaskForm() {
  const { values, setFieldValue } = useFormikContext<ITemplateTask>();

  const updateTask = useCallback(
    (changedFields: Partial<ITemplateTask>) => {
      Object.entries(changedFields).forEach(([field, value]) => {
        setFieldValue(field, value, false);
      });
    },
    [setFieldValue],
  );

  const updateField = useCallback(
    <K extends keyof ITemplateTask>(field: K) => (value: ITemplateTask[K]) => {
      setFieldValue(field, value, false);
    },
    [setFieldValue],
  );

  return {
    task: values,
    updateTask,
    updateField,
  };
}
