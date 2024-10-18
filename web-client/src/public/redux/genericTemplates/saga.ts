/* eslint-disable */
/* prettier-ignore */
import { all, call, fork, put, takeEvery, select } from 'redux-saga/effects';
import { EGenericTemplatesActions, setGenericTemplates, setSelectedGenericTemplates, fetchGenericTemplatesFailed } from './actions';

import { getGenericTemplates } from '../../api/getGenericTemplates';
import { getAccountGenericTemplates } from '../../api/getAccountGenericTemplates';
import { IAccountGenericTemplate } from '../../types/genericTemplates';
import { saveAccountGenericTemplates } from '../../api/saveAccountGenericTemplates';
import { getSelectedGenericTemplates } from '../selectors/user';
import { logger } from '../../utils/logger';
import { isArrayWithItems } from '../../utils/helpers';

type TAllGenericWorkflowsResponse = [IAccountGenericTemplate[], IAccountGenericTemplate[]];

const getAllGenericTemplatesAsync = (): Promise<TAllGenericWorkflowsResponse> =>
  Promise.all([
    getGenericTemplates(),
    getAccountGenericTemplates(),
  ])
    .then(result => result)
    .catch(error => error);

function* fetchAllGenericTemplates() {
  try {
    const [
      genericWorkflows,
      selectedGenericWorkflows,
    ]: TAllGenericWorkflowsResponse = yield call(getAllGenericTemplatesAsync);
    yield put(setGenericTemplates(genericWorkflows));
    const selected = selectedGenericWorkflows.map(({id}) => id);
    yield put(setSelectedGenericTemplates(selected));
  } catch (error) {
    logger.info('fetch generic templates error : ', error);
    yield put(fetchGenericTemplatesFailed());
  }
}

const saveSelectedGenericTemplatesAsync = (selected: number[]) =>
  saveAccountGenericTemplates(selected)
    .then(result => result)
    .catch(error => error);

function* saveSelectedGenericTemplates() {
  try {
    const { selected }: ReturnType<typeof getSelectedGenericTemplates> = yield select(getSelectedGenericTemplates);

    if (!isArrayWithItems(selected)) {
      return;
    }

    yield call(saveSelectedGenericTemplatesAsync, selected);
  } catch (error) {
    logger.info('save generic templates error : ', error);
    yield put(fetchGenericTemplatesFailed());
  }
}

export function* watchFetchGenericTemplates() {
  yield takeEvery(EGenericTemplatesActions.Fetch, fetchAllGenericTemplates);
  yield takeEvery(EGenericTemplatesActions.SaveSelected, saveSelectedGenericTemplates);
}

export function* rootSaga() {
  yield all([
    fork(watchFetchGenericTemplates),
  ]);
}
