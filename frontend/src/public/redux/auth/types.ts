import type { TAuthUserResult } from '../../types/user';

export enum ELoggedState {
  LoggedIn = 'logged-in',
  LoggedOut = 'logged-out',
}

export enum EAuthUserFailType {
  Common = 'common',
  NotVerified = 'not-verified',
}

export interface IAuthUser extends TAuthUserResult {
  error?: EAuthUserFailType;
  superUserToken?: string;
  loading: boolean;
  loggedState: ELoggedState;
}
