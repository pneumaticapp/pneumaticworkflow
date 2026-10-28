import { IHighlightsFilters } from '../../../types/redux';
import { EHighlightsDateFilter } from '../../../types/highlights';
import { getTodayDateRange } from '../../../components/Highlights/utils/highlightsDateRange';

export const getInitHighlightsFilters = (): IHighlightsFilters => {
  const { startDate, endDate } = getTodayDateRange();

  return {
    timeRange: EHighlightsDateFilter.Today,
    startDate,
    endDate,
    usersFilter: [],
    templatesFilter: [],
    hasChangedFilters: false,
  };
};
