import type { IGetHighlightsConfig } from '../../api/getHighlights';
import type { EHighlightsDateFilter, IHighlightsItem } from '../../types/highlights';
import type { ITemplateTitleBaseWithCount } from '../../types/template';

export interface ILoadHighlightsConfig extends Omit<IGetHighlightsConfig, 'filters'> {
  onScroll?: boolean;
}

export interface IHighlightsFilters {
  timeRange: EHighlightsDateFilter;
  startDate: Date;
  endDate: Date;
  usersFilter: number[];
  templatesFilter: number[];
  hasChangedFilters: boolean;
}

export interface IHighlightsStore {
  count: number;
  isFeedLoading: boolean;
  isTemplatesTitlesLoading: boolean;
  items: IHighlightsItem[];
  templatesTitles: ITemplateTitleBaseWithCount[];
  filters: IHighlightsFilters;
}
