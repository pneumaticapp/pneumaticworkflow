import { select, put, call } from 'redux-saga/effects';

import { handleAddTask, handleRemoveTask, removeTaskFromList } from '../saga';
import {
  changeTasksCount,
  insertNewTask,
  loadFilterSteps,
  loadFilterTemplates,
  showNewTasksNotification,
} from '../slice';
import { getTasksSettings, getTotalTasksCount } from '../../selectors/tasks';
import { getCurrentTask } from '../../selectors/task';
import { checkSomeRouteIsActive } from '../../../utils/history';
import { ETaskListCompletionStatus, ITaskListItem } from '../../../types/tasks';
import { ERoutes } from '../../../constants/routes';

jest.mock('../../../utils/history', () => ({
  checkSomeRouteIsActive: jest.fn(),
  history: { push: jest.fn(), replace: jest.fn() },
}));

jest.mock('../../../utils/logger', () => ({
  logger: { info: jest.fn(), error: jest.fn() },
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: {
    success: jest.fn(),
    warning: jest.fn(),
    notifyApiError: jest.fn(),
  },
}));

const mockCheckRoute = checkSomeRouteIsActive as jest.Mock;

const createTask = (id: number): ITaskListItem =>
  ({
    id,
    name: 'Task',
    workflowName: 'WF',
  }) as ITaskListItem;

describe('handleRemoveTask', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('decrements counter when shouldDecrementCounter=true', () => {
    const gen = handleRemoveTask(42, true);

    expect(gen.next().value).toEqual(select(getTotalTasksCount));
    expect(gen.next(5 as never).value).toEqual(put(changeTasksCount(4)));

    mockCheckRoute.mockReturnValue(false);
    expect(gen.next().done).toBe(true);
  });

  it('does not decrement when totalTasksCount is null', () => {
    const gen = handleRemoveTask(42, true);

    expect(gen.next().value).toEqual(select(getTotalTasksCount));

    mockCheckRoute.mockReturnValue(false);
    expect(gen.next(null as never).done).toBe(true);
  });

  it('skips counter when shouldDecrementCounter=false', () => {
    const gen = handleRemoveTask(42, false);

    mockCheckRoute.mockReturnValue(false);
    expect(gen.next().done).toBe(true);
  });

  it('defaults shouldDecrementCounter to true', () => {
    const gen = handleRemoveTask(42);

    expect(gen.next().value).toEqual(select(getTotalTasksCount));
    expect(gen.next(10 as never).value).toEqual(put(changeTasksCount(9)));

    mockCheckRoute.mockReturnValue(false);
    expect(gen.next().done).toBe(true);
  });

  it('selects currentTask and removes from list on tasks route', () => {
    const gen = handleRemoveTask(42, false);

    mockCheckRoute.mockReturnValue(true);

    expect(gen.next().value).toEqual(select(getCurrentTask));

    const step = gen.next({ id: 99 } as never);
    expect(step.done).toBe(false);

    expect(gen.next().done).toBe(true);
  });
});

describe('handleAddTask', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('removes reactivated task from Completed list', () => {
    const task = createTask(42);
    const gen = handleAddTask(task);

    expect(gen.next().value).toEqual(select(getTotalTasksCount));
    expect(gen.next(3 as never).value).toEqual(put(changeTasksCount(4)));
    expect(gen.next().value).toEqual(put(showNewTasksNotification(true)));
    expect(gen.next().value).toEqual(select(getTasksSettings));

    mockCheckRoute.mockReturnValue(true);
    expect(
      gen.next({
        completionStatus: ETaskListCompletionStatus.Completed,
        filterValues: { templateIdFilter: null },
      } as never).value,
    ).toEqual(call(removeTaskFromList, task.id));
    expect(mockCheckRoute).toHaveBeenCalledWith(ERoutes.Tasks);
    expect(gen.next().done).toBe(true);
  });

  it('does not touch Completed list when Tasks route is inactive', () => {
    const task = createTask(42);
    const gen = handleAddTask(task);

    expect(gen.next().value).toEqual(select(getTotalTasksCount));
    expect(gen.next(null as never).value).toEqual(put(showNewTasksNotification(true)));
    expect(gen.next().value).toEqual(select(getTasksSettings));

    mockCheckRoute.mockReturnValue(false);
    expect(
      gen.next({
        completionStatus: ETaskListCompletionStatus.Completed,
        filterValues: { templateIdFilter: null },
      } as never).done,
    ).toBe(true);
  });

  it('inserts new task on Active list', () => {
    const task = createTask(42);
    const gen = handleAddTask(task);

    expect(gen.next().value).toEqual(select(getTotalTasksCount));
    expect(gen.next(1 as never).value).toEqual(put(changeTasksCount(2)));
    expect(gen.next().value).toEqual(put(showNewTasksNotification(true)));
    expect(gen.next().value).toEqual(select(getTasksSettings));

    mockCheckRoute.mockReturnValue(true);
    expect(
      gen.next({
        completionStatus: ETaskListCompletionStatus.Active,
        filterValues: { templateIdFilter: null },
      } as never).value,
    ).toEqual(put(insertNewTask(task)));
    expect(gen.next().value).toEqual(put(loadFilterTemplates()));
    expect(gen.next().done).toBe(true);
  });

  it('reloads filter steps when template filter is set on Active list', () => {
    const task = createTask(42);
    const gen = handleAddTask(task);

    expect(gen.next().value).toEqual(select(getTotalTasksCount));
    expect(gen.next(null as never).value).toEqual(put(showNewTasksNotification(true)));
    expect(gen.next().value).toEqual(select(getTasksSettings));

    mockCheckRoute.mockReturnValue(true);
    expect(
      gen.next({
        completionStatus: ETaskListCompletionStatus.Active,
        filterValues: { templateIdFilter: 7 },
      } as never).value,
    ).toEqual(put(insertNewTask(task)));
    expect(gen.next().value).toEqual(put(loadFilterTemplates()));
    expect(gen.next().value).toEqual(put(loadFilterSteps({ templateId: 7 })));
    expect(gen.next().done).toBe(true);
  });
});
