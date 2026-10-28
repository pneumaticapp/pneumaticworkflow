import { PayloadAction } from '@reduxjs/toolkit';
import { all, fork, put, select, takeLatest } from 'redux-saga/effects';

import { getHighlightsItems, getHighlightsFilters } from '../selectors/highlights';
import { getHighlights, IGetHighlightsResponse, IGetHighlightsFilters } from '../../api/getHighlights';
import { logger } from '../../utils/logger';

import {
  loadHighlights,
  loadHighlightsTemplatesTitles,
  loadHighlightsTemplatesTitlesFailed,
  setHighlights,
  setHighlightsIsFeedLoading,
  setHighlightsTemplatesTitles,
} from './slice';
import { ILoadHighlightsConfig } from './types';
import {
  getHighlightsTitles,
  IGetHighlightsTitlesRequestConfig,
  TGetHighlightsTitlesResponse,
} from '../../api/getHighlightsTitles';
import { mapWorkflowsForSetHighlights } from '../../utils/mappers';
import { getUserTimezone } from '../selectors/user';
import { NotificationManager } from '../../components/UI/Notifications';

function* fetchTemplatesTitles({
  payload: { eventDateFrom, eventDateTo },
}: PayloadAction<IGetHighlightsTitlesRequestConfig>) {
  try {
    const templatesTitles: TGetHighlightsTitlesResponse = yield getHighlightsTitles({
      eventDateFrom,
      eventDateTo,
    });
    yield put(setHighlightsTemplatesTitles(templatesTitles));
  } catch (error) {
    NotificationManager.notifyApiError(error, { message: 'workflow-highlights.fetch-filters-fail' });
    yield put(loadHighlightsTemplatesTitlesFailed());
    logger.error(error);
  }
}

export function* fetchHighlights({ payload: { limit, offset, onScroll } }: PayloadAction<ILoadHighlightsConfig>) {
  try {
    const items: ReturnType<typeof getHighlightsItems> = yield select(getHighlightsItems);

    const filters: ReturnType<typeof getHighlightsFilters> = yield select(getHighlightsFilters);
    const normalizedFilters: IGetHighlightsFilters = {
      dateAfter: filters.startDate,
      dateBefore: filters.endDate,
      users: filters.usersFilter.map(String),
      templates: filters.templatesFilter.map(String),
    };
    const timezone: ReturnType<typeof getUserTimezone> = yield select(getUserTimezone);

    if (onScroll) {
      yield put(setHighlightsIsFeedLoading(true));

      const { count, next, previous, results }: IGetHighlightsResponse = yield getHighlights({
        limit,
        offset,
        filters: normalizedFilters,
      });

      const formattedResults = mapWorkflowsForSetHighlights(results, timezone);
      yield put(setHighlightsIsFeedLoading(false));
      yield put(setHighlights({ count, next, previous, results: [...items, ...formattedResults] }));

      return;
    }

    if (!onScroll) {
      yield put(setHighlights({ count: 0, results: [] }));
      yield put(setHighlightsIsFeedLoading(true));

      const { count, next, previous, results }: IGetHighlightsResponse = yield getHighlights({
        limit,
        offset,
        filters: normalizedFilters,
      });

      const formattedResults = mapWorkflowsForSetHighlights(results, timezone);
      yield put(setHighlightsIsFeedLoading(false));
      yield put(setHighlights({ count, next, previous, results: formattedResults }));
    }
  } catch (error) {
    NotificationManager.notifyApiError(error, { id: 'process-highlights.fetch-failed' });
    logger.error(error);
  }
}

export function* watchFetchTemplatesTitles() {
  yield takeLatest(loadHighlightsTemplatesTitles.type, fetchTemplatesTitles);
}

export function* watchFetchHighlights() {
  yield takeLatest(loadHighlights.type, fetchHighlights);
}

export function* rootSaga() {
  yield all([fork(watchFetchHighlights), fork(watchFetchTemplatesTitles)]);
}
