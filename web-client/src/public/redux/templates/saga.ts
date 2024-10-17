import { all, call, fork, put, select, takeEvery } from 'redux-saga/effects';
import uniqBy from 'lodash.uniqby';

import {
  ETemplatesActions,
  loadTemplatesSystemFailed,
  changeTemplatesList,
  loadTemplates,
  loadTemplatesFailed,
  TLoadTemplates,
  TLoadTemplateVariables,
  loadTemplateVariablesSuccess,
  setTemplateIntegrationsStats,
  TLoadTemplateIntegrationsStats,
  loadTemplateIntegrationsStats,
  changeTemplatesSystem,
  changeTemplatesSystemCategories,
  ETemplatesSystemStatus,
  setCurrentTemplatesSystemStatus,
} from '../actions';
import { getTemplatesSystem } from '../../api/getSystemTemplates';
import { getTemplatesIntegrationsStats } from '../../api/getTemplatesIntegrationsStats';
import { TTemplateIntegrationStatsApi } from '../../types/template';
import { logger } from '../../utils/logger';
import { NotificationManager } from '../../components/UI/Notifications';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { getTemplatesStore, getTemplatesSystemList } from '../selectors/templates';
import { getTemplates } from '../../api/getTemplates';
import { history } from '../../utils/history';
import { ERoutes } from '../../constants/routes';
import { getVariables } from '../../components/TemplateEdit/TaskForm/utils/getTaskVariables';
import { getTemplateFields, TGetTemplateFieldsResponse } from '../../api/getTemplateFields';
import { isArrayWithItems } from '../../utils/helpers';
import { getTemplatesSystemCategories } from '../../api/getSystemTemplatesCategories';
import { ITemplatesSystemCategories } from '../../types/redux';
import { LIMIT_LOAD_SYSTEMS_TEMPLATES, LIMIT_LOAD_TEMPLATES } from '../../constants/defaultValues';

function* fetchTemplatesSystem() {
  try {
    const {
      items,
      selection: { offset, searchText, category },
    }: ReturnType<typeof getTemplatesSystemList> = yield select(getTemplatesSystemList);

    const { count, results } = yield getTemplatesSystem({
      category,
      searchText,
      limit: LIMIT_LOAD_SYSTEMS_TEMPLATES,
      offset: offset * LIMIT_LOAD_SYSTEMS_TEMPLATES,
    });

    const data = offset > 0 ? uniqBy([...items, ...results], 'id') : results;

    if (results) yield put(changeTemplatesSystem({ count, items: data }));

    if (!data.length) {
      yield put(setCurrentTemplatesSystemStatus(ETemplatesSystemStatus.NoTemplates));
    } else {
      yield put(setCurrentTemplatesSystemStatus(ETemplatesSystemStatus.WaitingForAction));
    }
  } catch (error) {
    yield put(loadTemplatesSystemFailed());
    logger.info('fetch system templates failed : ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

function* fetchTemplatesSystemCategories() {
  try {
    const systemTemplatesCategories: ITemplatesSystemCategories[] | undefined = yield getTemplatesSystemCategories();

    if (isArrayWithItems(systemTemplatesCategories)) {
      yield put(changeTemplatesSystemCategories(systemTemplatesCategories));
    }
  } catch (error) {
    logger.info('fetch system templates categories failed : ', error);

    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

function* fetchTemplates({ payload: offset = 0 }: TLoadTemplates) {
  try {
    const { templatesList, templatesListSorting }: ReturnType<typeof getTemplatesStore> = yield select(
      getTemplatesStore,
    );

    const { count, results } = yield getTemplates({
      offset,
      limit: LIMIT_LOAD_TEMPLATES,
      sorting: templatesListSorting,
    });

    const items = offset > 0 ? uniqBy([...templatesList.items, ...results], 'id') : results;

    yield put(changeTemplatesList({ count, offset, items }));

    if (isArrayWithItems(results)) {
      yield put(loadTemplateIntegrationsStats({ templates: results.map(({ id }) => id) }));
    }
  } catch (error) {
    logger.info('fetch templates error : ', error);
    yield put(loadTemplatesFailed());
    NotificationManager.error({ message: 'templates.fetch-fail' });
    history.replace(ERoutes.Templates);
  }
}

export function* changeTemplatesSearchText() {
  yield put(loadTemplates(0));
}

function* fetchSortingTemplatesList() {
  yield put(changeTemplatesList({ count: 0, offset: 0, items: [] }));
  yield put(loadTemplates(0));
}

export function* handleLoadTemplateVariables(templateId: number) {
  try {
    yield put(loadTemplateVariablesSuccess({ templateId, variables: [] }));
    const { kickoff, tasks }: TGetTemplateFieldsResponse = yield call(getTemplateFields, String(templateId));
    const variables = getVariables({ kickoff, tasks });

    yield put(loadTemplateVariablesSuccess({ templateId, variables }));
  } catch (error) {
    logger.info('fetch template fields error: ', error);
    NotificationManager.error({ message: getErrorMessage(error) });
  }
}

export function* loadTemplateIntegrationsStatsSaga({ payload: { templates } }: TLoadTemplateIntegrationsStats) {
  try {
    const stats: TTemplateIntegrationStatsApi[] = yield call(getTemplatesIntegrationsStats, { templates });
    yield put(setTemplateIntegrationsStats(stats));
  } catch (error) {
    logger.info('fetch templates integrations stats error: ', error);
  }
}

function* fetchTemplateVariables({ payload: { templateId } }: TLoadTemplateVariables) {
  yield handleLoadTemplateVariables(templateId);
}

export function* watchLoadTemplatesSystem() {
  yield takeEvery(
    [
      ETemplatesActions.LoadTemplatesSystem,
      ETemplatesActions.ChangeTemplatesSystemSelectionSearch,
      ETemplatesActions.ChangeTemplatesSystemSelectionCategory,
      ETemplatesActions.ChangeTemplatesSystemPaginationNext,
    ],
    fetchTemplatesSystem,
  );
}

export function* watchLoadTemplatesSystemCategories() {
  yield takeEvery(ETemplatesActions.LoadTemplatesSystemCategories, fetchTemplatesSystemCategories);
}

export function* watchChangeTemplatesListSorting() {
  yield takeEvery(ETemplatesActions.ChangeTemplatesListSorting, fetchSortingTemplatesList);
}

export function* watchFetchTemplates() {
  yield takeEvery(ETemplatesActions.LoadTemplates, fetchTemplates);
}

export function* watchLoadTemplateVariables() {
  yield takeEvery(ETemplatesActions.LoadTemplateVariables, fetchTemplateVariables);
}

export function* watchLoadTemplateIntegrationsStats() {
  yield takeEvery(ETemplatesActions.LoadTemplateIntegrationsStats, loadTemplateIntegrationsStatsSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchLoadTemplatesSystem),
    fork(watchFetchTemplates),
    fork(watchLoadTemplatesSystemCategories),
    fork(watchChangeTemplatesListSorting),
    fork(watchLoadTemplateVariables),
    fork(watchLoadTemplateIntegrationsStats),
  ]);
}
