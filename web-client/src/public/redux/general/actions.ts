/* eslint-disable */
/* prettier-ignore */
import { ITypedReduxAction } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';

export const enum EGeneralActions {
  SetGeneralLoaderVisibility = 'SET_GENERAL_LOADER_VISIBILITY',
  OpenFullscreenImage = 'OPEN_FULLSCREEN_IMAGE',
  CloseFullscreenImage = 'CLOSE_FULLSCREEN_IMAGE',
  ClearAppFilters = 'CLEAR_APP_FILTERS',
}

export type TSetGeneralLoaderVisibility = ITypedReduxAction<EGeneralActions.SetGeneralLoaderVisibility, boolean>;
export const setGeneralLoaderVisibility: (payload: boolean) => TSetGeneralLoaderVisibility = actionGenerator<
  EGeneralActions.SetGeneralLoaderVisibility,
  boolean
>(EGeneralActions.SetGeneralLoaderVisibility);

type TOpenFullscreenImagePayload = { url: string };
export type TOpenFullscreenImage = ITypedReduxAction<EGeneralActions.OpenFullscreenImage, TOpenFullscreenImagePayload>;
export const openFullscreenImage: (payload: TOpenFullscreenImagePayload) => TOpenFullscreenImage = actionGenerator<
  EGeneralActions.OpenFullscreenImage,
  TOpenFullscreenImagePayload
>(EGeneralActions.OpenFullscreenImage);

export type TCloseFullscreenImage = ITypedReduxAction<EGeneralActions.CloseFullscreenImage, void>;
export const closeFullscreenImage: (payload?: void) => TCloseFullscreenImage = actionGenerator<
  EGeneralActions.CloseFullscreenImage,
  void
>(EGeneralActions.CloseFullscreenImage);

export type TClearAppFilters = ITypedReduxAction<EGeneralActions.ClearAppFilters, void>;
export const clearAppFilters: (payload?: void) => TClearAppFilters = actionGenerator<
  EGeneralActions.ClearAppFilters,
  void
>(EGeneralActions.ClearAppFilters);

export type TGeneralActions =
  | TSetGeneralLoaderVisibility
  | TOpenFullscreenImage
  | TCloseFullscreenImage
  | TClearAppFilters;
