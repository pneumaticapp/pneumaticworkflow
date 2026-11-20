import type { IHighlightsFilters, IHighlightsStore } from '../highlights/types';
import type { RootState } from '../store';

export const getHighlightsStore = (state: RootState): IHighlightsStore => state.highlights;

export const getHighlightsFilters = (state: RootState): IHighlightsFilters => state.highlights.filters;
