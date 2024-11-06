/* eslint-disable */
/* prettier-ignore */
import { ITaskListItem, ITasksSettings } from '../../../types/tasks';

export function checkShouldInsertNewTask(
  newTask: ITaskListItem,
  tasksSettings: ITasksSettings,
  searchText: string,
): boolean {
  const normalizedSearchText = searchText.toLocaleLowerCase();
  const { filterValues: { templateIdFilter, stepIdFilter } } = tasksSettings;

  return [
    newTask.name.toLocaleLowerCase().includes(normalizedSearchText)
    || newTask.workflowName.toLocaleLowerCase().includes(normalizedSearchText),

    !templateIdFilter || templateIdFilter === newTask.templateId,

    !stepIdFilter || stepIdFilter === newTask.templateTaskId,
  ].every(Boolean);
}
