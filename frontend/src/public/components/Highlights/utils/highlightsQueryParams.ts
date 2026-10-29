import { EHighlightsDateFilter } from '../../../types/highlights';

const DATE_FILTERS: string[] = Object.values(EHighlightsDateFilter);

export const parseTimeRangeQueryParam = (query: string): EHighlightsDateFilter =>
  DATE_FILTERS.includes(query) ? (query as EHighlightsDateFilter) : EHighlightsDateFilter.Today;

export const parseIdsQueryParam = (query: string): number[] =>
  query
    .split(',')
    .filter((part) => part.trim() !== '')
    .map(Number)
    .filter((id) => Number.isInteger(id) && id > 0);
