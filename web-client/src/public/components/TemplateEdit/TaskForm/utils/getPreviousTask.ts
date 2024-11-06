import { ITemplateTask } from "../../../../types/template";

export function getPreviousTask(currentTask: ITemplateTask, tasks: ITemplateTask[]): ITemplateTask | null {
  if (currentTask.number === 1) {
    return null;
  }

  const prevTask = tasks.find(task => task.number === currentTask.number - 1) || null;

  return prevTask;
}
