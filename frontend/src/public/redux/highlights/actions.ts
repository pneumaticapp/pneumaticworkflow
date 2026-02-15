import { actionGenerator } from '../../utils/redux';
import { ITypedReduxAction, IHighlightsFilters } from '../../types/redux';
import { IGetHighlightsConfig, IGetHighlightsResponse } from '../../api/getHighlights';
import { IGetHighlightsTitlesRequestConfig, TGetHighlightsTitlesResponse } from '../../api/getHighlightsTitles';

export enum EHighlightsActions {
  LoadHighlights = 'LOAD_HIGHLIGHTS',
  LoadHighlightsTemplatesTitles = 'LOAD_HIGHLIGHTS_TEMPLATES_TITLES',
  LoadHighlightsTemplatesTitlesFailed = 'LOAD_HIGHLIGHTS_TEMPLATES_TITLES_FAILED',
  ResetHighlightsStore = 'RESET_HIGHLIGHTS_STORE',
  SetEndDate = 'SET_END_DATE',
  SetHighlights = 'SET_HIGHLIGHTS',
  SetStartDate = 'SET_START_DATE',
  SetTemplatesTitles = 'SET_HIGHLIGHTS_TEMPLATES_TITLES',
  SetIsFeedLoading = 'IS_FEED_LOADING',
  SetFilters = 'SET_HIGLIGHTS_FILTERS',
  SetFiltersManuallyChanged = 'SET_HIGHTLIGHTS_FILTERS_MANUALLY_CHANGED',
}

export interface ILoadHighlightsConfig extends Omit<IGetHighlightsConfig, 'filters'> {
  onScroll?: boolean;
}

export type TLoadHighlights = ITypedReduxAction<EHighlightsActions.LoadHighlights, ILoadHighlightsConfig>;

export const loadHighlights: (payload: ILoadHighlightsConfig) => TLoadHighlights = actionGenerator<
  EHighlightsActions.LoadHighlights,
  ILoadHighlightsConfig
>(EHighlightsActions.LoadHighlights);

export type TSetHighlights = ITypedReduxAction<EHighlightsActions.SetHighlights, IGetHighlightsResponse>;

export const setHighlights: (payload: IGetHighlightsResponse) => TSetHighlights = actionGenerator<
  EHighlightsActions.SetHighlights,
  IGetHighlightsResponse
>(EHighlightsActions.SetHighlights);

export type TLoadHighlightsTemplatesTitles = ITypedReduxAction<
  EHighlightsActions.LoadHighlightsTemplatesTitles,
  IGetHighlightsTitlesRequestConfig
>;

export type TLoadHighlightsTemplatesTitlesFailed = ITypedReduxAction<
  EHighlightsActions.LoadHighlightsTemplatesTitlesFailed,
  void
>;
export const loadHighlightsTemplatesTitlesFailed: (payload?: void) => TLoadHighlightsTemplatesTitlesFailed =
  actionGenerator<EHighlightsActions.LoadHighlightsTemplatesTitlesFailed, void>(
    EHighlightsActions.LoadHighlightsTemplatesTitlesFailed,
  );

export const loadHighlightsTemplatesTitles: (
  payload: IGetHighlightsTitlesRequestConfig,
) => TLoadHighlightsTemplatesTitles = actionGenerator<
  EHighlightsActions.LoadHighlightsTemplatesTitles,
  IGetHighlightsTitlesRequestConfig
>(EHighlightsActions.LoadHighlightsTemplatesTitles);

export type TSetHighlightsTemplatesTitles = ITypedReduxAction<
  EHighlightsActions.SetTemplatesTitles,
  TGetHighlightsTitlesResponse
>;

export const setSetHighlightsTemplatesTitles: (payload: TGetHighlightsTitlesResponse) => TSetHighlightsTemplatesTitles =
  actionGenerator<EHighlightsActions.SetTemplatesTitles, TGetHighlightsTitlesResponse>(
    EHighlightsActions.SetTemplatesTitles,
  );

export type TResetHighlightsStore = ITypedReduxAction<EHighlightsActions.ResetHighlightsStore, void>;

export const resetHightlightsStore: (payload?: void) => TResetHighlightsStore = actionGenerator<
  EHighlightsActions.ResetHighlightsStore,
  void
>(EHighlightsActions.ResetHighlightsStore);

export type TSetStartDate = ITypedReduxAction<EHighlightsActions.SetStartDate, Date>;
export const setStartDate: (payload: Date) => TSetStartDate = actionGenerator<EHighlightsActions.SetStartDate, Date>(
  EHighlightsActions.SetStartDate,
);

export type TSetEndDate = ITypedReduxAction<EHighlightsActions.SetEndDate, Date>;
export const setEndDate: (payload: Date) => TSetEndDate = actionGenerator<EHighlightsActions.SetEndDate, Date>(
  EHighlightsActions.SetEndDate,
);

export type TSetIsFeedLoading = ITypedReduxAction<EHighlightsActions.SetIsFeedLoading, boolean>;
export const setIsFeedLoading: (payload: boolean) => TSetIsFeedLoading = actionGenerator<
  EHighlightsActions.SetIsFeedLoading,
  boolean
>(EHighlightsActions.SetIsFeedLoading);

export type TSetFilters = ITypedReduxAction<EHighlightsActions.SetFilters, Partial<IHighlightsFilters>>;
export const setFilters: (payload: Partial<IHighlightsFilters>) => TSetFilters = actionGenerator<
  EHighlightsActions.SetFilters,
  Partial<IHighlightsFilters>
>(EHighlightsActions.SetFilters);

export type TSetFiltersManuallyChanged = ITypedReduxAction<EHighlightsActions.SetFiltersManuallyChanged, void>;
export const setHighlightsFiltersManuallyChanged: (payload?: void) => TSetFiltersManuallyChanged = actionGenerator<
  EHighlightsActions.SetFiltersManuallyChanged,
  void
>(EHighlightsActions.SetFiltersManuallyChanged);

export type THighlightsActions =
  | TLoadHighlights
  | TLoadHighlightsTemplatesTitles
  | TLoadHighlightsTemplatesTitlesFailed
  | TResetHighlightsStore
  | TSetEndDate
  | TSetHighlights
  | TSetStartDate
  | TSetHighlightsTemplatesTitles
  | TSetIsFeedLoading
  | TSetFilters
  | TSetFiltersManuallyChanged;
