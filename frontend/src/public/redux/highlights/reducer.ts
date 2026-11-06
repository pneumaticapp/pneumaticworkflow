import { produce } from 'immer';
import { endOfToday, startOfToday } from 'date-fns';

import type { IHighlightsFilters, IHighlightsStore } from './types';
import { EHighlightsDateFilter } from '../../types/highlights';
import type { IHighlightsItem } from '../../types/highlights';
import type { ITemplateTitleBaseWithCount } from '../../types/template';

import { EHighlightsActions } from './actions';
import type { THighlightsActions } from './actions';
import { EGeneralActions } from '../general/actions';
import type { TGeneralActions } from '../general/actions';

export const INIT_FILTERS: IHighlightsFilters = {
  timeRange: EHighlightsDateFilter.Today,
  startDate: startOfToday(),
  endDate: endOfToday(),
  usersFilter: [],
  templatesFilter: [],
  filtersChanged: false,
};

const INIT_STATE: IHighlightsStore = {
  count: 0,
  isFeedLoading: false,
  isUsersLoading: false,
  isTemplatesTitlesLoading: false,
  items: [] as IHighlightsItem[],
  templatesTitles: [] as ITemplateTitleBaseWithCount[],
  filters: INIT_FILTERS,
};

export const reducer = (state = INIT_STATE, action: THighlightsActions | TGeneralActions): IHighlightsStore => {
  switch (action.type) {
    case EHighlightsActions.LoadHighlightsTemplatesTitles:
      return { ...state, isTemplatesTitlesLoading: true };
    case EHighlightsActions.LoadHighlightsTemplatesTitlesFailed:
      return { ...state, isTemplatesTitlesLoading: false };
    case EHighlightsActions.SetTemplatesTitles:
      return { ...state, templatesTitles: action.payload, isTemplatesTitlesLoading: false };
    case EHighlightsActions.LoadHighlights:
      return { ...state };
    case EHighlightsActions.SetHighlights:
      return { ...state, items: action.payload.results, count: action.payload.count };
    case EHighlightsActions.SetIsFeedLoading:
      return { ...state, isFeedLoading: action.payload };
    case EHighlightsActions.ResetHighlightsStore:
      return { ...INIT_STATE, filters: state.filters };
    case EHighlightsActions.SetEndDate:
      return produce(state, (draftState) => {
        draftState.filters.endDate = action.payload;
      });
    case EHighlightsActions.SetStartDate:
      return produce(state, (draftState) => {
        draftState.filters.startDate = action.payload;
      });
    case EHighlightsActions.SetFilters:
      return produce(state, (draftState) => {
        draftState.filters = { ...state.filters, ...action.payload };
      });
    case EHighlightsActions.SetFiltersManuallyChanged:
      return produce(state, (draftState) => {
        draftState.filters.filtersChanged = true;
      });
    case EGeneralActions.ClearAppFilters:
      return { ...state, filters: INIT_FILTERS };
    default:
      return { ...state };
  }
};
