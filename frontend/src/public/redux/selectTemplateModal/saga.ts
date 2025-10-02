/* eslint-disable */
/* prettier-ignore */
import { all, fork, put, select, takeEvery } from 'redux-saga/effects';

import { logger } from '../../utils/logger';
import { NotificationManager } from '../../components/UI/Notifications';

import {
  ESelectTemplateModalActions,
  setSelectTemplateModalTemplates,
} from './actions';

import { getTemplates } from '../../api/getTemplates';
import { ETemplatesSorting } from '../../types/workflow';
import { ITemplateListItem } from '../../types/template';
import { getTemplatesModalFilter } from '../selectors/selectTemplateModal';
import { isArrayWithItems } from '../../utils/helpers';

function* fetchSelectTemplateModalTemplates() {
  try {
    const templates: ITemplateListItem[] = yield getTemplates({
      sorting: ETemplatesSorting.UsageDesc,
      isActive: true,
      isTemplateOwner: true,
    });

    const templatesIdsFilter: ReturnType<typeof getTemplatesModalFilter> = yield select(getTemplatesModalFilter);
    const filteredTemplates = isArrayWithItems(templatesIdsFilter)
      ? templates.filter(template => templatesIdsFilter.some(templateId => templateId === template.id))
      : templates;

    yield put(setSelectTemplateModalTemplates(filteredTemplates));
  } catch (error) {
    NotificationManager.error({ id: 'select-template.failed-to-fetch-templates' });
    logger.error(error);
  }
}

export function* watchFetchSelectTemplateModalTemplates() {
  yield takeEvery(ESelectTemplateModalActions.LoadSelectTemplateModalTemplates, fetchSelectTemplateModalTemplates);
}

export function* rootSaga() {
  yield all([
    fork(watchFetchSelectTemplateModalTemplates),
  ]);
}
