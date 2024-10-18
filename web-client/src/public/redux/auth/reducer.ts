/* eslint-disable no-param-reassign */
import produce from 'immer';
import * as moment from 'moment-timezone';

import { getBrowserConfig } from '../../utils/getConfig';
import { ELoggedState, IAuthUser } from '../../types/redux';
import { parseCookies } from '../../utils/cookie';
import { EUserStatus } from '../../types/user';

import { EAuthActions, EAuthUserFailType, TAuthActions } from './actions';
import { ESubscriptionPlan } from '../../types/account';
import { EAccountsActions, TAccountsActions } from '../actions';

const { googleAuthUserInfo, invitedUser } = getBrowserConfig();

const EMPTY_USER: IAuthUser = {
  email: '',
  account: {
    id: undefined,
    name: '',
    isVerified: false,
    tenantName: '',
    billingPlan: ESubscriptionPlan.Unknown,
    plan: ESubscriptionPlan.Unknown,
    planExpiration: null,
    leaseLevel: 'standard',
    logoSm: null,
    logoLg: null,
    paymentCardProvided: true,
    trialEnded: false,
    trialIsActive: false,
    isSubscribed: false
  },
  id: -1,
  isAdmin: false,
  firstName: '',
  lastName: '',
  token: parseCookies(document.cookie).token || '',
  phone: '',
  photo: '',
  loading: false,
  status: EUserStatus.Active,
  googleAuthUserInfo,
  invitedUser,
  isAccountOwner: true,
  isDigestSubscriber: false,
  isTasksDigestSubscriber: false,
  isCommentsMentionsSubscriber: false,
  isNewTasksSubscriber: false,
  isNewslettersSubscriber: false,
  isSpecialOffersSubscriber: false,
  type: 'user',
  loggedState: parseCookies(document.cookie)['token'] ? ELoggedState.LoggedIn : ELoggedState.LoggedOut,
  language: '',
  timezone: moment.tz.guess(),
  dateFmt: '',
  dateFdw: ''
};

export const INIT_STATE: IAuthUser = {
  ...EMPTY_USER,
  ...getBrowserConfig().user,
};

// eslint-disable-next-line @typescript-eslint/default-param-last
export const reducer = (state = INIT_STATE, action: TAuthActions | TAccountsActions): IAuthUser => {
  switch (action.type) {
    case EAuthActions.AuthUser:
      return { ...state, loading: true };
    case EAuthActions.AuthUserSuccess:
      return { ...state, loading: false, loggedState: ELoggedState.LoggedIn, ...action.payload };
    case EAuthActions.ChangePasswordSuccess:
    case EAuthActions.EditUserSuccess:
    case EAuthActions.RegisterUserSuccess:
    case EAuthActions.ResetPasswordSuccess:
      return { ...state, loading: false, ...action.payload };
    case EAuthActions.EditAccountSuccess:
      return { ...state, loading: false, account: { ...state.account, ...action.payload } };
    case EAuthActions.ChangePassword:
    case EAuthActions.EditUser:
    case EAuthActions.EditAccount:
    case EAuthActions.LoginUser:
    case EAuthActions.LoginSuperuser:
    case EAuthActions.RegisterUser:
    case EAuthActions.RegisterUserInvited:
    case EAuthActions.ForgotPassword:
    case EAuthActions.ResetPassword:
      return { ...state, loading: true };
    case EAuthActions.ForgotPasswordSuccess:
    case EAuthActions.EditFailed:
      return { ...state, loading: false };
    case EAuthActions.AuthUserFail:
      return produce(state, (draftState) => {
        draftState.error = action.payload ?? EAuthUserFailType.Common;
        draftState.loading = false;
      });
    case EAuthActions.ForgotPasswordFail:
    case EAuthActions.ResetPasswordFail:
    case EAuthActions.ChangePasswordFail:
      return { ...state, error: EAuthUserFailType.Common, loading: false };
    case EAuthActions.RemoveGoogleUser:
      return { ...state, googleAuthUserInfo: {} };
    case EAuthActions.SetToken:
      return { ...state, token: action.payload };
    case EAuthActions.SetUserPhoto:
      return { ...state, photo: action.payload };
    case EAuthActions.LogoutUserSuccess: {
      return { ...state, loggedState: ELoggedState.LoggedOut };
    }
    case EAccountsActions.SetCurrentPlan: {
      const { billingPlan, planExpiration } = action.payload;

      return produce(state, (draftState) => {
        draftState.account.billingPlan = billingPlan;
        draftState.account.planExpiration = planExpiration;
      });
    }

    default:
      return { ...state };
  }
};
