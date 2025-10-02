/* eslint-disable */
/* prettier-ignore */
import { ITaskList } from '../../../../types/redux';
import { ETaskListSorting, ITaskListItem } from '../../../../types/tasks';
import { getTaskListWithNewTask } from '../getTaskListWithNewTask';

const createMockTask = (task: Partial<ITaskListItem>): ITaskListItem => {
  return {
    dueDate: null,
    dateStarted: '2022-12-08T11:03:24.042149Z',
    dateCompleted: null,
    id: 0,
    name: 'Task name',
    workflowName: 'Wokrflow name',
    templateId: 1,
    templateTaskId: 1,
    isUrgent: false,
    ...task,
  };
};

describe('getTaskListWithNewTask', () => {
  it('inserts task in the top of list if sorting is "Newest first"', () => {
    const initialTaskList: ITaskList = {
      items: [
        createMockTask({ id: 1 }),
        createMockTask({ id: 2 }),
        createMockTask({ id: 3 }),
      ],
      count: 3,
      offset: 3,
    };

    const NEW_TASK_ID = 4;
    const newTask = createMockTask({ id: NEW_TASK_ID });
    const resultTaskList = getTaskListWithNewTask(initialTaskList, newTask, ETaskListSorting.DateDesc);

    expect(resultTaskList.items.findIndex(task => task.id === NEW_TASK_ID)).toEqual(0);
    expect(resultTaskList.offset).toEqual(4);
    expect(resultTaskList.count).toEqual(4);
  });

  it('inserts not urgent task before urgent tasks if sorting is "Newest first"', () => {
    const initialTaskList: ITaskList = {
      items: [
        createMockTask({ id: 1, isUrgent: true }),
        createMockTask({ id: 2, isUrgent: true }),
        createMockTask({ id: 3 }),
      ],
      count: 3,
      offset: 3,
    };

    const NEW_TASK_ID = 4;
    const newTask = createMockTask({ id: NEW_TASK_ID });
    const resultTaskList = getTaskListWithNewTask(initialTaskList, newTask, ETaskListSorting.DateDesc);

    expect(resultTaskList.items.findIndex(task => task.id === NEW_TASK_ID)).toEqual(2);
    expect(resultTaskList.offset).toEqual(4);
    expect(resultTaskList.count).toEqual(4);
  });

  it('inserts task in the end of list if sorting is "Oldest first"', () => {
    const initialTaskList: ITaskList = {
      items: [
        createMockTask({ id: 1 }),
        createMockTask({ id: 2 }),
        createMockTask({ id: 3 }),
      ],
      count: 3,
      offset: 3,
    };

    const NEW_TASK_ID = 4;
    const newTask = createMockTask({ id: NEW_TASK_ID });
    const resultTaskList = getTaskListWithNewTask(initialTaskList, newTask, ETaskListSorting.DateAsc);

    expect(resultTaskList.items.findIndex(task => task.id === NEW_TASK_ID)).toEqual(3);
    expect(resultTaskList.offset).toEqual(4);
    expect(resultTaskList.count).toEqual(4);
  });

  it('inserts urgent task in the top of list if sorting is "Oldest first"', () => {
    const initialTaskList: ITaskList = {
      items: [
        createMockTask({ id: 1 }),
        createMockTask({ id: 2 }),
        createMockTask({ id: 3 }),
      ],
      count: 3,
      offset: 3,
    };

    const NEW_TASK_ID = 4;
    const newTask = createMockTask({ id: NEW_TASK_ID, isUrgent: true });
    const resultTaskList = getTaskListWithNewTask(initialTaskList, newTask, ETaskListSorting.DateAsc);

    expect(resultTaskList.items.findIndex(task => task.id === NEW_TASK_ID)).toEqual(0);
    expect(resultTaskList.offset).toEqual(4);
    expect(resultTaskList.count).toEqual(4);
  });

  it('does not insert task if sorting is "Oldest first" and list is not fully loaded', () => {
    const initialTaskList: ITaskList = {
      items: [
        createMockTask({ id: 1 }),
        createMockTask({ id: 2 }),
        createMockTask({ id: 3 }),
      ],
      count: 2,
      offset: 2,
    };

    const NEW_TASK_ID = 4;
    const newTask = createMockTask({ id: NEW_TASK_ID });
    const resultTaskList = getTaskListWithNewTask(initialTaskList, newTask, ETaskListSorting.DateAsc);

    expect(resultTaskList.items.findIndex(task => task.id === NEW_TASK_ID)).toEqual(-1);
    expect(resultTaskList.offset).toEqual(2);
    expect(resultTaskList.count).toEqual(2);
  });

  it('inserts task with setted estimatedEndDate if sorting is "Overdue"', () => {
    const initialTaskList: ITaskList = {
      items: [
        createMockTask({ id: 1, dueDate: '2021-04-16T10:17:00.024060Z' }),
        createMockTask({ id: 2, dueDate: '2021-07-14T15:28:32.534944Z' }),
        createMockTask({ id: 3 }),
      ],
      count: 2,
      offset: 2,
    };

    const NEW_TASK_ID = 4;
    const newTask = createMockTask({ id: NEW_TASK_ID, dueDate: '2021-07-12T18:27:18.260524Z' });
    const resultTaskList = getTaskListWithNewTask(initialTaskList, newTask, ETaskListSorting.Overdue);

    expect(resultTaskList.items.findIndex(task => task.id === NEW_TASK_ID)).toEqual(1);
    expect(resultTaskList.offset).toEqual(3);
    expect(resultTaskList.count).toEqual(3);
  });

  it('inserts task with NO setted estimatedEndDate if sorting is "Overdue"', () => {
    const initialTaskList: ITaskList = {
      items: [
        createMockTask({ id: 1, dueDate: '2021-04-16T10:17:00.024060Z' }),
        createMockTask({ id: 2, dueDate: '2021-07-14T15:28:32.534944Z' }),
        createMockTask({ id: 3 }),
      ],
      count: 3,
      offset: 3,
    };

    const NEW_TASK_ID = 4;
    const newTask = createMockTask({ id: NEW_TASK_ID });
    const resultTaskList = getTaskListWithNewTask(initialTaskList, newTask, ETaskListSorting.Overdue);

    expect(resultTaskList.items.findIndex(task => task.id === NEW_TASK_ID)).toEqual(2);
    expect(resultTaskList.offset).toEqual(4);
    expect(resultTaskList.count).toEqual(4);
  });

  it('inserts urgent task with NO setted estimatedEndDate in the top of list if sorting is "Overdue"', () => {
    const initialTaskList: ITaskList = {
      items: [
        createMockTask({ id: 1, dueDate: '2021-04-16T10:17:00.024060Z' }),
        createMockTask({ id: 2, dueDate: '2021-07-14T15:28:32.534944Z' }),
        createMockTask({ id: 3 }),
      ],
      count: 3,
      offset: 3,
    };

    const NEW_TASK_ID = 4;
    const newTask = createMockTask({ id: NEW_TASK_ID, isUrgent: true });
    const resultTaskList = getTaskListWithNewTask(initialTaskList, newTask, ETaskListSorting.Overdue);

    expect(resultTaskList.items.findIndex(task => task.id === NEW_TASK_ID)).toEqual(0);
    expect(resultTaskList.offset).toEqual(4);
    expect(resultTaskList.count).toEqual(4);
  });

  it(
    'inserts urgent task without estimatedEndDate between urgent tasks with estimatedEndDate and not urgent tasks if sorting is "Overdue"',
    () => {
      const initialTaskList: ITaskList = {
        items: [
          createMockTask({ id: 1, isUrgent: true, dueDate: '2021-04-16T10:17:00.024060Z' }),
          createMockTask({ id: 2, dueDate: '2021-07-14T15:28:32.534944Z' }),
          createMockTask({ id: 3 }),
        ],
        count: 3,
        offset: 3,
      };

      const NEW_TASK_ID = 4;
      const newTask = createMockTask({ id: NEW_TASK_ID, isUrgent: true });
      const resultTaskList = getTaskListWithNewTask(initialTaskList, newTask, ETaskListSorting.Overdue);

      expect(resultTaskList.items.findIndex(task => task.id === NEW_TASK_ID)).toEqual(1);
      expect(resultTaskList.offset).toEqual(4);
      expect(resultTaskList.count).toEqual(4);
    });
});
