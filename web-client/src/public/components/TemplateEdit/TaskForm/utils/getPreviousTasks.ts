import { ITemplateTask } from "../../../../types/template";

export function getPreviousTasks(currentTask: ITemplateTask, tasks: ITemplateTask[]) {
  return tasks.filter(task => task.number < currentTask.number);
}
