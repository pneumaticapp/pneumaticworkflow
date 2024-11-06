/* eslint-disable */
/* prettier-ignore */
import * as moment from 'moment';
import { ITaskList } from '../../../types/redux';
import { ETaskListCompleteSorting, ETaskListSorting, ITaskListItem } from '../../../types/tasks';

export function getTaskListWithNewTask(
  initialTaskList: ITaskList,
  newTask: ITaskListItem,
  sorting: ETaskListSorting | ETaskListCompleteSorting,
): ITaskList {
  const {
    items: tasksItems,
    count: tasksCount,
    offset: tasksOffset,
  } = initialTaskList;

  const firstNotUrgentIndex = tasksItems.findIndex(task => {
    return !task.isUrgent;
  });
  const tasksItemsLength = tasksItems.length;

  const insertTaskMap:
  { [key in ETaskListSorting]: (tasksItems: ITaskListItem[]) => ITaskListItem[] } |
  { [key in ETaskListCompleteSorting]: (tasksItems: ITaskListItem[]) => ITaskListItem[] } = {

    [ETaskListSorting.DateDesc]: (tasksItems: ITaskListItem[]) => {
      return [newTask, ...tasksItems];
    },
    [ETaskListSorting.DateAsc]: (tasksItems: ITaskListItem[]) => {
      const areAllTasksLoaded = tasksItemsLength === tasksCount;

      if (!areAllTasksLoaded) {
        return tasksItems;
      }

      return [...tasksItems, newTask];
    },
    [ETaskListSorting.Overdue]: (tasksItems: ITaskListItem[]) => {
      const insertIndex = tasksItems.findIndex(task => {
        if (!task.dueDate) {
          return true;
        }

        if (!newTask.dueDate) {
          return !task.dueDate;
        }

        return moment(task.dueDate).isAfter(newTask.dueDate);
      });

      if (insertIndex === -1 && tasksItemsLength !== tasksCount) {
        return tasksItems;
      }

      if (insertIndex === -1) {
        return [...tasksItems, newTask];
      }

      return [...tasksItems.slice(0, insertIndex), newTask, ...tasksItems.slice(insertIndex)];
    },
  };

  if (newTask.isUrgent) {
    const newTaskList = insertTaskMap[sorting](tasksItems.slice(0, firstNotUrgentIndex));
    const items = [...newTaskList, ...tasksItems.slice(firstNotUrgentIndex)];
    const offset = items.length - tasksItems.length;

    return {
      items,
      count: tasksCount + offset,
      offset: tasksOffset + offset,
    };
  }
  const newTaskList = insertTaskMap[sorting](tasksItems.slice(firstNotUrgentIndex));
  const items = [...tasksItems.slice(0, firstNotUrgentIndex), ...newTaskList];
  const offset = items.length - tasksItems.length;

  return {
    items,
    count: tasksCount + offset,
    offset: tasksOffset + offset,
  };
}
