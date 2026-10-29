import { IApplicationState, IHighlightsFilters } from '../../types/redux';
import { IHighlightsItem } from '../../types/highlights';
import { ITemplateTitleBaseWithCount } from '../../types/template';

export const getHighlightsCount = (state: IApplicationState): number => state.highlights.count;

export const getHighlightsItems = (state: IApplicationState): IHighlightsItem[] => state.highlights.items;

export const getHighlightsIsFeedLoading = (state: IApplicationState): boolean => state.highlights.isFeedLoading;

export const getHighlightsIsTemplatesTitlesLoading = (state: IApplicationState): boolean =>
  state.highlights.isTemplatesTitlesLoading;

export const getHighlightsTemplatesTitles = (state: IApplicationState): ITemplateTitleBaseWithCount[] =>
  state.highlights.templatesTitles;

export const getHighlightsFilters = (state: IApplicationState): IHighlightsFilters => state.highlights.filters;
