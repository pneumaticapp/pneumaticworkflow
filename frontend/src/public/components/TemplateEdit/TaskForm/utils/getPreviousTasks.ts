import { ITemplateTaskClient } from "../../../../types/template";

export function getPreviousTasks(currentTask: ITemplateTaskClient, tasks: ITemplateTaskClient[]) {
  return tasks.filter(task => task.number < currentTask.number);
}
