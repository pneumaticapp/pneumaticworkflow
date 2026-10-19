import { useCallback, useRef } from 'react';

import { ITemplateTaskClient } from '../../../types/template';
import { useTaskFormScope, useTemplateField } from '../useTemplateForm';

export function useTaskForm() {
  const { values, setFieldValue } = useTemplateField();
  const taskUuid = useTaskFormScope();

  const index = values.tasks.findIndex((task) => task.uuid === taskUuid);
  const task = values.tasks[index];
  const taskRef = useRef(task);
  taskRef.current = task;

  const updateTask = useCallback(
    (changedFields: Partial<ITemplateTaskClient>) => {
      const nextTask = { ...taskRef.current, ...changedFields };
      taskRef.current = nextTask;
      setFieldValue(`tasks.${index}`, nextTask, false);
    },
    [index, setFieldValue],
  );

  const updateField = useCallback(
    <K extends keyof ITemplateTaskClient>(field: K) =>
      (value: ITemplateTaskClient[K]) => {
        const nextTask = { ...taskRef.current, [field]: value };
        taskRef.current = nextTask;
        setFieldValue(`tasks.${index}.${String(field)}`, value, false);
      },
    [index, setFieldValue],
  );

  if (!task) {
    throw new Error(`Task with uuid "${taskUuid}" is not present in the template form state`);
  }

  return {
    task,
    updateTask,
    updateField,
  };
}
