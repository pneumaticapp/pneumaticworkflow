import { IApplicationState, IHighlightsStore, IHighlightsFilters } from '../../types/redux';

export const getHighlightsStore = (state: IApplicationState): IHighlightsStore => (
  state.highlights
);

export const getHighlightsFilters = (state: IApplicationState): IHighlightsFilters => (
  state.highlights.filters
);
