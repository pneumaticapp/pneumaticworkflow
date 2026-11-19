import type { IHighlightsFilters } from '../highlights/types';
import type { RootState } from '../store';
import type { IHighlightsItem } from '../../types/highlights';
import type { ITemplateTitleBaseWithCount } from '../../types/template';

export const getHighlightsCount = (state: RootState): number => state.highlights.count;

export const getHighlightsItems = (state: RootState): IHighlightsItem[] => state.highlights.items;

export const getHighlightsIsFeedLoading = (state: RootState): boolean => state.highlights.isFeedLoading;

export const getHighlightsIsTemplatesTitlesLoading = (state: RootState): boolean =>
  state.highlights.isTemplatesTitlesLoading;

export const getHighlightsTemplatesTitles = (state: RootState): ITemplateTitleBaseWithCount[] =>
  state.highlights.templatesTitles;

export const getHighlightsFilters = (state: RootState): IHighlightsFilters => state.highlights.filters;
