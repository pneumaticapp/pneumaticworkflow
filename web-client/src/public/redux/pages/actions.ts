import { actionGenerator } from '../../utils/redux';
import { ITypedReduxAction } from '../../types/redux';
import { IPages } from '../../types/page';

export const enum EPagesActions {
  LoadPages = 'LOAD_PAGES',
  LoadPagesSuccess = 'LOAD_PAGES_SUCCESS',
  LoadPagesFailed = 'LOAD_PAGES_FAILED',
}

export type TLoadPages = ITypedReduxAction<EPagesActions.LoadPages, void>;
export const loadPages: (payload?: void) => TLoadPages = actionGenerator<EPagesActions.LoadPages, void>(
  EPagesActions.LoadPages,
);

export type TLoadPagesSuccess = ITypedReduxAction<EPagesActions.LoadPagesSuccess, IPages>;
export const loadPagesSuccess: (payload: IPages) => TLoadPagesSuccess = actionGenerator<
  EPagesActions.LoadPagesSuccess,
  IPages
>(EPagesActions.LoadPagesSuccess);

export type TLoadPagesFailed = ITypedReduxAction<EPagesActions.LoadPagesFailed, void>;
export const loadPagesFailed: (payload?: void) => TLoadPagesFailed = actionGenerator<
  EPagesActions.LoadPagesFailed,
  void
>(EPagesActions.LoadPagesFailed);

export type TPagesActions = TLoadPages | TLoadPagesSuccess | TLoadPagesFailed;
