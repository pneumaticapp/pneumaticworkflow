import uniqBy from 'lodash.uniqby';
import { all, fork, put, takeEvery, select, takeLatest, call, delay, take, takeLeading } from 'redux-saga/effects';
import { EventChannel } from 'redux-saga';

import {
  changeWorkflowsList,
  changeWorkflow,
  changeWorkflowLog,
  loadWorkflowsListFailed,
  setWorkflowIsLoading,
  TChangeWorkflowLogViewSettings,
  TLoadWorkflowsList,
  TLoadWorkflow,
  loadWorkflowsList,
  TWorkflowFinished,
  TEditWorkflow,
  TSendWorkflowLogComment,
  setIsEditKickoff,
  setIsEditWorkflowName,
  setIsSavingWorkflowName,
  setIsSavingKickoff,
  editWorkflowSuccess,
  setWorkflowEdit,
  loadWorkflowsFilterTemplatesSuccess,
  loadWorkflowsFilterTemplatesFailed,
  TDeleteWorkflow,
  openRunWorkflowModal,
  loadWorkflowsFilterStepsSuccess,
  ETaskListActions,
  setGeneralLoaderVisibility,
  setCurrentTask,
  patchTaskInList,
  updateTaskWorkflowLogItem,
} from '../actions';

import {
  IWorkflowLogItem,
  EWorkflowsLogSorting,
  EWorkflowsStatus,
  TUserCounter,
  TTemplateStepCounter,
  EWorkflowStatus,
  TWorkflowResponse,
  TWorkflowDetailsResponse,
  IWorkflowClient,
  IWorkflowDetailsClient,
  EWorkflowTaskStatus,
  IWorkflowTaskClient,
} from '../../types/workflow';
import { ERoutes } from '../../constants/routes';
import { getWorkflowsStore, getWorkflowsSearchText, getWorkflowsStatus, getTaskStore } from '../selectors/workflows';
import { getEditKickoff, mapFilesToRequest } from '../../utils/workflows';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { getWorkflows } from '../../api/getWorkflows';
import { getWorkflow } from '../../api/getWorkflow';
import { getWorkflowLog } from '../../api/getWorkflowLog';
import { returnWorkflowToTask } from '../../api/returnWorkflowToTask';
import { history } from '../../utils/history';
import { IStoreTask, IStoreWorkflows } from '../../types/redux';
import { logger } from '../../utils/logger';
import { NotificationManager } from '../../components/UI/Notifications';
import { sendWorkflowComment } from '../../api/sendWorkflowComment';
import { finishWorkflow } from '../../api/finishWorkflow';
import { editWorkflow, IEditWorkflowResponse } from '../../api/editWorkflow';
import { getTemplatesTitles } from '../../api/getTemplatesTitles';
import { IKickoff, ITemplateResponse, ITemplateTitle } from '../../types/template';
import { getWorkflowLogStore } from '../selectors/workflowLog';
import { deleteRemovedFilesFromFields } from '../../api/deleteRemovedFilesFromFields';
import { TChannelAction } from '../tasks/saga';
import { ITemplateStep } from '../../types/tasks';
import { getTemplateSteps } from '../../api/getTemplateSteps';
import {
  loadWorkflowsFilterStepsFailed,
  TCloneWorkflow,
  TReturnWorkflowToTask,
  closeWorkflowLogPopup,
  TOpenWorkflowLogPopup,
  setCurrentPerformersCounters,
  setWorkflowStartersCounters,
  TWorkflowResumed,
  TLoadWorkflowsFilterSteps,
  setWorkflowsTemplateStepsCounters,
  TSnoozeWorkflow,
  patchWorkflowInList,
  patchWorkflowDetailed,
  EWorkflowsActions,
  TDeleteComment,
  updateWorkflowLogItem,
  TEditComment,
  TWatchedComment,
  TDeleteReactionComment,
  TCreateReactionComment,
} from './actions';
import { handleLoadTemplateVariables } from '../templates/saga';

import { deleteWorkflow } from '../../api/deleteWorkflow';
import { getTemplate } from '../../api/getTemplate';
import { getRunnableWorkflow } from '../../components/TemplateEdit/utils/getRunnableWorkflow';
import { getClonedKickoff } from '../../components/Workflows/WorkflowsGridPage/WorkflowCard/utils/getClonedKickoff';
import { getWorkflowsCurrentPerformerCounters } from '../../api/getWorkflowsCurrentPerformerCounters';
import { getWorkflowsStartersCounters } from '../../api/getWorkflowsStartersCounters';
import { continueWorkflow } from '../../api/continueWorkflow';
import { getWorkflowsTemplateStepsCounters } from '../../api/getWorkflowsTemplateStepsCounters';
import { snoozeWorkflow } from '../../api/snoozeWorkflow';
import { deleteComment } from '../../api/workflows/deleteComment';
import { editComment } from '../../api/workflows/editComment';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mergePaths } from '../../utils/urls';
import { parseCookies } from '../../utils/cookie';
import { createWebSocketChannel } from '../utils/createWebSocketChannel';
import { deleteReactionComment } from '../../api/workflows/deleteReactionComment';
import { createReactionComment } from '../../api/workflows/createReactionComment';
import { watchedComment } from '../../api/workflows/watchedComment';
import { envWssURL } from '../../constants/enviroment';
import {
  mapBackandworkflowLogToRedux,
  mapBackendWorkflowToRedux,
  mapBackendNewEventToRedux,
  formatDueDateToEditWorkflow,
  mapWorkflowsToISOStringToRedux,
  mapWorkflowsAddComputedPropsToRedux,
} from '../../utils/mappers';
import { getUserTimezone } from '../selectors/user';
import { getCurrentTask } from '../selectors/task';
import { formatDateToISOInWorkflow } from '../../utils/dateTime';
import { getWorkflowAddComputedPropsToRedux } from '../../components/Workflows/utils/getWorfkflowClientProperties';

function* handleLoadWorkflow({ workflowId, showLoader = true }: { workflowId: number; showLoader?: boolean }) {
  const {
    workflowLog: { isCommentsShown, sorting },
  }: IStoreWorkflows = yield select(getWorkflowsStore);

  try {
    if (showLoader) {
      yield put(setWorkflowIsLoading(true));
    }

    const [workflow, workflowLog]: [TWorkflowDetailsResponse, IWorkflowLogItem[]] = yield all([
      getWorkflow(workflowId),
      getWorkflowLog({
        workflowId,
        sorting,
        comments: isCommentsShown,
      }),
    ]);

    const timezone: ReturnType<typeof getUserTimezone> = yield select(getUserTimezone);
    const formattedWorkflowLog = mapBackandworkflowLogToRedux(workflowLog, timezone);

    const formattedKickoffWorkflow = mapBackendWorkflowToRedux(workflow, timezone);
    const formattedDueDateWorkflow = formatDateToISOInWorkflow(formattedKickoffWorkflow);
    const formattedWorkflow = getWorkflowAddComputedPropsToRedux(formattedDueDateWorkflow) as IWorkflowDetailsClient;

    yield put(changeWorkflow(formattedWorkflow));
    yield put(changeWorkflowLog({ items: formattedWorkflowLog, workflowId }));
  } catch (error) {
    logger.info('fetch prorcess error : ', error);
    throw error;
  } finally {
    if (showLoader) {
      yield put(setWorkflowIsLoading(false));
    }
  }
}

function* fetchWorkflow({ payload: id }: TLoadWorkflow) {
  try {
    yield fork(handleLoadWorkflow, { workflowId: id });
  } catch (error) {
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

function* handleOpenWorkflowLogPopup({
  payload: { workflowId, shouldSetWorkflowDetailUrl, redirectTo404IfNotFound },
}: TOpenWorkflowLogPopup) {
  try {
    if (shouldSetWorkflowDetailUrl) {
      const newUrl = ERoutes.WorkflowDetail.replace(':id', String(workflowId)) + history.location.search;
      window.history.replaceState(null, '', newUrl);
    }

    yield handleLoadWorkflow({ workflowId });
  } catch (error) {
    yield put(closeWorkflowLogPopup());
    if (redirectTo404IfNotFound && error?.status === 404) {
      history.push(ERoutes.Error);

      return;
    }

    if (shouldSetWorkflowDetailUrl) {
      history.push(ERoutes.Workflows);
    }

    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

function* fetchWorkflowLog({
  payload: { id, sorting, comments, isOnlyAttachmentsShown },
}: TChangeWorkflowLogViewSettings) {
  yield put(changeWorkflowLog({ isLoading: true }));

  try {
    const timezone: ReturnType<typeof getUserTimezone> = yield select(getUserTimezone);
    const fetchedProcessLog: IWorkflowLogItem[] = yield getWorkflowLog({
      workflowId: id,
      sorting,
      comments,
      isOnlyAttachmentsShown,
    });
    const formattedFetchedProcessLog = mapBackandworkflowLogToRedux(fetchedProcessLog, timezone);

    yield put(changeWorkflowLog({ workflowId: id, items: formattedFetchedProcessLog }));
  } catch (error) {
    logger.info('fetch process log error : ', error);
    NotificationManager.error({ message: 'workflows.fetch-in-work-process-log-fail' });
  } finally {
    yield put(changeWorkflowLog({ isLoading: false }));
  }
}

function* fetchWorkflowsList({ payload: offset = 0 }: TLoadWorkflowsList) {
  const {
    workflowsList,
    workflowsSettings: {
      sorting,
      values: {
        statusFilter,
        templatesIdsFilter,
        stepsIdsFilter,
        performersIdsFilter,
        performersGroupIdsFilter,
        workflowStartersIdsFilter,
      },
    },
  }: IStoreWorkflows = yield select(getWorkflowsStore);

  const searchText: ReturnType<typeof getWorkflowsSearchText> = yield select(getWorkflowsSearchText);

  try {
    const { count, results }: { count: number; results: TWorkflowResponse[] } = yield getWorkflows({
      offset,
      sorting,
      statusFilter,
      templatesIdsFilter,
      performersGroupIdsFilter,
      stepsIdsFilter,
      performersIdsFilter,
      workflowStartersIdsFilter,
      searchText,
    });
    const formattedResults = mapWorkflowsToISOStringToRedux(results);
    const items = offset > 0 ? uniqBy([...workflowsList.items, ...formattedResults], 'id') : formattedResults;

    yield put(changeWorkflowsList({ count, offset, items: mapWorkflowsAddComputedPropsToRedux(items) }));
  } catch (error) {
    logger.info('fetch workflows list error : ', error);
    yield put(loadWorkflowsListFailed());
    NotificationManager.error({ message: 'workflows.fetch-processes-list-fail' });
  }
}

function* saveWorkflowLogComment({ payload: { text, attachments } }: TSendWorkflowLogComment) {
  const {
    items,
    workflowId: processId,
    sorting,
  }: ReturnType<typeof getWorkflowLogStore> = yield select(getWorkflowLogStore);

  if (!processId) {
    return;
  }

  const normalizedAttachments = mapFilesToRequest(attachments);

  try {
    yield put(setGeneralLoaderVisibility(true));
    const newComment: IWorkflowLogItem = yield sendWorkflowComment({
      id: processId,
      text,
      attachments: normalizedAttachments,
    });

    const preLoadedProcessLogMap = {
      [EWorkflowsLogSorting.New]: [newComment, ...items],
      [EWorkflowsLogSorting.Old]: [...items, newComment],
    };

    const preLoadedProcessLog = preLoadedProcessLogMap[sorting];

    yield put(changeWorkflowLog({ items: preLoadedProcessLog }));
  } catch (error) {
    logger.info('send process log comment error:', error);
    NotificationManager.error({ message: 'workflows.send-process-log-comment-fail' });
    yield put(changeWorkflowLog({ items }));
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* editWorkflowInWork({ payload }: TEditWorkflow) {
  const {
    workflowsList: { items, count, offset },
  }: ReturnType<typeof getWorkflowsStore> = yield select(getWorkflowsStore);
  const { name, kickoff, isUrgent, dueDate } = payload;

  if (name) yield put(setIsSavingWorkflowName(true));
  if (kickoff) yield put(setIsSavingKickoff(true));

  yield deleteRemovedFilesFromFields(payload.kickoff?.fields);

  try {
    yield put(setGeneralLoaderVisibility(true));

    const changedFields = {
      ...(typeof isUrgent !== 'undefined' && { isUrgent }),
      ...(typeof name !== 'undefined' && { name }),
      ...(typeof dueDate !== 'undefined' && { dueDate }),
    };

    yield put(
      patchWorkflowInList({
        workflowId: payload.workflowId,
        changedFields,
      }),
    );

    yield put(
      patchWorkflowDetailed({
        workflowId: payload.workflowId,
        changedFields,
      }),
    );

    const formattedPayload = formatDueDateToEditWorkflow(payload);
    const editedWorkflow: IEditWorkflowResponse = yield editWorkflow(formattedPayload);
    const formattedEditedWorkflow = formatDateToISOInWorkflow(editedWorkflow);
    const formattedWorkflow = getWorkflowAddComputedPropsToRedux(formattedEditedWorkflow) as IWorkflowDetailsClient;

    const newEditingProcess = {
      name: formattedEditedWorkflow.name,
      kickoff: getEditKickoff(formattedEditedWorkflow.kickoff),
    };

    const task: ReturnType<typeof getCurrentTask> = yield select(getCurrentTask);
    const worlflowActiveTasks = formattedWorkflow.tasks.filter(
      (localTask: IWorkflowTaskClient) => localTask.status === EWorkflowTaskStatus.Active,
    );
    yield put(setWorkflowEdit(newEditingProcess));
    yield put(changeWorkflow(formattedWorkflow));
    if (typeof isUrgent !== 'undefined' && task && payload.workflowId === task.workflow.id) {
      yield put(setCurrentTask({ ...task, isUrgent }));
      yield all(
        worlflowActiveTasks.map((localTask) =>
          put(
            patchTaskInList({
              taskId: localTask.id,
              task: { ...localTask, dateStarted: localTask.dateStarted || undefined, isUrgent },
            }),
          ),
        ),
      );
    }
    // yield put(loadWorkflowsList(0));
    yield updateDetailedWorkflow(payload.workflowId);

    if (typeof isUrgent === 'undefined') {
      NotificationManager.success({ message: 'workflows.edit-success' });
    }

    if (name) {
      yield put(setIsEditWorkflowName(false));
    }

    if (kickoff) {
      yield put(setIsEditKickoff(false));
    }
  } catch (error) {
    logger.info('edit workflow error : ', error);
    const errorMessage = getErrorMessage(error);

    NotificationManager.warning({
      message: errorMessage,
    });

    yield put(changeWorkflowsList({ items, count, offset }));
  } finally {
    yield put(setIsSavingWorkflowName(false));
    yield put(setIsSavingKickoff(false));
    yield put(editWorkflowSuccess());
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* setWorkflowResumedSaga({ payload: { workflowId, onSuccess } }: TWorkflowResumed) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    const workflow: IEditWorkflowResponse = yield continueWorkflow(workflowId);
    const normilizedWorkflow: IWorkflowClient = getWorkflowAddComputedPropsToRedux(formatDateToISOInWorkflow(workflow));
    yield put(
      patchWorkflowInList({
        workflowId,
        changedFields: {
          status: EWorkflowStatus.Running,
          tasks: normilizedWorkflow.tasks,
          minDelay: normilizedWorkflow.minDelay,
        },
      }),
    );

    yield updateDetailedWorkflow(workflowId);
    onSuccess?.();

    NotificationManager.success({ title: 'task.resume-process-success' });
  } catch (err) {
    NotificationManager.warning({ title: 'task.resume-process-fail' });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* setWorkflowFinishedSaga({ payload: { workflowId, onWorkflowEnded } }: TWorkflowFinished) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield finishWorkflow({ id: workflowId });
    NotificationManager.success({ title: 'task.complete-process-success' });

    yield updateDetailedWorkflow(workflowId);
    onWorkflowEnded?.();
  } catch (err) {
    NotificationManager.warning({
      title: 'task.complete-process-fail',
      message: getErrorMessage(err),
    });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* fetchFilterTemplates() {
  try {
    const workflowStatus: EWorkflowsStatus = yield select(getWorkflowsStatus);
    const templatesTitles: ITemplateTitle[] = yield getTemplatesTitles({
      workflowStatus,
    });
    yield put(loadWorkflowsFilterTemplatesSuccess(templatesTitles));
  } catch (err) {
    yield put(loadWorkflowsFilterTemplatesFailed());
    logger.info('fetch workflow titles error : ', err);
    NotificationManager.error({ message: 'workflows.load-tasks-count-fail' });
  }
}

export function* deleteWorkflowSaga({ payload: { workflowId, onSuccess } }: TDeleteWorkflow) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield deleteWorkflow(workflowId);
    NotificationManager.success({ title: 'templates.delete-success' });
    yield put(closeWorkflowLogPopup());
    onSuccess?.();
  } catch (err) {
    NotificationManager.warning({
      title: 'templates.delete-failed',
      message: getErrorMessage(err),
    });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* returnWorkflowToTaskSaga({ payload: { workflowId, taskId, onSuccess } }: TReturnWorkflowToTask) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield returnWorkflowToTask({ id: workflowId, taskId });
    yield put(loadWorkflowsList(0));
    yield updateDetailedWorkflow(workflowId);
    onSuccess?.();
  } catch (err) {
    NotificationManager.warning({
      id: 'workflows.card-return-failed',
      message: getErrorMessage(err),
    });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* cloneWorkflowSaga({ payload: { workflowId, workflowName, templateId } }: TCloneWorkflow) {
  try {
    yield put(setGeneralLoaderVisibility(true));

    if (!templateId) {
      throw new Error('no template id');
    }

    const [workflowDetails, template]: [TWorkflowDetailsResponse, ITemplateResponse] = yield all([
      getWorkflow(workflowId),
      getTemplate(templateId),
    ]);
    const formattedworkflowDetails = formatDateToISOInWorkflow(workflowDetails);
    if (!formattedworkflowDetails || !template) {
      throw new Error('failed to prepare runnable workflow object');
    }

    const runnableWorkflow = getRunnableWorkflow(template);
    if (!runnableWorkflow) {
      return;
    }

    const kickoff: IKickoff = yield getClonedKickoff(formattedworkflowDetails.kickoff, template.kickoff);

    yield put(
      openRunWorkflowModal({
        ...runnableWorkflow,
        name: `${workflowName} (Clone)`,
        kickoff,
      }),
    );
  } catch (error) {
    logger.info('clone workflow error : ', error);

    NotificationManager.error({
      title: 'workflows.fail-copy',
    });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* fetchFilterSteps({ payload: { templateId, onAfterLoaded } }: TLoadWorkflowsFilterSteps) {
  try {
    const [steps]: [ITemplateStep[]] = yield all([
      call(getTemplateSteps, { id: templateId }),
      handleLoadTemplateVariables(templateId),
    ]);

    yield put(loadWorkflowsFilterStepsSuccess({ templateId, steps }));

    onAfterLoaded?.(steps);
  } catch (error) {
    yield put(loadWorkflowsFilterStepsFailed({ templateId }));
    logger.info('fetch tasks filter steps error : ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

export function* updateCurrentPerformersCountersSaga() {
  const {
    workflowsSettings: {
      values: { templatesIdsFilter, stepsIdsFilter, workflowStartersIdsFilter },
    },
  }: IStoreWorkflows = yield select(getWorkflowsStore);

  try {
    const counters: TUserCounter[] | undefined = yield call(getWorkflowsCurrentPerformerCounters, {
      templatesIdsFilter,
      stepsIdsFilter,
      workflowStartersIdsFilter,
    });

    if (!counters) {
      return;
    }

    yield put(setCurrentPerformersCounters(counters));
  } catch (error) {
    logger.error('failed to get workflows current performer counters ', error);
  }
}

export function* updateWorkflowStartersCountersSaga() {
  const {
    workflowsSettings: {
      values: { statusFilter, templatesIdsFilter, performersIdsFilter },
    },
  }: IStoreWorkflows = yield select(getWorkflowsStore);

  try {
    const counters: TUserCounter[] | undefined = yield call(getWorkflowsStartersCounters, {
      statusFilter,
      templatesIdsFilter,
      performersIdsFilter,
    });

    if (!counters) {
      return;
    }

    yield put(setWorkflowStartersCounters(counters));
  } catch (error) {
    logger.error('failed to get workflows starters counters ', error);
  }
}

export function* updateWorkflowsTemplateStepsCountersSaga() {
  const {
    workflowsSettings: {
      templateList,
      values: { statusFilter, performersIdsFilter, performersGroupIdsFilter, workflowStartersIdsFilter },
    },
  }: IStoreWorkflows = yield select(getWorkflowsStore);
  const allTemplatesIds = templateList.items.map((template) => template.id);

  try {
    const counters: TTemplateStepCounter[] | undefined = yield call(getWorkflowsTemplateStepsCounters, {
      statusFilter,
      templatesIdsFilter: allTemplatesIds,
      performersIdsFilter,
      performersGroupIdsFilter,
      workflowStartersIdsFilter,
    });

    if (!counters) {
      return;
    }

    yield put(setWorkflowsTemplateStepsCounters(counters));
  } catch (error) {
    logger.error('failed to get workflows starters counters ', error);
  }
}

export function* snoozeWorkflowSaga({ payload: { workflowId, date, onSuccess } }: TSnoozeWorkflow) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    const workflow: IEditWorkflowResponse = yield call(snoozeWorkflow, workflowId, date);
    const normilizedWorkflow: IWorkflowClient = getWorkflowAddComputedPropsToRedux(formatDateToISOInWorkflow(workflow));
    yield put(
      patchWorkflowInList({
        workflowId: workflow.id,
        changedFields: {
          status: EWorkflowStatus.Snoozed,
          minDelay: normilizedWorkflow.minDelay,
          tasks: normilizedWorkflow.tasks,
        },
      }),
    );

    yield updateDetailedWorkflow(workflowId);

    onSuccess?.(normilizedWorkflow);
  } catch (error) {
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to snooze a workflow ', error);
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* updateDetailedWorkflow(workflowId: number) {
  const { workflow }: ReturnType<typeof getWorkflowsStore> = yield select(getWorkflowsStore);

  if (workflow?.id !== workflowId) {
    return;
  }

  yield handleLoadWorkflow({ workflowId, showLoader: false });
}

export function* handleApplyFilters() {
  yield delay(700);
  yield put(loadWorkflowsList(0));
}

export function* watchFetchWorkflowsList() {
  yield takeLeading(EWorkflowsActions.LoadWorkflowsList, fetchWorkflowsList);
}

export function* watchChangeWorkflowLogViewSettings() {
  yield takeLatest(EWorkflowsActions.ChangeWorkflowLogViewSettings, fetchWorkflowLog);
}

export function* watchOpenWorkflowLogPopup() {
  yield takeEvery(EWorkflowsActions.OpenWorkflowLogPopup, handleOpenWorkflowLogPopup);
}

export function* watchFetchWorkflow() {
  yield takeLatest(EWorkflowsActions.LoadWorkflow, fetchWorkflow);
}

export function* watchEidtWorkflow() {
  yield takeEvery(EWorkflowsActions.EditWorkflow, editWorkflowInWork);
}

export function* watchSetWorkflowResumed() {
  yield takeEvery(EWorkflowsActions.SetWorkflowResumed, setWorkflowResumedSaga);
}

export function* handleSearchTextChanged() {
  yield delay(300);
  yield put(loadWorkflowsList(0));
}

export function* watchSetWorkflowFinished() {
  yield takeEvery(EWorkflowsActions.SetWorkflowFinished, function* finishedWorkflow(action: TWorkflowFinished) {
    const handlerAction: TChannelAction = {
      type: ETaskListActions.ChannelAction,
      handler: () => setWorkflowFinishedSaga(action),
    };
    yield put(handlerAction);
  });
}

export function* deleteCommentSaga({ payload: { id } }: TDeleteComment) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    const updateComment: IWorkflowLogItem = yield deleteComment({ id });
    yield put(updateWorkflowLogItem(updateComment));
    yield put(updateTaskWorkflowLogItem(updateComment));
  } catch (err) {
    NotificationManager.error({ message: getErrorMessage(err) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* editCommentSaga({ payload: { id, text, attachments } }: TEditComment) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    const updateComment: IWorkflowLogItem = yield editComment({ id, text, attachments });
    yield put(updateWorkflowLogItem(updateComment));
    yield put(updateTaskWorkflowLogItem(updateComment));
  } catch (err) {
    NotificationManager.error({ message: getErrorMessage(err) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* watchNewWorkflowsEvent() {
  const {
    api: { wsPublicUrl, urls },
  } = getBrowserConfigEnv();
  const url = mergePaths(
    envWssURL || wsPublicUrl,
    `${urls.wsWorkflowsEvent}?auth_token=${parseCookies(document.cookie).token}`,
  );
  const channel: EventChannel<IWorkflowLogItem> = yield call(createWebSocketChannel, url);

  while (true) {
    const newEvent: IWorkflowLogItem = yield take(channel);
    const timezone: ReturnType<typeof getUserTimezone> = yield select(getUserTimezone);
    const { data }: IStoreTask = yield select(getTaskStore);
    const { workflow }: IStoreTask = yield select(getWorkflowsStore);

    const formattedNewEvent: IWorkflowLogItem = mapBackendNewEventToRedux(newEvent, timezone);

    if (newEvent.workflowId === data?.workflow.id || newEvent?.workflowId === workflow?.id) {
      yield put(updateWorkflowLogItem(formattedNewEvent));
      yield put(updateTaskWorkflowLogItem(formattedNewEvent));
    }
  }
}

export function* watchedCommentSaga({ payload: { id } }: TWatchedComment) {
  try {
    yield watchedComment({ id });
  } catch (err) {
    NotificationManager.error({ message: getErrorMessage(err) });
  }
}

export function* deleteReactionCommentSaga({ payload: { id, value } }: TDeleteReactionComment) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield deleteReactionComment({ id, value });
  } catch (err) {
    NotificationManager.error({ message: getErrorMessage(err) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* createReactionCommentSaga({ payload: { id, value } }: TCreateReactionComment) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield createReactionComment({ id, value });
  } catch (err) {
    NotificationManager.error({ message: getErrorMessage(err) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* watchDeleteReactionComment() {
  yield takeEvery(EWorkflowsActions.DeleteReactionComment, deleteReactionCommentSaga);
}

export function* watchCreateReactionComment() {
  yield takeEvery(EWorkflowsActions.CreateReactionComment, createReactionCommentSaga);
}

export function* watchWatchedComment() {
  yield takeEvery(EWorkflowsActions.WatchedComment, watchedCommentSaga);
}

export function* watchDeleteComment() {
  yield takeEvery(EWorkflowsActions.DeleteComment, deleteCommentSaga);
}

export function* watchEditComment() {
  yield takeEvery(EWorkflowsActions.EditComment, editCommentSaga);
}

export function* watchLoadFilterTemplates() {
  yield takeEvery(EWorkflowsActions.LoadFilterTemplates, fetchFilterTemplates);
}

export function* watchLoadFilterSteps() {
  yield takeEvery(EWorkflowsActions.LoadFilterSteps, fetchFilterSteps);
}

export function* watchSendWorkflowLogComment() {
  yield takeEvery(EWorkflowsActions.SendWorkflowLogComment, saveWorkflowLogComment);
}

export function* watchDeleteWorfklow() {
  yield takeEvery(EWorkflowsActions.DeleteWorkflow, deleteWorkflowSaga);
}

export function* watchReturnWorkflowToTask() {
  yield takeEvery(EWorkflowsActions.ReturnWorkflowToTask, returnWorkflowToTaskSaga);
}

export function* watchCloneWorkflow() {
  yield takeEvery(EWorkflowsActions.CloneWorkflow, cloneWorkflowSaga);
}

export function* watchUpdateCurrentPerformersCounters() {
  yield takeEvery(EWorkflowsActions.UpdateCurrentPerformersCounters, updateCurrentPerformersCountersSaga);
}

export function* watchUpdateWorkflowStartersCounters() {
  yield takeEvery(EWorkflowsActions.UpdateWorkflowStartersCounters, updateWorkflowStartersCountersSaga);
}

export function* watchSearchTextChanged() {
  yield takeLatest(EWorkflowsActions.ChangeWorkflowsSearchText, handleSearchTextChanged);
}

export function* watchUpdateWorkflowsTemplateStepsCounters() {
  yield takeLatest(EWorkflowsActions.UpdateWorkflowsTemplateStepsCounters, updateWorkflowsTemplateStepsCountersSaga);
}

export function* watchChangeWorkflowsSettings() {
  yield takeLatest(EWorkflowsActions.ApplyFilters, handleApplyFilters);
}

export function* watchSnoozeWorkflow() {
  yield takeEvery(EWorkflowsActions.SnoozeWorkflow, snoozeWorkflowSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchFetchWorkflow),
    fork(watchFetchWorkflowsList),
    fork(watchChangeWorkflowLogViewSettings),
    fork(watchSetWorkflowResumed),
    fork(watchSetWorkflowFinished),
    fork(watchEidtWorkflow),
    fork(watchLoadFilterTemplates),
    fork(watchSendWorkflowLogComment),
    fork(watchChangeWorkflowsSettings),
    fork(watchDeleteWorfklow),
    fork(watchReturnWorkflowToTask),
    fork(watchCloneWorkflow),
    fork(watchLoadFilterSteps),
    fork(watchOpenWorkflowLogPopup),
    fork(watchUpdateCurrentPerformersCounters),
    fork(watchUpdateWorkflowStartersCounters),
    fork(watchSearchTextChanged),
    fork(watchUpdateWorkflowsTemplateStepsCounters),
    fork(watchSnoozeWorkflow),
    fork(watchDeleteComment),
    fork(watchEditComment),
    fork(watchWatchedComment),
    fork(watchCreateReactionComment),
    fork(watchDeleteReactionComment),
  ]);
}
