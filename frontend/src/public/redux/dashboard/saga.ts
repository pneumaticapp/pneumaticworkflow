/* eslint-disable */
/* prettier-ignore */
import { all, call, fork, put, takeEvery, select } from 'redux-saga/effects';
import {
  EDashboardActions,
  setDashboardCounters,
  setBreakdownItems,
  TLoadBreakdownTasks,
  setIsDasboardLoaderVisible,
  patchBreakdownItem,
  loadGettingStartedChecklistSuccess,
  loadGettingStartedChecklistFailed,
  TOpenRunWorkflowModalByTemplateId,
  TOpenRunWorkflowModalSideMenu,
} from './actions';
import { setGeneralLoaderVisibility } from '../general/actions';

import { logger } from '../../utils/logger';
import { NotificationManager } from '../../components/UI/Notifications';
import { getDashboardWorkflowOverviewApi, IGetDashboardOverviewResponse } from '../../api/dashboard/getDashboardWorkflowOverview';
import { getDashboardTasksOverview } from '../../api/dashboard/getDashboardTasksOverview';
import { getDashboardWorkflowBreakdown } from '../../api/dashboard/getDashboardWorkflowBreakdown';
import { getDashboardTasksBreakdown } from '../../api/dashboard/getDashboardTasksBreakdown';
import { getDashboardWorkflowsTasks } from '../../api/dashboard/getDashboardWorkflowsTasks';
import { getDashboardTasksBySteps } from '../../api/dashboard/getDashboardTasks';
import {
  EDashboardModes,
  IDashboardTask,
  TDashboardBreakdownItemResponse,
} from '../../types/redux';
import { getIsAdmin } from '../selectors/user';
import {
  getDashboardBreakdownItems,
  getDashboardStore,
  getDashboardTimeRange,
  getDashboardMode,
} from '../selectors/dashboard';
import { getRangeDates } from '../../components/Dashboard/utils/getRangeDates';
import { handleLoadTemplateVariables } from '../templates/saga';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { normalizeBreakdownItems } from '../../utils/dashboard';
import { isArrayWithItems } from '../../utils/helpers';

import { getTemplate } from '../../api/getTemplate';

import { openRunWorkflowModal } from '../runWorkflowModal/actions';
import { getRunnableWorkflow } from '../../components/TemplateEdit/utils/getRunnableWorkflow';
import { ITemplateResponse } from '../../types/template';
import { getGettingStartedChecklist } from '../../api/getGettingStartedChecklist';
import { IGettingStartedChecklist } from '../../types/dashboard';
import { loadTemplateIntegrationsStats } from '../actions';
import { isObject } from '../../utils/mappers';

function* fetchDashboardData() {
  yield put(setIsDasboardLoaderVisible(true));
  yield all([
    fetchDashboardCounters(),
    fetchDashboardBreakdownItems(),
  ]);
  yield put(setIsDasboardLoaderVisible(false));

  const breakdownItems: ReturnType<typeof getDashboardBreakdownItems> = yield select(getDashboardBreakdownItems);
  if (isArrayWithItems(breakdownItems)) {
    yield put(loadTemplateIntegrationsStats({ templates: breakdownItems.map(i => i.templateId) }));
  }
}

function* fetchDashboardCounters() {
  try {
    const timeRange: ReturnType<typeof getDashboardTimeRange> = yield select(getDashboardTimeRange);
    const isAdmin: boolean = yield select(getIsAdmin);
    const dashboardMode: EDashboardModes = yield isAdmin ? select(getDashboardMode) : EDashboardModes.Tasks;
    const timeRangeDates = getRangeDates(timeRange);

    const getCounters = dashboardMode === EDashboardModes.Workflows
      ? getDashboardWorkflowOverviewApi
      : getDashboardTasksOverview;

    const countersResponse: IGetDashboardOverviewResponse = yield call(getCounters, timeRangeDates);

    yield put(setDashboardCounters(countersResponse));
  } catch (error) {
    logger.info('fetch dashboard stats error : ', error);
    NotificationManager.error({ message: 'dashboard.error-fetch' });
  }
}

function* fetchDashboardBreakdownItems() {
  try {
    const isAdmin: boolean = yield select(getIsAdmin);
    const { timeRange, mode }: ReturnType<typeof getDashboardStore> =
      yield select(getDashboardStore);
    const rangeDates = getRangeDates(timeRange);

    const getBreakdown = (isAdmin && mode === EDashboardModes.Workflows)
      ? getDashboardWorkflowBreakdown
      : getDashboardTasksBreakdown;
    const breakdownItems: TDashboardBreakdownItemResponse[] = yield getBreakdown(rangeDates);
    const normalizedBreakdownItems = normalizeBreakdownItems(breakdownItems);
    yield put(setBreakdownItems(normalizedBreakdownItems));
  } catch (error) {
    logger.info('fetch breakdown items error : ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

export function* fetchBreakdownTasks({ payload: { templateId } }: TLoadBreakdownTasks) {
  const isAdmin: boolean = yield select(getIsAdmin);
  const {
    timeRange,
    breakdownItems,
    mode: dashboardMode,
  }: ReturnType<typeof getDashboardStore> = yield select(getDashboardStore);
  const { endDate, startDate, now } = getRangeDates(timeRange);

  const breakdown = breakdownItems.find(breakdown => breakdown.templateId === templateId);
  if (isArrayWithItems(breakdown?.tasks)) {
    return;
  }

  try {
    yield put(patchBreakdownItem({ templateId, changedFields: { areTasksLoading: true } }));

    const getBreakdownTasks = (isAdmin && dashboardMode === EDashboardModes.Workflows)
      ? getDashboardWorkflowsTasks
      : getDashboardTasksBySteps;

    const [tasks]: [IDashboardTask[]] = yield all([
      call(getBreakdownTasks, {
        startDate,
        endDate,
        now,
        templateId: String(templateId),
      }),
      handleLoadTemplateVariables(templateId),
    ]);

    yield put(patchBreakdownItem({ templateId, changedFields: { tasks } }));
  } catch (error) {
    logger.info('fetch dashboard breakdown tasks error: ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  } finally {
    yield put(patchBreakdownItem({ templateId, changedFields: { areTasksLoading: false } }));
  }
}

export function* openRunWorflowSaga({ payload: { templateId, ancestorTaskId } }: TOpenRunWorkflowModalByTemplateId) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    const resData: ITemplateResponse = yield getTemplate(templateId);
    const templateData = getRunnableWorkflow(resData);

    if (templateData) {
      yield put(openRunWorkflowModal({ ...templateData, ancestorTaskId }));
    }
  } catch (error) {
    logger.info('fetch template error : ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* openRunWorflowByTemplateDataSaga({ payload: { templateData, ancestorTaskId } }: TOpenRunWorkflowModalSideMenu) {
  try {
    yield put(setGeneralLoaderVisibility(true));

    yield put(openRunWorkflowModal({ ...templateData, ancestorTaskId }));
  } catch (error) {
    logger.info('fetch template error : ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* loadChecklistSaga() {
  try {
    const cheklist: IGettingStartedChecklist = yield call(getGettingStartedChecklist);

    if (isObject(cheklist)) {
      yield put(loadGettingStartedChecklistSuccess(cheklist));
    }
  } catch (error) {
    yield put(loadGettingStartedChecklistFailed());
    logger.info('fetch getting started checklist: ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

export function* watchLoadDashboardData() {
  yield takeEvery(EDashboardActions.LoadDashboardData, fetchDashboardData);
}

export function* watchLoadBreakdownTasks() {
  yield takeEvery(EDashboardActions.LoadBreakdownTasks, fetchBreakdownTasks);
}

export function* watchOpenRunWorkflow() {
  yield takeEvery(EDashboardActions.OpenRunWorkflowModal, openRunWorflowSaga);
}

export function* watchOpenRunWorkflowSideMenu() {
  yield takeEvery(EDashboardActions.OpenRunWorkflowModalSideMenu, openRunWorflowByTemplateDataSaga);
}

export function* watchLoadChecklist() {
  yield takeEvery(EDashboardActions.LoadChecklist, loadChecklistSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchLoadDashboardData),
    fork(watchLoadBreakdownTasks),
    fork(watchOpenRunWorkflow),
    fork(watchOpenRunWorkflowSideMenu),
    fork(watchLoadChecklist),
  ]);
}
