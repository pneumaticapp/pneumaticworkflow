/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:max-file-line-count */
import uniqBy from 'lodash.uniqby';
import {
  all,
  fork,
  put,
  takeEvery,
  select,
  takeLatest,
  call,
  take,
  throttle,
  actionChannel,
  ActionChannelEffect,
  ActionPattern,
  delay,
} from 'redux-saga/effects';

import {
  changeTaskList,
  changeTasksCount,
  TLoadTaskList,
  setTaskListDetailedTaskId,
  ETaskListActions,
  TLoadTasksFilterSteps,
  loadTasksFilterStepsFailed,
  loadTasksFilterStepsSuccess,
  showNewTasksNotification,
  insertNewTask,
  TInsertNewTask,
  loadTasksFilterTemplatesSuccess,
  loadTasksFilterTemplatesFailed,
  loadTasksFilterTemplates,
  loadTasksFilterSteps,
  setTaskListStatus,
  TShiftTaskList,
} from './actions';

import { ERoutes } from '../../constants/routes';
import { getAuthUser } from '../selectors/user';
import { getTasksCount, IGetTasksCountResponse } from '../../api/getTasksCount';
import { getUserTasks } from '../../api/getUserTasks';
import { checkSomeRouteIsActive, history } from '../../utils/history';
import { IStoreTasks } from '../../types/redux';
import { logger } from '../../utils/logger';
import { NotificationManager } from '../../components/UI/Notifications';
import {
  getTaskList,
  getTasksSearchText,
  getTasksSettings,
  getTasksSorting,
  getTasksStore,
  getTotalTasksCount,
} from '../selectors/tasks';
import { loadCurrentTask } from '../task/actions';
import { ETaskListCompletionStatus, ITaskListItem, ITemplateStep } from '../../types/tasks';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { getTemplateSteps } from '../../api/getTemplateSteps';
import { parseCookies } from '../../utils/cookie';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mergePaths } from '../../utils/urls';
import { EventChannel } from 'redux-saga';
import { createWebSocketChannel } from '../utils/createWebSocketChannel';
import { getTaskListWithNewTask } from './utils/getTaskListWithNewTask';
import { checkShouldInsertNewTask } from './utils/checkShouldInsertNewTask';
import { ITemplateTitle } from '../../types/template';
import { getTemplatesTitles } from '../../api/getTemplatesTitles';
import { handleLoadTemplateVariables } from '../templates/saga';
import { ETaskListStatus } from '../../components/Tasks/types';
import { setCurrentTask } from '../actions';
import { getCurrentTask } from '../selectors/task';
import { envWssURL } from '../../constants/enviroment';


export function* setDetailedTask(taskId: number) {
  yield put(setTaskListDetailedTaskId(taskId));
  yield put(loadCurrentTask({ taskId }));
}

export function* removeTaskFromList(taskId: number) {
  const {
    taskList: initialTaskList,
    tasksSettings: {
      filterValues: { templateIdFilter, stepIdFilter },
    },
    tasksSearchText,
  }: IStoreTasks = yield select(getTasksStore);

  const { items: tasksItems, count: tasksCount, offset: tasksOffset } = initialTaskList;

  const newTasks = tasksItems.filter((task) => task.id !== taskId);
  const isTaskRemoved = newTasks.length !== tasksItems.length;

  if (!isTaskRemoved) {
    return;
  }

  const newTaskList = {
    items: newTasks,
    count: tasksCount - 1,
    offset: tasksOffset - 1,
  };
  const withSettings = templateIdFilter || stepIdFilter || tasksSearchText;
  const emptyListStatus = withSettings ? ETaskListStatus.LastFilteredTaskFinished : ETaskListStatus.LastTaskFinished;
  yield put(changeTaskList({ taskList: newTaskList, emptyListStatus }));
}

export function* openNextTask(currentTaskId: number = -1) {
  if (!checkSomeRouteIsActive(ERoutes.Tasks)) {
    return;
  }
  yield put(setCurrentTask(null));

  const { taskList }: IStoreTasks = yield select(getTasksStore);
  const currentTaskIndex = taskList.items.findIndex((task) => task.id === currentTaskId);

  const nextTaskId = taskList.items[currentTaskIndex + 1]?.id || taskList.items[0]?.id;
  if (!nextTaskId || currentTaskId === nextTaskId) {
    return;
  }
  yield setDetailedTask(nextTaskId);
}

function* fetchTaskList(offset: number, nextStatus: ETaskListStatus) {
  const {
    taskList,
    tasksSettings: {
      sorting,
      completionStatus,
      filterValues: { templateIdFilter, stepIdFilter },
    },
  }: IStoreTasks = yield select(getTasksStore);
  const isEmptyList = offset === 0;
  const {
    authUser: { id, isAdmin },
  }: ReturnType<typeof getAuthUser> = yield select(getAuthUser);
  const searchText: ReturnType<typeof getTasksSearchText> = yield select(getTasksSearchText);
  yield put(setTaskListStatus(nextStatus));

  try {
    const { count, results } = yield getUserTasks({
      id: isAdmin ? id : 0,
      offset,
      sorting,
      searchText,
      templateId: templateIdFilter,
      templateStepId: stepIdFilter,
      status: completionStatus,
    });

    const items: ITaskListItem[] = !isEmptyList ? uniqBy([...taskList.items, ...results], 'id') : results;

    const withSettings = templateIdFilter || stepIdFilter || searchText;
    const emptyListStatus = withSettings ? ETaskListStatus.EmptySearchResult : ETaskListStatus.NoTasks;
    yield put(changeTaskList({ taskList: { count, offset, items }, emptyListStatus }));

    if (isEmptyList) {
      yield openNextTask();
    }
  } catch (error) {
    logger.info('fetch process task list error : ', error);
    yield put(setTaskListStatus(ETaskListStatus.WaitingForAction));
    NotificationManager.error({ message: 'workflows.fetch-tasks-fail' });
    history.replace(ERoutes.Tasks);
  }
}

function* fetchTasksCount() {
  try {
    const response: IGetTasksCountResponse | undefined = yield getTasksCount();
    if (response) {
      const { tasksCount } = response;
      yield put(changeTasksCount(tasksCount));
    }
  } catch (error) {
    logger.info('fetch tasks count error : ', error);
    NotificationManager.error({ message: 'workflows.load-tasks-count-fail' });
  }
}

export function* handleSearchTasks() {
  yield put(setTaskListStatus(ETaskListStatus.Searching));
  yield delay(500);
  yield fetchTaskList(0, ETaskListStatus.Searching);
}

export function* handleInsertNewTask({ payload: newTask }: TInsertNewTask) {
  const tasksSettings: ReturnType<typeof getTasksSettings> = yield select(getTasksSettings);
  const searchText: ReturnType<typeof getTasksSearchText> = yield select(getTasksSearchText);
  if (!checkShouldInsertNewTask(newTask, tasksSettings, searchText)) {
    return;
  }

  const initialTaskList: ReturnType<typeof getTaskList> = yield select(getTaskList);
  const tasksSorting: ReturnType<typeof getTasksSorting> = yield select(getTasksSorting);

  const newTaskList = getTaskListWithNewTask(initialTaskList, newTask, tasksSorting);
  yield put(changeTaskList({ taskList: newTaskList }));

  if (newTaskList.count === 1) {
    yield openNextTask();
  }
}

export function* fetchTasksFilterTemplates() {
  try {
    const {
      tasksSettings: { completionStatus },
    }: IStoreTasks = yield select(getTasksStore);
    const templates: ITemplateTitle[] = yield getTemplatesTitles({
      withTasksInProgress: completionStatus === ETaskListCompletionStatus.Active,
    });
    yield put(loadTasksFilterTemplatesSuccess(templates));
  } catch (error) {
    yield put(loadTasksFilterTemplatesFailed());
    logger.info('fetch tasks filter templates error : ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

function* fetchTasksFilterSteps({ payload: { templateId } }: TLoadTasksFilterSteps) {
  try {
    const {
      tasksSettings: { completionStatus },
    }: IStoreTasks = yield select(getTasksStore);
    const [steps]: [ITemplateStep[]] = yield all([
      call(getTemplateSteps, {
        id: templateId,
        withTasksInProgress: completionStatus === ETaskListCompletionStatus.Active,
      }),
      handleLoadTemplateVariables(templateId),
    ]);
    yield put(loadTasksFilterStepsSuccess(steps));
  } catch (error) {
    put(loadTasksFilterStepsFailed());
    logger.info('fetch tasks filter steps error : ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

function* handleShiftTaskList({ payload: { currentTaskId } }: TShiftTaskList) {
  yield openNextTask(currentTaskId);
  yield removeTaskFromList(currentTaskId);
}

export function* watchFetchTaskList() {
  yield takeEvery(ETaskListActions.LoadTaskList, function* ({ payload: offset }: TLoadTaskList) {
    yield fetchTaskList(offset, ETaskListStatus.Loading);
  });
}

export function* watchFetchTasksCount() {
  yield takeEvery(ETaskListActions.LoadTasksCount, fetchTasksCount);
}

export function* watchSearchTasks() {
  yield takeLatest(ETaskListActions.SearchTasks, handleSearchTasks);
}

export function* watchLoadTasksFilterTemplates() {
  yield takeEvery(ETaskListActions.LoadFilterTemplates, fetchTasksFilterTemplates);
}

export function* watchLoadTasksFilterSteps() {
  yield throttle(500, ETaskListActions.LoadFilterSteps, fetchTasksFilterSteps);
}

export function* watchInsertNewTask() {
  yield takeEvery(ETaskListActions.InsertNewTask, handleInsertNewTask);
}

export function* watchShiftTaskList() {
  yield takeLatest(ETaskListActions.ShiftTaskList, handleShiftTaskList);
}

export function* watchNewTask() {
  const {
    api: { wsPublicUrl, urls },
  } = getBrowserConfigEnv();
  const url = mergePaths(envWssURL || wsPublicUrl, `${urls.wsNewTask}?auth_token=${parseCookies(document.cookie).token}`);
  const channel: EventChannel<ITaskListItem> = yield call(createWebSocketChannel, url);

  while (true) {
    const newTask: ITaskListItem = yield take(channel);
    const handlerAction: TChannelAction = {
      type: ETaskListActions.ChannelAction,
      handler: () => handleAddTask(newTask),
    };
    yield put(handlerAction);
  }
}

function* handleAddTask(newTask: ITaskListItem) {
  const totalTasksCount: ReturnType<typeof getTotalTasksCount> = yield select(getTotalTasksCount);
  if (totalTasksCount !== null) {
    yield put(changeTasksCount(totalTasksCount + 1));
  }

  yield put(showNewTasksNotification(true));

  const settings: ReturnType<typeof getTasksSettings> = yield select(getTasksSettings);
  const {
    completionStatus,
    filterValues: { templateIdFilter },
  } = settings;
  if (completionStatus === ETaskListCompletionStatus.Completed) {
    return;
  }
  if (!checkSomeRouteIsActive(ERoutes.Tasks)) {
    return;
  }

  yield put(insertNewTask(newTask));
  yield put(loadTasksFilterTemplates());
  if (templateIdFilter) {
    yield put(loadTasksFilterSteps({ templateId: templateIdFilter }));
  }
}

export function* watchRemoveTask() {
  const {
    api: { wsPublicUrl, urls },
  } = getBrowserConfigEnv();
  const url = mergePaths(envWssURL || wsPublicUrl, `${urls.wsRemovedTask}?auth_token=${parseCookies(document.cookie).token}`);
  const channel: EventChannel<ITaskListItem> = yield call(createWebSocketChannel, url);

  while (true) {
    const removedTask: ITaskListItem = yield take(channel);
    yield put({
      type: ETaskListActions.ChannelAction,
      handler: () => {
        return handleRemoveTask(removedTask.id);
      },
    });
  }
}

function* handleRemoveTask(taskId: number) {
  const totalTasksCount: ReturnType<typeof getTotalTasksCount> = yield select(getTotalTasksCount);
  if (totalTasksCount !== null) {
    yield put(changeTasksCount(totalTasksCount - 1));
  }

  if (!checkSomeRouteIsActive(ERoutes.Tasks)) {
    return;
  }

  const currentTask: ReturnType<typeof getCurrentTask> = yield select(getCurrentTask);
  if (currentTask?.id === taskId) {
    yield openNextTask(currentTask.id);
  }

  yield removeTaskFromList(taskId);
}

export type TChannelAction = { type: string; handler(): void };
export function* watchTasksListChannelActions() {
  const channel: ActionPattern<ActionChannelEffect> = yield actionChannel(ETaskListActions.ChannelAction);
  while (true) {
    const { handler }: TChannelAction = yield take(channel);
    yield handler();
  }
}

export function* rootSaga() {
  yield all([
    fork(watchFetchTaskList),
    fork(watchFetchTasksCount),
    fork(watchSearchTasks),
    fork(watchLoadTasksFilterSteps),
    fork(watchInsertNewTask),
    fork(watchLoadTasksFilterTemplates),
    fork(watchTasksListChannelActions),
    fork(watchShiftTaskList),
  ]);
}
