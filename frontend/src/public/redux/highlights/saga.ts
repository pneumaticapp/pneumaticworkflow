import { all, fork, put, select, takeEvery, takeLatest } from 'redux-saga/effects';

import { getHighlightsStore, getHighlightsFilters } from '../selectors/highlights';
import type { IGetHighlightsResponse, IGetHighlightsFilters } from '../../api/getHighlights';
import { getHighlights } from '../../api/getHighlights';
import { logger } from '../../utils/logger';

import type { TLoadHighlights, TLoadHighlightsTemplatesTitles } from './actions';
import {
  EHighlightsActions,
  setIsFeedLoading,
  setHighlights,
  setSetHighlightsTemplatesTitles,
  loadHighlightsTemplatesTitlesFailed,
} from './actions';
import type { TGetHighlightsTitlesResponse } from '../../api/getHighlightsTitles';
import { getHighlightsTitles } from '../../api/getHighlightsTitles';
import { mapWorkflowsForSetHighlights } from '../../utils/mappers';
import { getUserTimezone } from '../selectors/user';
import { NotificationManager } from '../../components/UI/Notifications';

function* fetchTemplatesTitles({ payload: { eventDateFrom, eventDateTo } }: TLoadHighlightsTemplatesTitles) {
  try {
    const templatesTitles: TGetHighlightsTitlesResponse = yield getHighlightsTitles({
      eventDateFrom,
      eventDateTo,
    });
    yield put(setSetHighlightsTemplatesTitles(templatesTitles));
  } catch (error) {
    NotificationManager.notifyApiError(error, { message: 'workflow-highlights.fetch-filters-fail' });
    yield put(loadHighlightsTemplatesTitlesFailed());
    logger.error(error);
  }
}

export function* fetchHighlights({ payload: { limit, offset, onScroll } }: TLoadHighlights) {
  try {
    const { items }: ReturnType<typeof getHighlightsStore> = yield select(getHighlightsStore);

    const filters: ReturnType<typeof getHighlightsFilters> = yield select(getHighlightsFilters);
    const normalizedFilters: IGetHighlightsFilters = {
      dateAfter: filters.startDate,
      dateBefore: filters.endDate,
      users: filters.usersFilter.map(String),
      templates: filters.templatesFilter.map(String),
    };
    const timezone: ReturnType<typeof getUserTimezone> = yield select(getUserTimezone);

    if (onScroll) {
      yield put(setIsFeedLoading(true));

      const { count, next, previous, results }: IGetHighlightsResponse = yield getHighlights({
        limit,
        offset,
        filters: normalizedFilters,
      });

      const formattedResults = mapWorkflowsForSetHighlights(results, timezone);
      yield put(setIsFeedLoading(false));
      yield put(setHighlights({ count, next, previous, results: [...items, ...formattedResults] }));

      return;
    }

    if (!onScroll) {
      yield put(setHighlights({ count: 0, results: [] }));
      yield put(setIsFeedLoading(true));

      const { count, next, previous, results }: IGetHighlightsResponse = yield getHighlights({
        limit,
        offset,
        filters: normalizedFilters,
      });

      const formattedResults = mapWorkflowsForSetHighlights(results, timezone);
      yield put(setIsFeedLoading(false));
      yield put(setHighlights({ count, next, previous, results: formattedResults }));
    }
  } catch (error) {
    NotificationManager.notifyApiError(error, { id: 'process-highlights.fetch-failed' });
    logger.error(error);
  }
}

export function* watchFetchTemplatesTitles() {
  yield takeEvery(EHighlightsActions.LoadHighlightsTemplatesTitles, fetchTemplatesTitles);
}

export function* watchFetchHighlights() {
  yield takeLatest(EHighlightsActions.LoadHighlights, fetchHighlights);
}

export function* rootSaga() {
  yield all([fork(watchFetchHighlights), fork(watchFetchTemplatesTitles)]);
}
