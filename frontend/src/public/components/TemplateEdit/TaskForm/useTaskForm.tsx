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
  const skipNextPersistRef = useRef(false);
  const valuesRef = useRef(values);
  const taskRef = useRef(task);
  const patchTaskRef = useRef(patchTask);

  valuesRef.current = values;
  taskRef.current = task;
  patchTaskRef.current = patchTask;

  const flushPersist = useCallback(() => {
    const currentValues = valuesRef.current;

    if (previousValuesRef.current === currentValues) {
      return;
    }

    const changedFields = getChangedFields(previousValuesRef.current, currentValues);
    previousValuesRef.current = currentValues;

    if (Object.keys(changedFields).length > 0) {
      patchTaskRef.current({ taskUUID: taskRef.current.uuid, changedFields });
    }
  }, []);

  useEffect(() => {
    let timeoutId: number | undefined;

    if (externalTaskRef.current !== task) {
      externalTaskRef.current = task;
      skipNextPersistRef.current = true;
    } else if (skipNextPersistRef.current) {
      skipNextPersistRef.current = false;
      previousValuesRef.current = values;
    } else if (previousValuesRef.current !== values) {
      timeoutId = window.setTimeout(flushPersist, 0);
    }

    return () => {
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);

        if (taskRef.current.uuid === task.uuid) {
          flushPersist();
        }
      }
    };
  }, [values, task, flushPersist]);

  return children as React.ReactElement;
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
  const { values, setFieldValue, setValues } = useFormikContext<ITemplateTask>();
  const valuesRef = useRef(values);

  valuesRef.current = values;

  const updateTask = useCallback(
    (changedFields: Partial<ITemplateTask>) => {
      const nextValues = { ...valuesRef.current, ...changedFields };

      valuesRef.current = nextValues;
      setValues(nextValues, false);
    },
    [setValues],
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
