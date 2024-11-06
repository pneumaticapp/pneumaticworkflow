/* eslint-disable */
/* prettier-ignore */
// tslint:disable: max-file-line-count
import {
  all,
  fork,
  put,
  takeEvery,
  select,
  call,
  take,
  ActionPattern,
  ActionChannelEffect,
  actionChannel,
} from 'redux-saga/effects';
import {
  ETaskActions,
  TLoadCurrentTask,
  setCurrentTask,
  TSetTaskCompleted,
  TSetTaskReverted,
  setCurrentTaskStatus,
  ETaskStatus,
  TAddTaskPerformer,
  changeTaskPerformers,
  TRemoveTaskPerformer,
  TAddTaskGuest,
  TMarkChecklistItem,
  TUnmarkChecklistItem,
  changeChecklistItem,
  setChecklistsHandling,
  TSetChecklistsHandling,
  TSetCurrentTaskDueDate,
  patchCurrentTask,
} from './actions';
import { getTask } from '../../api/getTask';
import { ITaskAPI } from '../../types/tasks';
import { logger } from '../../utils/logger';
import { ERoutes } from '../../constants/routes';
import { NotificationManager } from '../../components/UI/Notifications';
import { history } from '../../utils/history';
import { completeTask } from '../../api/completeTask';
import { revertTask } from '../../api/revertTask';
import {
  changeWorkflowLogViewSettings,
  ETaskListActions,
  loadWorkflow,
  patchTaskInList,
  shiftTaskList,
  usersFetchFinished,
} from '../actions';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { getAuthUser, getUsers } from '../selectors/user';
import { removeOutputFromLocalStorage } from '../../components/TaskCard/utils/storageOutputs';
import { ETaskCardViewMode } from '../../components/TaskCard';
import { deleteRemovedFilesFromFields } from '../../api/deleteRemovedFilesFromFields';
import { TChannelAction } from '../tasks/saga';
import { getCurrentTask, getTaskPerformers } from '../selectors/task';
import { addTaskPerformer } from '../../api/addTaskPerformer';
import { removeTaskPerformer } from '../../api/removeTaskPerformer';
import { addTaskGuest } from '../../api/addTaskGuest';
import { removeTaskGuest } from '../../api/removeTaskGuest';
import { TUserListItem } from '../../types/user';
import { getWorkflowLog } from '../selectors/workflows';
import { EResponseStatuses } from '../../constants/defaultValues';
import { getNormalizedTask, getTaskChecklist, getTaskChecklistItem } from '../../utils/tasks';
import { markChecklistItem } from '../../api/markChecklistItem';
import { unmarkChecklistItem } from '../../api/unmarkChecklistItem';
import { deleteTaskDueDate } from '../../api/deleteTaskDueDate';
import { changeTaskDueDate } from '../../api/changeTaskDueDate';

function* fetchTask({ payload: { taskId, viewMode } }: TLoadCurrentTask) {
  const { sorting, isCommentsShown, isOnlyAttachmentsShown }: ReturnType<typeof getWorkflowLog> = yield select(
    getWorkflowLog,
  );
  const prevTask: ReturnType<typeof getCurrentTask> = yield select(getCurrentTask);
  yield put(setCurrentTask(null));

  try {
    if (!Number.isInteger(taskId)) {
      throw {
        message: 'Not found.',
        status: EResponseStatuses.NotFound,
      };
    }

    yield put(setCurrentTaskStatus(ETaskStatus.Loading));

    const task: ITaskAPI = yield getTask(taskId);
    const normalizedTask = getNormalizedTask(task);

    yield put(setCurrentTask(normalizedTask));

    const action =
      viewMode !== ETaskCardViewMode.Guest
        ? loadWorkflow(task.workflow.id)
        : changeWorkflowLogViewSettings({
            id: task.workflow.id,
            sorting,
            comments: isCommentsShown,
            isOnlyAttachmentsShown,
          });

    yield put(action);
  } catch (error) {
    yield put(setCurrentTask(prevTask));

    if (viewMode === ETaskCardViewMode.Guest) {
      history.replace(ERoutes.Error);

      return;
    }

    const isTaskNotFound = error?.status === EResponseStatuses.NotFound;
    if (isTaskNotFound && viewMode === ETaskCardViewMode.Single) {
      history.replace(ERoutes.Error);

      return;
    }

    logger.info('fetch current task error : ', error);
    NotificationManager.warning({ message: getErrorMessage(error) });
    if (viewMode === ETaskCardViewMode.Single) {
      history.replace(ERoutes.Tasks);
    }
  } finally {
    yield put(setCurrentTaskStatus(ETaskStatus.WaitingForAction));
  }
}

function* addTaskGuestSaga({
  payload: { taskId, guestEmail, onStartUploading, onEndUploading, onError },
}: TAddTaskGuest) {
  const currentUsers: ReturnType<typeof getUsers> = yield select(getUsers);

  try {
    onStartUploading?.();
    const uploadedGuest: TUserListItem = yield call(addTaskGuest, taskId, guestEmail);
    const newUsers = [...currentUsers, uploadedGuest];
    yield put(usersFetchFinished(newUsers));
    yield addPerformersToList([uploadedGuest.id]);
    onEndUploading?.();
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    onError?.();
  }
}

export function* setTaskCompleted({ payload: { taskId, workflowId, output, viewMode } }: TSetTaskCompleted) {
  const {
    authUser: { id: currentUserId },
  }: ReturnType<typeof getAuthUser> = yield select(getAuthUser);

  if (!currentUserId) {
    return;
  }

  yield put(setCurrentTaskStatus(ETaskStatus.Completing));

  // wait until checklist are handled
  const task: ReturnType<typeof getCurrentTask> = yield select(getCurrentTask);
  if (task?.areChecklistsHandling) {
    while (true) {
      const setChecklistsHandlingAction: TSetChecklistsHandling = yield take(ETaskActions.SetChecklistsHandling);
      const areChecklistsHandled = !setChecklistsHandlingAction.payload;
      if (areChecklistsHandled) {
        break;
      }
    }
  }

  try {
    yield deleteRemovedFilesFromFields(output);

    yield completeTask(workflowId, currentUserId, taskId, output);
    NotificationManager.success({ title: 'tasks.task-success-complete' });

    removeOutputFromLocalStorage(taskId);
    yield put(setCurrentTaskStatus(ETaskStatus.Completed));

    if (viewMode === ETaskCardViewMode.List) {
      yield put(shiftTaskList({ currentTaskId: taskId }));
    }

    if (viewMode === ETaskCardViewMode.Single) {
      history.push(ERoutes.Tasks);
    }
  } catch (err) {
    logger.error(err);
    NotificationManager.warning({
      title: 'tasks.task-fail-complete',
      message: getErrorMessage(err),
    });

    yield put(setCurrentTaskStatus(ETaskStatus.WaitingForAction));
  }
}

export function* setTaskReverted({ payload: { workflowId: processId, viewMode, taskId } }: TSetTaskReverted) {
  const {
    authUser: { id: currentUserId },
  }: ReturnType<typeof getAuthUser> = yield select(getAuthUser);

  if (!currentUserId) {
    return;
  }

  try {
    yield put(setCurrentTaskStatus(ETaskStatus.Returning));

    yield revertTask({ id: processId });

    NotificationManager.success({ message: 'tasks.task-success-revert' });

    if (viewMode === ETaskCardViewMode.List) {
      yield put(shiftTaskList({ currentTaskId: taskId }));
    }

    if (viewMode === ETaskCardViewMode.Single) {
      history.push(ERoutes.Tasks);
    }
  } catch (err) {
    NotificationManager.warning({
      title: 'tasks.task-fail-revert',
      message: getErrorMessage(err),
    });
  } finally {
    yield put(setCurrentTaskStatus(ETaskStatus.WaitingForAction));
  }
}

function* addPerformersToList(userIds: number[]) {
  const performers: ReturnType<typeof getTaskPerformers> = yield select(getTaskPerformers);

  const newPerformers = [...performers, ...userIds];
  yield put(changeTaskPerformers(newPerformers));
}

function* removePerformersFromList(userId: number[]) {
  const performers: ReturnType<typeof getTaskPerformers> = yield select(getTaskPerformers);

  const newPerformers = performers.filter((performerId) => !userId.includes(performerId));
  yield put(changeTaskPerformers(newPerformers));
}

function* handleChangeChecklistItem(listApiName: string, itemApiName: string, isChecked: boolean) {
  yield put(changeChecklistItem({ listApiName, itemApiName, isChecked }));

  const requestApi = isChecked ? markChecklistItem : unmarkChecklistItem;
  const task: ReturnType<typeof getCurrentTask> = yield select(getCurrentTask);
  if (!task) {
    return;
  }
  const checklist = getTaskChecklist(task, listApiName);
  const checklistItem = getTaskChecklistItem(task, listApiName, itemApiName);

  if (!checklist || !checklistItem) {
    return;
  }

  try {
    yield put(setChecklistsHandling(true));

    yield requestApi(checklist.id, checklistItem.id);
  } catch (error) {
    yield put(changeChecklistItem({ listApiName, itemApiName, isChecked: !isChecked }));
    NotificationManager.warning({ message: getErrorMessage(error) });

    logger.info('failed to change checklist item: ', error);
  } finally {
    yield put(setChecklistsHandling(false));
  }
}

function* markChecklistItemSaga({ payload: { listApiName, itemApiName } }: TMarkChecklistItem) {
  yield handleChangeChecklistItem(listApiName, itemApiName, true);
}

function* unmarkChecklistItemSaga({ payload: { listApiName, itemApiName } }: TUnmarkChecklistItem) {
  yield handleChangeChecklistItem(listApiName, itemApiName, false);
}

type TUpdateTaskPerformersActions = TAddTaskPerformer | TRemoveTaskPerformer;
export function* updatePerformersSaga({ type, payload: { taskId, userId } }: TUpdateTaskPerformersActions) {
  const users: ReturnType<typeof getUsers> = yield select(getUsers);
  const user = users.find((user) => user.id === userId);
  if (!user) {
    return;
  }

  const fetchMethodMap = [
    {
      check: () => type === ETaskActions.AddTaskPerformer && user.type === 'user',
      *fetch() {
        yield call(addTaskPerformer, taskId, userId);
      },
    },
    {
      check: () => type === ETaskActions.RemoveTaskPerformer && user.type === 'user',
      *fetch() {
        yield call(removeTaskPerformer, taskId, userId);
      },
    },
    {
      check: () => type === ETaskActions.RemoveTaskPerformer && user.type === 'guest',
      *fetch() {
        yield call(removeTaskGuest, taskId, user.email);
      },
    },
  ];

  const fetchMethod = fetchMethodMap.find(({ check }) => check())?.fetch;
  if (!fetchMethod) {
    return;
  }

  const listAction = type === ETaskActions.AddTaskPerformer ? addPerformersToList : removePerformersFromList;
  const recoverListAction = type === ETaskActions.AddTaskPerformer ? removePerformersFromList : addPerformersToList;

  try {
    yield listAction([userId]);
    yield fetchMethod();
  } catch (error) {
    yield recoverListAction([userId]);
    NotificationManager.error({ message: getErrorMessage(error) });
    logger.info('failed to update task performers: ', error);
  }
}

export function* watchSetTaskReverted() {
  yield takeEvery(ETaskActions.SetTaskReverted, function* (action: TSetTaskReverted) {
    const handlerAction: TChannelAction = {
      type: ETaskListActions.ChannelAction,
      handler: () => setTaskReverted(action),
    };
    yield put(handlerAction);
  });
}

export function* watchUpdateTaskPerformers() {
  const changePerformersChannel: ActionPattern<ActionChannelEffect> = yield actionChannel([
    ETaskActions.AddTaskPerformer,
    ETaskActions.RemoveTaskPerformer,
  ]);
  while (true) {
    const action: TUpdateTaskPerformersActions = yield take(changePerformersChannel);
    yield updatePerformersSaga(action);
  }
}

export function* setCurrentTaskDueDateSaga({ payload: dueDate }: TSetCurrentTaskDueDate) {
  const task: ReturnType<typeof getCurrentTask> = yield select(getCurrentTask);
  if (!task) return;

  try {
    yield put(patchCurrentTask({ dueDate }));
    yield put(patchTaskInList({ taskId: task.id, task: { dueDate } }));
    yield call(changeTaskDueDate, task.id, dueDate);
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.info('failed to change task due date: ', error);
    yield put(patchCurrentTask({ dueDate: task.dueDate }));
  }
}

export function* deleteCurrentTaskDueDateSaga() {
  const task: ReturnType<typeof getCurrentTask> = yield select(getCurrentTask);
  if (!task) {
    return;
  }
  try {
    yield put(patchCurrentTask({ dueDate: null }));
    yield put(patchTaskInList({ taskId: task.id, task: { dueDate: null } }));
    yield call(deleteTaskDueDate, task.id);
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.info('failed to delete task due date: ', error);
    yield put(patchCurrentTask({ dueDate: task.dueDate }));
  }
}

export function* watchLoadCurrentTask() {
  yield takeEvery(ETaskActions.LoadCurrentTask, fetchTask);
}

export function* watchAddTaskGuest() {
  yield takeEvery(ETaskActions.AddTaskGuest, addTaskGuestSaga);
}

export function* watchSetTaskCompleted() {
  yield takeEvery(ETaskActions.SetTaskCompleted, function* (action: TSetTaskCompleted) {
    const handlerAction: TChannelAction = {
      type: ETaskListActions.ChannelAction,
      handler: () => setTaskCompleted(action),
    };
    yield put(handlerAction);
  });
}

export function* watchMarkChecklistItem() {
  yield takeEvery(ETaskActions.MarkChecklistItem, markChecklistItemSaga);
}

export function* watchUnmarkChecklistItem() {
  yield takeEvery(ETaskActions.UnmarkChecklistItem, unmarkChecklistItemSaga);
}

export function* watchSetCurrentTaskDueDate() {
  yield takeEvery(ETaskActions.SetCurrentTaskDueDate, setCurrentTaskDueDateSaga);
}

export function* watchDeleteCurrentTaskDueDate() {
  yield takeEvery(ETaskActions.DeleteCurrentTaskDueDate, deleteCurrentTaskDueDateSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchLoadCurrentTask),
    fork(watchSetTaskCompleted),
    fork(watchSetTaskReverted),
    fork(watchUpdateTaskPerformers),
    fork(watchAddTaskGuest),
    fork(watchMarkChecklistItem),
    fork(watchUnmarkChecklistItem),
    fork(watchSetCurrentTaskDueDate),
    fork(watchDeleteCurrentTaskDueDate),
  ]);
}
