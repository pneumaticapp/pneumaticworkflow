import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IHighlightsFilters, IHighlightsStore } from '../../types/redux';
import { IGetHighlightsResponse } from '../../api/getHighlights';
import { IGetHighlightsTitlesRequestConfig, TGetHighlightsTitlesResponse } from '../../api/getHighlightsTitles';
import { EGeneralActions } from '../general/actions';
import { ILoadHighlightsConfig } from './types';
import { getInitHighlightsFilters } from './utils/getInitHighlightsFilters';

const getInitState = (): IHighlightsStore => ({
  count: 0,
  isFeedLoading: false,
  isTemplatesTitlesLoading: false,
  items: [],
  templatesTitles: [],
  filters: getInitHighlightsFilters(),
});

export const loadHighlights = createAction<ILoadHighlightsConfig>('highlights/loadHighlights');

const highlightsSlice = createSlice({
  name: 'highlights',
  initialState: getInitState,
  reducers: {
    loadHighlightsTemplatesTitles: (state, _action: PayloadAction<IGetHighlightsTitlesRequestConfig>) => {
      state.isTemplatesTitlesLoading = true;
    },

    loadHighlightsTemplatesTitlesFailed: (state) => {
      state.isTemplatesTitlesLoading = false;
    },

    setHighlightsTemplatesTitles: (state, action: PayloadAction<TGetHighlightsTitlesResponse>) => {
      state.templatesTitles = action.payload;
      state.isTemplatesTitlesLoading = false;
    },

    setHighlights: (state, action: PayloadAction<IGetHighlightsResponse>) => {
      state.items = action.payload.results;
      state.count = action.payload.count;
    },

    setHighlightsIsFeedLoading: (state, action: PayloadAction<boolean>) => {
      state.isFeedLoading = action.payload;
    },

    resetHighlightsStore: (state) => ({ ...getInitState(), filters: state.filters }),

    setHighlightsFilters: (state, action: PayloadAction<Partial<IHighlightsFilters>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },

    setHighlightsFiltersChanged: (state) => {
      state.filters.hasChangedFilters = true;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(EGeneralActions.ClearAppFilters, (state) => {
      state.filters = getInitHighlightsFilters();
    });
  },
});

export const {
  loadHighlightsTemplatesTitles,
  loadHighlightsTemplatesTitlesFailed,
  setHighlightsTemplatesTitles,
  setHighlights,
  setHighlightsIsFeedLoading,
  resetHighlightsStore,
  setHighlightsFilters,
  setHighlightsFiltersChanged,
} = highlightsSlice.actions;

export default highlightsSlice.reducer;
