/* eslint-disable */
/* prettier-ignore */
import { ITypedReduxAction } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { IAccountGenericTemplate } from '../../types/genericTemplates';

export const enum EGenericTemplatesActions {
  Change = 'CHANGE_GENERIC_TEMPLATE',
  Fetch = 'FETCH_GENERIC_TEMPLATES',
  FetchFailed = 'FETCH_GENERIC_TEMPLATES_FAILED',
  Set = 'SET_GENERIC_TEMPLATES',
  SetSelected = 'SET_SELECTED_GENERIC_TEMPLATES',
  SaveSelected = 'SAVE_SELECTED_GENERIC_TEMPLATES',
}

export type TSelectGenericTemplate = ITypedReduxAction<EGenericTemplatesActions.Change, number>;
export const changeSelectGenericTemplate: (payload: number) => TSelectGenericTemplate =
  actionGenerator<EGenericTemplatesActions.Change, number>(EGenericTemplatesActions.Change);

export type TSetSelectedGenericTemplates = ITypedReduxAction<EGenericTemplatesActions.SetSelected, number[]>;
export const setSelectedGenericTemplates: (payload: number[]) => TSetSelectedGenericTemplates =
  actionGenerator<EGenericTemplatesActions.SetSelected, number[]>(EGenericTemplatesActions.SetSelected);

export type TSaveSelectedGenericTemplates = ITypedReduxAction<EGenericTemplatesActions.SaveSelected, void>;
export const saveSelectedGenericTemplates: (payload?: void) => TSaveSelectedGenericTemplates =
  actionGenerator<EGenericTemplatesActions.SaveSelected, void>(EGenericTemplatesActions.SaveSelected);

export type TSetGenericTemplates = ITypedReduxAction<EGenericTemplatesActions.Set, IAccountGenericTemplate[]>;
export const setGenericTemplates: (payload: IAccountGenericTemplate[]) => TSetGenericTemplates =
  actionGenerator<EGenericTemplatesActions.Set, IAccountGenericTemplate[]>(EGenericTemplatesActions.Set);

export type TFetchGenericTemplates = ITypedReduxAction<EGenericTemplatesActions.Fetch, void>;
export const fetchGenericTemplates: (payload?: void) => TFetchGenericTemplates =
  actionGenerator<EGenericTemplatesActions.Fetch, void>(EGenericTemplatesActions.Fetch);

export type TFetchGenericTemplatesFailed = ITypedReduxAction<EGenericTemplatesActions.FetchFailed, void>;
export const fetchGenericTemplatesFailed: (payload?: void) => TFetchGenericTemplatesFailed =
  actionGenerator<EGenericTemplatesActions.FetchFailed, void>(EGenericTemplatesActions.FetchFailed);

export type TGenericTemplatesActions =
  | TSelectGenericTemplate
  | TSetGenericTemplates
  | TSetSelectedGenericTemplates
  | TFetchGenericTemplates;
