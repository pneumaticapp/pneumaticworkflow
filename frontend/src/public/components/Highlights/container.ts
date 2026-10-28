import { connect } from 'react-redux';
import { AnyAction } from 'redux';

import { IApplicationState } from '../../types/redux';
import { openWorkflowLogPopup } from '../../redux/workflows/slice';
import {
  loadHighlights,
  loadHighlightsTemplatesTitles,
  resetHighlightsStore,
  setHighlightsFilters,
  setHighlightsFiltersChanged,
} from '../../redux/highlights/slice';

import { HighlightsFeed, IHighlightsFeedProps } from './HighlightsFeed';
import { withSyncedQueryString } from '../../HOCs/withSyncedQueryString';
import { EHighlightsDateFilter } from '../../types/highlights';
import { getActiveUsers } from '../../utils/users';
import { getTodayDateRange } from './utils/highlightsDateRange';
import { parseDateQueryParam, serializeDateQueryParam } from './utils/dateQueryParam';

type THighlightsFeedStoreProps = Pick<
  IHighlightsFeedProps,
  | 'count'
  | 'items'
  | 'isWorkflowLogPopupLoading'
  | 'workflowId'
  | 'isFeedLoading'
  | 'templatesTitles'
  | 'users'
  | 'isTemplatesTitlesLoading'
  | 'timeRange'
  | 'startDate'
  | 'endDate'
  | 'usersFilter'
  | 'templatesFilter'
  | 'hasChangedFilters'
>;

type THighlightsFeedDispatchProps = Pick<
  IHighlightsFeedProps,
  | 'openWorkflowLogPopup'
  | 'loadHighlights'
  | 'resetHighlightsStore'
  | 'loadTemplatesTitles'
  | 'setHighlightsFilters'
  | 'setHighlightsFiltersChanged'
>;

export function mapStateToProps({
  accounts: { users },
  workflows: {
    workflowLog: { isLoading, workflowId },
  },
  highlights: {
    count,
    isFeedLoading,
    isTemplatesTitlesLoading,
    items,
    templatesTitles,
    filters: { timeRange, startDate, endDate, usersFilter, templatesFilter, hasChangedFilters },
  },
}: IApplicationState): THighlightsFeedStoreProps {
  return {
    count,
    isFeedLoading,
    isWorkflowLogPopupLoading: isLoading,
    isTemplatesTitlesLoading,
    items,
    workflowId,
    users: getActiveUsers(users),
    templatesTitles,
    timeRange,
    startDate,
    endDate,
    usersFilter,
    templatesFilter,
    hasChangedFilters,
  };
}

export const mapDispatchToProps: THighlightsFeedDispatchProps = {
  loadHighlights,
  loadTemplatesTitles: loadHighlightsTemplatesTitles,
  openWorkflowLogPopup,
  resetHighlightsStore,
  setHighlightsFilters,
  setHighlightsFiltersChanged,
};

const SyncedHiglights = withSyncedQueryString<THighlightsFeedStoreProps>([
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
    createAction: (startDateQuery: string) => {
      const startDate = parseDateQueryParam(startDateQuery);

      if (!startDate) {
        return { type: 'EMPTY_ACTION' } as AnyAction;
      }

      return setHighlightsFilters({ startDate });
    },
    getQueryParamByProp: serializeDateQueryParam,
  },
  {
    propName: 'endDate',
    queryParamName: 'end-date',
    defaultAction: setHighlightsFilters({ endDate: getTodayDateRange().endDate }),
    createAction: (endDateQuery: string) => {
      const endDate = parseDateQueryParam(endDateQuery);

      if (!endDate) {
        return { type: 'EMPTY_ACTION' } as AnyAction;
      }

      return setHighlightsFilters({ endDate });
    },
    getQueryParamByProp: serializeDateQueryParam,
  },
  {
    propName: 'usersFilter',
    queryParamName: 'users',
    defaultAction: setHighlightsFilters({ usersFilter: [] }),
    createAction: (usersQuery) => {
      const usersFilter = usersQuery.split(',').map(Number);

      return setHighlightsFilters({ usersFilter });
    },
    getQueryParamByProp: (users) => users.join(','),
  },
  {
    propName: 'templatesFilter',
    queryParamName: 'templates',
    defaultAction: setHighlightsFilters({ templatesFilter: [] }),
    createAction: (templatesQuery) => {
      const templatesFilter = templatesQuery.split(',').map(Number);

      return setHighlightsFilters({ templatesFilter });
    },
    getQueryParamByProp: (templates) => templates.join(','),
  },
])(HighlightsFeed);

export const HighlightsFeedContainer = connect(mapStateToProps, mapDispatchToProps)(SyncedHiglights);
