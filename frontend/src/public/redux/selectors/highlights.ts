import { IHighlightsStore, IHighlightsFilters } from '../../types/redux';
import type { IApplicationState } from '../store';

export const getHighlightsStore = (state: IApplicationState): IHighlightsStore => state.highlights;

export const getHighlightsFilters = (state: IApplicationState): IHighlightsFilters => state.highlights.filters;
