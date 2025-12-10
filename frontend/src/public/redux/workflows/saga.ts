import uniqBy from 'lodash.uniqby';
import { all, fork, put, takeEvery, select, takeLatest, call, delay, take, takeLeading } from 'redux-saga/effects';
import { EventChannel } from 'redux-saga';

import { PayloadAction } from '@reduxjs/toolkit';
import {
  openRunWorkflowModal,
  ETaskListActions,
  setGeneralLoaderVisibility,
  setCurrentTask,
  patchTaskInList,
  updateTaskWorkflowLogItem,
} from '../actions';
import {
  changeWorkflow,
  changeWorkflowsList,
  changeWorkflowLog,
  changeWorkflowLogViewSettings,
  changeWorkflowsSearchText,
  setWorkflowIsLoading,
  loadWorkflowsList,
  openWorkflowLogPopup,
  closeWorkflowLogPopup,
  updateWorkflowLogItem,
  loadWorkflow,
  loadWorkflowsListFailed,
  loadFilterTemplates,
  loadFilterTemplatesSuccess as loadWorkflowsFilterTemplatesSuccess,
  loadFilterTemplatesFailed as loadWorkflowsFilterTemplatesFailed,
  loadFilterSteps,
  loadFilterStepsSuccess as loadWorkflowsFilterStepsSuccess,
  loadFilterStepsFailed as loadWorkflowsFilterStepsFailed,
  setIsEditWorkflowName,
  setIsEditKickoff,
  setIsSavingWorkflowName,
  setIsSavingKickoff,
  setWorkflowEdit,
  applyFilters,
  setCurrentPerformersCounters,
  setWorkflowStartersCounters,
  setWorkflowsTemplateStepsCounters,
  patchWorkflowInList,
  patchWorkflowDetailed,
  setFilterSelectedFields as setWorkflowsFilterSelectedFields,
  setLastLoadedTemplateId,
  setWorkflowsPresetsRedux,
  createReactionComment as createReactionCommentAction,
  watchedComment as watchedCommentAction,
  editWorkflowSuccess,
  setWorkflowResumed,
  setWorkflowFinished,
  deleteReactionComment as deleteReactionCommentAction,
  sendWorkflowLogComments,
  editWorkflow as editWorkflowAction,
  deleteWorkflowAction,
  returnWorkflowToTaskAction,
  cloneWorkflowAction,
  updateCurrentPerformersCounters,
  updateWorkflowStartersCounters,
  updateWorkflowsTemplateStepsCounters,
  snoozeWorkflow as snoozeWorkflowAction,
  deleteComment as deleteCommentAction,
  editComment as editCommentAction,
  saveWorkflowsPreset,
} from './slice';
import {
  IChangeWorkflowLogViewSettingsPayload,
  ISaveWorkflowsPresetPayload,
  ISendWorkflowLogComment,
  TCloneWorkflowPayload,
  TDeleteWorkflowPayload,
  TEditWorkflowPayload,
  TLoadWorkflowsFilterStepsPayload,
  TOpenWorkflowLogPopupPayload,
  TReturnWorkflowToTaskPayload,
  TSetWorkflowFinishedPayload,
  TSetWorkflowResumedPayload,
  TSnoozeWorkflowPayload,
} from './types';
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
  EWorkflowsView,
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
import { IApplicationState, IStoreTask, IStoreWorkflows } from '../../types/redux';
import { logger } from '../../utils/logger';
import { NotificationManager } from '../../components/UI/Notifications';
import { sendWorkflowComment } from '../../api/sendWorkflowComment';
import { finishWorkflow } from '../../api/finishWorkflow';
import { editWorkflow, IEditWorkflowResponse } from '../../api/editWorkflow';
import { getTemplatesTitles, TGetTemplatesTitlesResponse } from '../../api/getTemplatesTitles';
import { IKickoff, ITemplateResponse, TTemplatePreset } from '../../types/template';
import { getWorkflowLogStore } from '../selectors/workflowLog';
import { deleteRemovedFilesFromFields } from '../../api/deleteRemovedFilesFromFields';
import { TChannelAction } from '../tasks/saga';
import { ITemplateStep } from '../../types/tasks';
import { getTemplateSteps } from '../../api/getTemplateSteps';

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
import { deleteComment, IDeleteComment } from '../../api/workflows/deleteComment';
import { editComment, IEditComment } from '../../api/workflows/editComment';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mergePaths } from '../../utils/urls';
import { parseCookies } from '../../utils/cookie';
import { createWebSocketChannel } from '../utils/createWebSocketChannel';
import { deleteReactionComment, IDeleteReaction } from '../../api/workflows/deleteReactionComment';
import { createReactionComment, ICreateReaction } from '../../api/workflows/createReactionComment';
import { IWatchedComment, watchedComment } from '../../api/workflows/watchedComment';
import { envWssURL } from '../../constants/enviroment';
import {
  mapBackandworkflowLogToRedux,
  mapBackendWorkflowToRedux,
  mapBackendNewEventToRedux,
  formatDueDateToEditWorkflow,
  mapWorkflowsToISOStringToRedux,
  mapWorkflowsAddComputedPropsToRedux,
  getNormalizeOutputUsersToEmails,
} from '../../utils/mappers';
import { getUserTimezone, getAuthUser, getUsers } from '../selectors/user';
import { getCurrentTask } from '../selectors/task';
import { formatDateToISOInWorkflow, toTspDate } from '../../utils/dateTime';
import { getWorkflowAddComputedPropsToRedux } from '../../components/Workflows/utils/getWorfkflowClientProperties';
import { getTemplatePresets, TGetTemplatePresetsResponse } from '../../api/getTemplatePresets';
import { getCorrectPresetFields } from '../../components/Workflows/utils/getCorrectPresetFields';
import { updateTemplatePresets } from '../../api/updateTemplatePresets';
import { addTemplatePreset } from '../../api/addTemplatePreset';
import { ALL_SYSTEM_FIELD_NAMES } from '../../components/Workflows/WorkflowsTablePage/WorkflowsTable/constants';
import { TUserListItem } from '../../types/user';

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

function* fetchWorkflow({ payload: id }: PayloadAction<number>) {
  try {
    yield fork(handleLoadWorkflow, { workflowId: id });
  } catch (error) {
    NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
  }
}

function* handleOpenWorkflowLogPopup({
  payload: { workflowId, shouldSetWorkflowDetailUrl, redirectTo404IfNotFound },
}: PayloadAction<TOpenWorkflowLogPopupPayload>) {
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
    NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
  }
}

function* fetchWorkflowLog({
  payload: { id, sorting, comments, isOnlyAttachmentsShown },
}: PayloadAction<IChangeWorkflowLogViewSettingsPayload>) {
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
    NotificationManager.notifyApiError(error, { message: 'workflows.fetch-in-work-process-log-fail' });
  } finally {
    yield put(changeWorkflowLog({ isLoading: false }));
  }
}

function* fetchWorkflowsList({ payload: offset = 0 }: PayloadAction<number>) {
  const {
    workflowsList,
    workflowsSettings: {
      view,
      sorting,
      values: {
        statusFilter,
        templatesIdsFilter,
        stepsIdsFilter,
        performersIdsFilter,
        performersGroupIdsFilter,
        workflowStartersIdsFilter,
      },
      selectedFields,
    },
  }: IStoreWorkflows = yield select(getWorkflowsStore);

  const searchText: ReturnType<typeof getWorkflowsSearchText> = yield select(getWorkflowsSearchText);
  const currentTemplateId = templatesIdsFilter.length === 1 ? templatesIdsFilter[0] : null;
  const severalTemplateIds = templatesIdsFilter.length > 1 || templatesIdsFilter.length === 0;

  const lastLoadedTemplateIdForTable: number | null = yield select(
    (state: IApplicationState) => state.workflows.workflowsSettings.lastLoadedTemplateIdForTable,
  );

  const shouldGetAllDefaultFields = Boolean(view === EWorkflowsView.Table && offset === 0 && severalTemplateIds);

  const internalNavigation =
    sessionStorage.getItem('isInternalNavigation') === 'true' &&
    Boolean(
      view === EWorkflowsView.Table &&
        offset === 0 &&
        currentTemplateId &&
        String(lastLoadedTemplateIdForTable) !== String(currentTemplateId),
    );
  const externalNavigation = Boolean(view === EWorkflowsView.Table && currentTemplateId && selectedFields.length === 0);

  const shouldGetPresets = internalNavigation || externalNavigation;
  sessionStorage.setItem('isInternalNavigation', 'false');

  let newSelectedFields: string[] = [];
  let shouldResetFields = false;

  if (view === EWorkflowsView.Grid) {
    shouldResetFields = true;
    newSelectedFields = [];
    yield put(setWorkflowsFilterSelectedFields(newSelectedFields));
    yield put(setLastLoadedTemplateId(null));
  }

  if (shouldGetPresets) {
    try {
      shouldResetFields = true;
      const presets: TGetTemplatePresetsResponse = yield call(getTemplatePresets, String(currentTemplateId));
      yield put(setWorkflowsPresetsRedux(presets));

      newSelectedFields = getCorrectPresetFields(presets);
      yield put(setWorkflowsFilterSelectedFields(newSelectedFields));
      yield put(setLastLoadedTemplateId(String(currentTemplateId)));
    } catch (error) {
      console.error('fetchWorkflowsList: Failed to load fields for template', currentTemplateId, ':', error);
    }
  } else if (shouldGetAllDefaultFields) {
    shouldResetFields = true;
    yield put(setLastLoadedTemplateId(null));
    newSelectedFields = ALL_SYSTEM_FIELD_NAMES;
    yield put(setWorkflowsFilterSelectedFields(newSelectedFields));
  }
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
      fields: shouldResetFields ? newSelectedFields : selectedFields,
    });
    const formattedResults = mapWorkflowsToISOStringToRedux(results);
    const items = offset > 0 ? uniqBy([...workflowsList.items, ...formattedResults], 'id') : formattedResults;

    yield put(changeWorkflowsList({ count, offset, items: mapWorkflowsAddComputedPropsToRedux(items) }));
  } catch (error) {
    logger.info('fetch workflows list error : ', error);
    yield put(loadWorkflowsListFailed());
    NotificationManager.notifyApiError(error, { message: 'workflows.fetch-processes-list-fail' });
  }
}

function* saveWorkflowLogComment({ payload: { text, attachments } }: PayloadAction<ISendWorkflowLogComment>) {
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
    NotificationManager.notifyApiError(error, { message: 'workflows.send-process-log-comment-fail' });
    yield put(changeWorkflowLog({ items }));
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* editWorkflowInWork({ payload }: PayloadAction<TEditWorkflowPayload>) {
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

    const usersList: TUserListItem[] = yield select(getUsers);
    const setUsers = new Map<number, string>(usersList.map((user) => [user.id, user.email]));
    const normalizedOutputs = getNormalizeOutputUsersToEmails(formattedPayload.kickoff?.fields || [], setUsers);
    const normalizedPayload = formattedPayload.kickoff
      ? {
        ...formattedPayload,
        kickoff: {
          ...formattedPayload.kickoff,
          fields: normalizedOutputs,
        },
      }
      : formattedPayload;

    const editedWorkflow: IEditWorkflowResponse = yield editWorkflow(normalizedPayload);
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

export function* setWorkflowResumedSaga({
  payload: { workflowId, onSuccess },
}: PayloadAction<TSetWorkflowResumedPayload>) {
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

export function* setWorkflowFinishedSaga({
  payload: { workflowId, onWorkflowEnded },
}: PayloadAction<TSetWorkflowFinishedPayload>) {
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
    const templatesTitles: TGetTemplatesTitlesResponse = yield getTemplatesTitles(workflowStatus);
    yield put(loadWorkflowsFilterTemplatesSuccess(templatesTitles));
  } catch (err) {
    yield put(loadWorkflowsFilterTemplatesFailed());
    logger.info('fetch workflow titles error : ', err);
    NotificationManager.notifyApiError(err, { message: 'workflows.load-tasks-count-fail' });
  }
}

export function* deleteWorkflowSaga({ payload: { workflowId, onSuccess } }: PayloadAction<TDeleteWorkflowPayload>) {
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

export function* returnWorkflowToTaskSaga({
  payload: { workflowId, taskId, onSuccess },
}: PayloadAction<TReturnWorkflowToTaskPayload>) {
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

export function* cloneWorkflowSaga({
  payload: { workflowId, workflowName, templateId },
}: PayloadAction<TCloneWorkflowPayload>) {
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
    NotificationManager.notifyApiError(error, { title: 'workflows.fail-copy' });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* fetchFilterSteps({
  payload: { templateId, onAfterLoaded },
}: PayloadAction<TLoadWorkflowsFilterStepsPayload>) {
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
    NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
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

export function* snoozeWorkflowSaga({
  payload: { workflowId, date, onSuccess },
}: PayloadAction<TSnoozeWorkflowPayload>) {
  const dateTsp = toTspDate(date);
  if (dateTsp === null) {
    throw new Error(`snoozeWorkflowSaga: Invalid date format: ${date}`);
  }
  try {
    yield put(setGeneralLoaderVisibility(true));
    const workflow: IEditWorkflowResponse = yield call(snoozeWorkflow, workflowId, dateTsp);
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
  yield takeLeading(loadWorkflowsList.type, fetchWorkflowsList);
}

export function* watchChangeWorkflowLogViewSettings() {
  yield takeLatest(changeWorkflowLogViewSettings.type, fetchWorkflowLog);
}

export function* watchOpenWorkflowLogPopup() {
  yield takeEvery(openWorkflowLogPopup.type, handleOpenWorkflowLogPopup);
}

export function* watchFetchWorkflow() {
  yield takeLatest(loadWorkflow.type, fetchWorkflow);
}

export function* watchEidtWorkflow() {
  yield takeEvery(editWorkflowAction.type, editWorkflowInWork);
}

export function* watchSetWorkflowResumed() {
  yield takeEvery(setWorkflowResumed.type, setWorkflowResumedSaga);
}

export function* handleSearchTextChanged() {
  yield delay(300);
  yield put(loadWorkflowsList(0));
}

export function* watchSetWorkflowFinished() {
  yield takeEvery(
    setWorkflowFinished.type,
    function* finishedWorkflow(action: PayloadAction<TSetWorkflowFinishedPayload>) {
      const handlerAction: TChannelAction = {
        type: ETaskListActions.ChannelAction,
        handler: () => setWorkflowFinishedSaga(action),
      };
      yield put(handlerAction);
    },
  );
}

export function* deleteCommentSaga({ payload: { id } }: PayloadAction<IDeleteComment>) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    const updateComment: IWorkflowLogItem = yield deleteComment({ id });
    yield put(updateWorkflowLogItem(updateComment));
    yield put(updateTaskWorkflowLogItem(updateComment));
  } catch (error) {
    NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* editCommentSaga({ payload: { id, text, attachments } }: PayloadAction<IEditComment>) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    const updateComment: IWorkflowLogItem = yield editComment({ id, text, attachments });
    yield put(updateWorkflowLogItem(updateComment));
    yield put(updateTaskWorkflowLogItem(updateComment));
  } catch (error) {
    NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
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

export function* watchedCommentSaga({ payload: { id } }: PayloadAction<IWatchedComment>) {
  try {
    yield watchedComment({ id });
  } catch (error) {
    NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
  }
}

export function* deleteReactionCommentSaga({ payload: { id, value } }: PayloadAction<IDeleteReaction>) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield deleteReactionComment({ id, value });
  } catch (error) {
    NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* createReactionCommentSaga({ payload: { id, value } }: PayloadAction<ICreateReaction>) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield createReactionComment({ id, value });
  } catch (error) {
    NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* saveWorkflowsPresetSaga({
  payload: { orderedFields, type, templateId },
}: PayloadAction<ISaveWorkflowsPresetPayload>) {
  const {
    workflowsSettings: { presets },
  }: IStoreWorkflows = yield select(getWorkflowsStore);
  const defaultPreset = presets.find((preset) => preset.isDefault && preset.type === type);

  const { authUser }: ReturnType<typeof getAuthUser> = yield select(getAuthUser);
  const userName = `${authUser.firstName} ${authUser.lastName}`;

  try {
    if (defaultPreset) {
      const updatedPreset: TTemplatePreset = yield call(updateTemplatePresets, {
        ...defaultPreset,
        fields: orderedFields,
        isDefault: true,
      });
      const updatedPresets = presets.map((preset) => (preset.id === defaultPreset.id ? updatedPreset : preset));
      yield put(setWorkflowsPresetsRedux(updatedPresets));
    } else {
      const newPreset: TTemplatePreset = yield call(addTemplatePreset, templateId, {
        name: `Preset ${presets.length + 1} - ${userName}`,
        type,
        isDefault: true,
        fields: orderedFields,
      });
      yield put(setWorkflowsPresetsRedux([...presets, newPreset]));
    }
  } catch (error) {
    logger.error('saveWorkflowsPresetSaga: Failed to save preset:', { orderedFields, type, templateId, error });
    NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
  }

  yield put(loadWorkflowsList(0));
}

export function* watchDeleteReactionComment() {
  yield takeEvery(deleteReactionCommentAction.type, deleteReactionCommentSaga);
}

export function* watchCreateReactionComment() {
  yield takeEvery(createReactionCommentAction.type, createReactionCommentSaga);
}

export function* watchWatchedComment() {
  yield takeEvery(watchedCommentAction.type, watchedCommentSaga);
}

export function* watchDeleteComment() {
  yield takeEvery(deleteCommentAction.type, deleteCommentSaga);
}

export function* watchEditComment() {
  yield takeEvery(editCommentAction.type, editCommentSaga);
}

export function* watchLoadFilterTemplates() {
  yield takeEvery(loadFilterTemplates.type, fetchFilterTemplates);
}

export function* watchLoadFilterSteps() {
  yield takeEvery(loadFilterSteps.type, fetchFilterSteps);
}

export function* watchSendWorkflowLogComment() {
  yield takeEvery(sendWorkflowLogComments.type, saveWorkflowLogComment);
}

export function* watchDeleteWorfklow() {
  yield takeEvery(deleteWorkflowAction.type, deleteWorkflowSaga);
}

export function* watchReturnWorkflowToTask() {
  yield takeEvery(returnWorkflowToTaskAction.type, returnWorkflowToTaskSaga);
}

export function* watchCloneWorkflow() {
  yield takeEvery(cloneWorkflowAction.type, cloneWorkflowSaga);
}

export function* watchUpdateCurrentPerformersCounters() {
  yield takeEvery(updateCurrentPerformersCounters.type, updateCurrentPerformersCountersSaga);
}

export function* watchUpdateWorkflowStartersCounters() {
  yield takeEvery(updateWorkflowStartersCounters.type, updateWorkflowStartersCountersSaga);
}

export function* watchSearchTextChanged() {
  yield takeLatest(changeWorkflowsSearchText.type, handleSearchTextChanged);
}

export function* watchUpdateWorkflowsTemplateStepsCounters() {
  yield takeLatest(updateWorkflowsTemplateStepsCounters.type, updateWorkflowsTemplateStepsCountersSaga);
}

export function* watchChangeWorkflowsSettings() {
  yield takeLatest(applyFilters.type, handleApplyFilters);
}

export function* watchSnoozeWorkflow() {
  yield takeEvery(snoozeWorkflowAction.type, snoozeWorkflowSaga);
}

export function* watchSaveWorkflowsPreset() {
  yield takeEvery(saveWorkflowsPreset.type, saveWorkflowsPresetSaga);
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
    fork(watchSaveWorkflowsPreset),
  ]);
}
