import { startOfToday, endOfToday, isValid } from 'date-fns';
import { connect } from 'react-redux';
import { AnyAction } from 'redux';

import { IApplicationState } from '../../types/redux';
import { openWorkflowLogPopup } from '../../redux/workflows/actions';
import {
  loadHighlights,
  loadHighlightsTemplatesTitles,
  resetHightlightsStore,
  setFilters,
  setHighlightsFiltersManuallyChanged,
} from '../../redux/highlights/actions';

import { HighlightsFeed, IHighlightsFeedProps } from './HighlightsFeed';
import { withSyncedQueryString } from '../../HOCs/withSyncedQueryString';
import { EHighlightsDateFilter } from '../../types/highlights';
import { getActiveUsers } from '../../utils/users';

type THighlightsFeedStoreProps = Pick<
IHighlightsFeedProps,
'count'
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
| 'filtersChanged'
>;

type THighlightsFeedDispatchProps = Pick<
IHighlightsFeedProps,
| 'openWorkflowLogPopup'
| 'loadHighlights'
| 'resetHightlightsStore'
| 'loadTemplatesTitles'
| 'setFilters'
| 'setFiltersChanged'
>;

export function mapStateToProps({
  accounts: {
    users,
  },
  workflows: { workflowLog: {
    isLoading,
    workflowId,
  } },
  highlights: {
    count,
    isFeedLoading,
    isTemplatesTitlesLoading,
    items,
    templatesTitles,
    filters: {
      timeRange,
      startDate,
      endDate,
      usersFilter,
      templatesFilter,
      filtersChanged,
    },
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
    filtersChanged,
  };
}

export const mapDispatchToProps: THighlightsFeedDispatchProps = {
  loadHighlights,
  loadTemplatesTitles: loadHighlightsTemplatesTitles,
  openWorkflowLogPopup,
  resetHightlightsStore,
  setFilters,
  setFiltersChanged: setHighlightsFiltersManuallyChanged,
};

const SyncedHiglights = withSyncedQueryString<THighlightsFeedStoreProps>([
  {
    propName: 'timeRange',
    queryParamName: 'time-range',
    defaultAction: setFilters({ timeRange: EHighlightsDateFilter.Today }),
    createAction: (timeRange: EHighlightsDateFilter) => setFilters({ timeRange }),
    getQueryParamByProp: value => value,
  },
  {
    propName: 'startDate',
    queryParamName: 'start-date',
    defaultAction: setFilters({ startDate: startOfToday() }),
    createAction: (startDateQuery: string) => {
      const startDate = new Date(startDateQuery);

      if (!isValid(startDate)) {
        return { type: 'EMPTY_ACTION' } as AnyAction;
      }

      return setFilters({ startDate });
    },
    getQueryParamByProp: (propValue: string) => propValue,
  },
  {
    propName: 'endDate',
    queryParamName: 'end-date',
    defaultAction: setFilters({ endDate: endOfToday() }),
    createAction: (endDateQuery: string) => {
      const endDate = new Date(endDateQuery);

      if (!isValid(endDate)) {
        return { type: 'EMPTY_ACTION' } as AnyAction;
      }

      return setFilters({ endDate });
    },
    getQueryParamByProp: (propValue: string) => propValue,
  },
  {
    propName: 'usersFilter',
    queryParamName: 'users',
    defaultAction: setFilters({ usersFilter: [] }),
    createAction: usersQuery => {
      const usersFilter = usersQuery.split(',').map(Number);

      return setFilters({ usersFilter });
    },
    getQueryParamByProp: users => users.join(','),
  },
  {
    propName: 'templatesFilter',
    queryParamName: 'templates',
    defaultAction: setFilters({ templatesFilter: [] }),
    createAction: templatesQuery => {
      const templatesFilter = templatesQuery.split(',').map(Number);

      return setFilters({ templatesFilter });
    },
    getQueryParamByProp: templates => templates.join(','),
  },
])(HighlightsFeed);

export const HighlightsFeedContainer = connect(mapStateToProps, mapDispatchToProps)(SyncedHiglights);
