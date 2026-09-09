import { ITemplateTaskClient } from '../../../types/template';

export function insertTemplateTask(
  tasks: ITemplateTaskClient[],
  newTask: ITemplateTaskClient,
  index: number,
): ITemplateTaskClient[] {
  return [...tasks.slice(0, index), newTask, ...tasks.slice(index)].map((task, taskIndex) => ({
    ...task,
    number: taskIndex + 1,
  }));
}

export function removeTemplateTask(tasks: ITemplateTaskClient[], targetTaskUuid: string): ITemplateTaskClient[] {
  return tasks.filter((task) => task.uuid !== targetTaskUuid).map((task, index) => ({ ...task, number: index + 1 }));
}

export function updateTemplateTaskDelay(
  tasks: ITemplateTaskClient[],
  targetTask: ITemplateTaskClient,
  delay: string,
): ITemplateTaskClient[] {
  return tasks.map((task) => (task.uuid === targetTask.uuid ? { ...targetTask, delay } : task));
}
