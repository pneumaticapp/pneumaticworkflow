import { runSaga } from 'redux-saga';
import { call } from 'redux-saga/effects';

import {
  fetchTasksFilterSteps,
  handleAddTask,
  handleRemoveTask,
  refreshTasksFilters,
} from '../saga';
import {
  changeTasksCount,
  insertNewTask,
  loadFilterSteps,
  loadFilterStepsFailed,
  loadFilterStepsSuccess,
  loadFilterTemplates,
  setFilterStep,
  showNewTasksNotification,
} from '../slice';
import { getTemplateSteps } from '../../../api/getTemplateSteps';
import { ETaskListCompletionStatus, ITaskListItem } from '../../../types/tasks';
import { checkSomeRouteIsActive } from '../../../utils/history';
import { initState } from '../slice';

jest.mock('../../../api/getTemplateSteps', () => ({
  getTemplateSteps: jest.fn(),
}));

jest.mock('../../templates/saga', () => ({
  handleLoadTemplateVariables: jest.fn(function* () {}),
}));

jest.mock('../../../utils/history', () => ({
  checkSomeRouteIsActive: jest.fn(),
  history: { replace: jest.fn(), location: { pathname: '/tasks' } },
}));

jest.mock('../../../utils/logger', () => ({
  logger: { info: jest.fn(), error: jest.fn() },
}));

jest.mock('../../../utils/getErrorMessage', () => ({
  getErrorMessage: jest.fn(() => 'error'),
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: {
    notifyApiError: jest.fn(),
  },
}));

interface IDispatchedAction {
  type: string;
  payload?: unknown;
}

const createTasksState = ({
  templateIdFilter = null as number | null,
  taskApiNameFilter = null as string | null,
  completionStatus = ETaskListCompletionStatus.Active,
  taskItems = [] as Partial<ITaskListItem>[],
} = {}) => ({
  tasks: {
    ...initState,
    taskList: {
      ...initState.taskList,
      count: taskItems.length,
      offset: taskItems.length,
      items: taskItems,
    },
    tasksCount: taskItems.length,
    tasksSettings: {
      ...initState.tasksSettings,
      completionStatus,
      filterValues: {
        templateIdFilter,
        taskApiNameFilter,
      },
    },
  },
  task: {
    data: null,
  },
});

const createTaskListItem = (overrides: Partial<ITaskListItem> = {}): ITaskListItem => ({
  id: 101,
  name: 'Task name',
  workflowName: 'Workflow name',
  templateId: 1,
  templateTaskApiName: 'step-1',
  dueDate: null,
  dateStarted: '2022-12-08T11:03:24.042149Z',
  dateCompleted: null,
  isUrgent: false,
  ...overrides,
});

describe('refreshTasksFilters', () => {
  it('reloads templates and steps when template filter is set', async () => {
    const dispatched: IDispatchedAction[] = [];

    function* wrapper() {
      yield call(refreshTasksFilters);
    }

    await runSaga(
      {
        dispatch: (action: IDispatchedAction) => {
          dispatched.push(action);
        },
        getState: () => createTasksState({ templateIdFilter: 7 }),
      },
      wrapper,
    ).toPromise();

    expect(dispatched).toEqual([
      loadFilterTemplates(),
      loadFilterSteps({ templateId: 7 }),
    ]);
  });

  it('reloads only templates when template filter is not set', async () => {
    const dispatched: IDispatchedAction[] = [];

    function* wrapper() {
      yield call(refreshTasksFilters);
    }

    await runSaga(
      {
        dispatch: (action: IDispatchedAction) => {
          dispatched.push(action);
        },
        getState: () => createTasksState(),
      },
      wrapper,
    ).toPromise();

    expect(dispatched).toEqual([loadFilterTemplates()]);
  });
});

describe('handleAddTask', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('skips duplicate websocket events for a task already in the list', async () => {
    (checkSomeRouteIsActive as jest.Mock).mockReturnValue(true);

    const existingTask = createTaskListItem({ id: 101 });
    const dispatched: IDispatchedAction[] = [];

    function* wrapper() {
      yield call(handleAddTask, createTaskListItem({ id: 101, name: 'Duplicate event' }));
    }

    await runSaga(
      {
        dispatch: (action: IDispatchedAction) => {
          dispatched.push(action);
        },
        getState: () =>
          createTasksState({
            taskItems: [existingTask],
          }),
      },
      wrapper,
    ).toPromise();

    expect(dispatched).toEqual([]);
    expect(dispatched).not.toContainEqual(insertNewTask(existingTask));
    expect(dispatched).not.toContainEqual(changeTasksCount(2));
    expect(dispatched).not.toContainEqual(showNewTasksNotification(true));
  });

  it('inserts a new task and refreshes filters on the Tasks page', async () => {
    (checkSomeRouteIsActive as jest.Mock).mockReturnValue(true);

    const newTask = createTaskListItem({ id: 202, templateId: 15 });
    const dispatched: IDispatchedAction[] = [];

    function* wrapper() {
      yield call(handleAddTask, newTask);
    }

    await runSaga(
      {
        dispatch: (action: IDispatchedAction) => {
          dispatched.push(action);
        },
        getState: () =>
          createTasksState({
            templateIdFilter: 15,
            taskItems: [createTaskListItem({ id: 101, templateId: 15 })],
          }),
      },
      wrapper,
    ).toPromise();

    expect(dispatched).toContainEqual(changeTasksCount(2));
    expect(dispatched).toContainEqual(showNewTasksNotification(true));
    expect(dispatched).toContainEqual(
      expect.objectContaining({
        type: 'tasks/changeTaskList',
      }),
    );
    expect(dispatched).toContainEqual(loadFilterTemplates());
    expect(dispatched).toContainEqual(loadFilterSteps({ templateId: 15 }));
  });
});

describe('handleRemoveTask', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('refreshes filters after removing a task on the Tasks page', async () => {
    (checkSomeRouteIsActive as jest.Mock).mockReturnValue(true);

    const dispatched: IDispatchedAction[] = [];

    function* wrapper() {
      yield call(handleRemoveTask, 101);
    }

    await runSaga(
      {
        dispatch: (action: IDispatchedAction) => {
          dispatched.push(action);
        },
        getState: () =>
          createTasksState({
            templateIdFilter: 15,
            taskItems: [{ id: 101 }, { id: 102 }],
          }),
      },
      wrapper,
    ).toPromise();

    expect(dispatched).toContainEqual(loadFilterTemplates());
    expect(dispatched).toContainEqual(loadFilterSteps({ templateId: 15 }));
  });

  it('does not refresh filters when not on the Tasks page', async () => {
    (checkSomeRouteIsActive as jest.Mock).mockReturnValue(false);

    const dispatched: IDispatchedAction[] = [];

    function* wrapper() {
      yield call(handleRemoveTask, 101);
    }

    await runSaga(
      {
        dispatch: (action: IDispatchedAction) => {
          dispatched.push(action);
        },
        getState: () =>
          createTasksState({
            templateIdFilter: 15,
            taskItems: [{ id: 101 }],
          }),
      },
      wrapper,
    ).toPromise();

    expect(dispatched).not.toContainEqual(loadFilterTemplates());
    expect(dispatched).not.toContainEqual(loadFilterSteps({ templateId: 15 }));
  });
});

describe('fetchTasksFilterSteps', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('clears selected step when it is no longer present in the loaded steps', async () => {
    const TEMPLATE_ID = 42;
    const steps = [{ id: 1, name: 'Step 1', apiName: 'step-1', number: 1 }];

    (getTemplateSteps as jest.Mock).mockResolvedValue(steps);

    const dispatched: IDispatchedAction[] = [];
    const action = loadFilterSteps({ templateId: TEMPLATE_ID });

    function* wrapper() {
      yield call(fetchTasksFilterSteps, action);
    }

    await runSaga(
      {
        dispatch: (actionItem: IDispatchedAction) => {
          dispatched.push(actionItem);
        },
        getState: () =>
          createTasksState({
            templateIdFilter: TEMPLATE_ID,
            taskApiNameFilter: 'obsolete-step',
          }),
      },
      wrapper,
    ).toPromise();

    expect(dispatched).toContainEqual(loadFilterStepsSuccess(steps));
    expect(dispatched).toContainEqual(setFilterStep(null));
  });

  it('ignores stale response when template filter has changed', async () => {
    const steps = [{ id: 1, name: 'Step 1', apiName: 'step-1', number: 1 }];

    (getTemplateSteps as jest.Mock).mockResolvedValue(steps);

    const dispatched: IDispatchedAction[] = [];
    const action = loadFilterSteps({ templateId: 1 });

    function* wrapper() {
      yield call(fetchTasksFilterSteps, action);
    }

    await runSaga(
      {
        dispatch: (actionItem: IDispatchedAction) => {
          dispatched.push(actionItem);
        },
        getState: () =>
          createTasksState({
            templateIdFilter: 2,
          }),
      },
      wrapper,
    ).toPromise();

    expect(dispatched).toEqual([loadFilterStepsFailed()]);
    expect(dispatched).not.toContainEqual(loadFilterStepsSuccess(steps));
  });

  it('dispatches failed action when request throws', async () => {
    (getTemplateSteps as jest.Mock).mockRejectedValue(new Error('network'));

    const dispatched: IDispatchedAction[] = [];
    const action = loadFilterSteps({ templateId: 1 });

    function* wrapper() {
      yield call(fetchTasksFilterSteps, action);
    }

    await runSaga(
      {
        dispatch: (actionItem: IDispatchedAction) => {
          dispatched.push(actionItem);
        },
        getState: () => createTasksState({ templateIdFilter: 1 }),
      },
      wrapper,
    ).toPromise();

    expect(dispatched).toContainEqual(loadFilterStepsFailed());
  });
});
