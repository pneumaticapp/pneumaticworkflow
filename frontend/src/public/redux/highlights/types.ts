import type { EHighlightsDateFilter, IHighlightsItem } from '../../types/highlights';
import type { ITemplateTitleBaseWithCount } from '../../types/template';

export interface IHighlightsFilters {
  timeRange: EHighlightsDateFilter;
  startDate: Date;
  endDate: Date;
  usersFilter: number[];
  templatesFilter: number[];
  filtersChanged: boolean;
}

export interface IHighlightsStore {
  count: number;
  isFeedLoading: boolean;
  isUsersLoading: boolean;
  isTemplatesTitlesLoading: boolean;
  items: IHighlightsItem[];
  templatesTitles: ITemplateTitleBaseWithCount[];
  filters: IHighlightsFilters;
}
