import { ITask, ITaskAPI, TTaskChecklists, TTaskChecklistsItems, TTaskChecklistsItem, TTaskChecklist } from '../types/tasks';

export const getNormalizedTask = (task: ITaskAPI): ITask => {
  const normalizedChecklists: TTaskChecklists = {};

  task.checklists.forEach((checklist) => {
    const normalizedItems: TTaskChecklistsItems = {};

    checklist.selections.forEach((selection) => {
      normalizedItems[selection.apiName] = selection;
    });

    const totalItems = checklist.selections.length;
    const checkedItems = checklist.selections.reduce((acc, item) => item.isSelected ? acc + 1 : acc, 0);
  
    normalizedChecklists[checklist.apiName] = {
      ...checklist,
      items: normalizedItems,
      totalItems,
      checkedItems,
    };
  });

  return { ...task, checklists: normalizedChecklists, areChecklistsHandling: false };
};

export const getTaskChecklist = (
  task: ITask,
  listApiName: string,
): TTaskChecklist | null => {
  return task.checklists[listApiName] || null;
};

export const getTaskChecklistItem = (
  task: ITask,
  listApiName: string,
  itemApiName: string,
): TTaskChecklistsItem | null => {
  return task.checklists[listApiName]?.items[itemApiName] || null;
};
