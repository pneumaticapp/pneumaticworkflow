import React, { ComponentType } from 'react';
import { useSelector } from 'react-redux';
import { AnyAction } from 'redux';

import { withSyncedQueryString } from '../../HOCs/withSyncedQueryString';
import { setHighlightsFilters } from '../../redux/highlights/slice';
import { getHighlightsFilters } from '../../redux/selectors/highlights';
import { EHighlightsDateFilter } from '../../types/highlights';
import { HighlightsFeed } from './HighlightsFeed';
import { THighlightsQuerySyncProps } from './types';
import { parseDateQueryParam, serializeDateQueryParam } from './utils/dateQueryParam';
import { getTodayDateRange } from './utils/highlightsDateRange';

const EMPTY_ACTION: AnyAction = { type: 'EMPTY_ACTION' };

const parseIdsQueryParam = (query: string): number[] => query.split(',').map(Number);

const SyncedHighlightsFeed = withSyncedQueryString<THighlightsQuerySyncProps>([
  {
    propName: 'timeRange',
    queryParamName: 'time-range',
    defaultAction: setHighlightsFilters({ timeRange: EHighlightsDateFilter.Today }),
    createAction: (timeRange: EHighlightsDateFilter) => setHighlightsFilters({ timeRange }),
    getQueryParamByProp: (value) => value,
  },
  {
    propName: 'startDate',
    queryParamName: 'start-date',
    defaultAction: setHighlightsFilters({ startDate: getTodayDateRange().startDate }),
    createAction: (query) => {
      const startDate = parseDateQueryParam(query);

      return startDate ? setHighlightsFilters({ startDate }) : EMPTY_ACTION;
    },
    getQueryParamByProp: serializeDateQueryParam,
  },
  {
    propName: 'endDate',
    queryParamName: 'end-date',
    defaultAction: setHighlightsFilters({ endDate: getTodayDateRange().endDate }),
    createAction: (query) => {
      const endDate = parseDateQueryParam(query);

      return endDate ? setHighlightsFilters({ endDate }) : EMPTY_ACTION;
    },
    getQueryParamByProp: serializeDateQueryParam,
  },
  {
    propName: 'usersFilter',
    queryParamName: 'users',
    defaultAction: setHighlightsFilters({ usersFilter: [] }),
    createAction: (query) => setHighlightsFilters({ usersFilter: parseIdsQueryParam(query) }),
    getQueryParamByProp: (users: number[]) => users.join(','),
  },
  {
    propName: 'templatesFilter',
    queryParamName: 'templates',
    defaultAction: setHighlightsFilters({ templatesFilter: [] }),
    createAction: (query) => setHighlightsFilters({ templatesFilter: parseIdsQueryParam(query) }),
    getQueryParamByProp: (templates: number[]) => templates.join(','),
  },
])(HighlightsFeed) as ComponentType<THighlightsQuerySyncProps>;

export function HighlightsFeedContainer() {
  const { timeRange, startDate, endDate, usersFilter, templatesFilter } = useSelector(getHighlightsFilters);

  return (
    <SyncedHighlightsFeed
      timeRange={timeRange}
      startDate={startDate}
      endDate={endDate}
      usersFilter={usersFilter}
      templatesFilter={templatesFilter}
    />
  );
}
