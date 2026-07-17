import { ITemplateTaskClient } from "../../../../types/template";

export function getPreviousTask(currentTask: ITemplateTaskClient, tasks: ITemplateTaskClient[]): ITemplateTaskClient | null {
  if (currentTask.number === 1) {
    return null;
  }

  const prevTask = tasks.find(task => task.number === currentTask.number - 1) || null;

  return prevTask;
}
