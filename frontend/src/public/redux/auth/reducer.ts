import produce from 'immer';
import * as moment from 'moment-timezone';
import { mapToCamelCase } from '../../utils/mappers';

import { getBrowserConfig } from '../../utils/getConfig';
import { ELoggedState, IAuthUser } from '../../types/redux';
import { parseCookies } from '../../utils/cookie';
import { EUserStatus } from '../../types/user';

import { EAuthActions, EAuthUserFailType, TAuthActions } from './actions';
import { setCurrentPlan, changeUserManager, changeUserReports } from '../accounts/slice';
import { ESubscriptionPlan } from '../../types/account';

const { invitedUser } = getBrowserConfig();

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
    trialEnded: false,
    trialIsActive: false,
    isSubscribed: false,
    billingSync: true,
  },
  id: -1,
  isAdmin: false,
  managerId: null,
  hasWorkflowViewerAccess: false,
  firstName: '',
  lastName: '',
  token: parseCookies(document.cookie).token || '',
  phone: '',
  photo: '',
  loading: false,
  status: EUserStatus.Active,
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
  dateFdw: '',
  reportIds: [],
};

/**
 * Normalize API response field `subordinatesIds` to internal `reportIds`.
 * The backend returns `subordinates_ids` (camelCased to `subordinatesIds`),
 * but internal Redux state uses `reportIds`.
 */
function normalizeSubordinates(data: Record<string, any>): Record<string, any> {
  if (data && 'subordinatesIds' in data && !('reportIds' in data)) {
    const { subordinatesIds, ...rest } = data;
    return { ...rest, reportIds: subordinatesIds };
  }
  return data;
}

export const INIT_STATE: IAuthUser = {
  ...EMPTY_USER,
  ...normalizeSubordinates(mapToCamelCase(getBrowserConfig().user) as Record<string, any>),
} as IAuthUser;

// eslint-disable-next-line @typescript-eslint/default-param-last
export const reducer = (state = INIT_STATE, action: TAuthActions | { type: string; payload: any }): IAuthUser => {
  switch (action.type) {
    case EAuthActions.AuthUser:
      return { ...state, loading: true };
    case EAuthActions.AuthUserSuccess:
      return {
        ...state, loading: false, loggedState: ELoggedState.LoggedIn,
        ...normalizeSubordinates(action.payload as Record<string, any>),
      };
    case EAuthActions.ChangePasswordSuccess:
    case EAuthActions.EditUserSuccess:
    case EAuthActions.RegisterUserSuccess:
    case EAuthActions.ResetPasswordSuccess:
      return { ...state, loading: false, ...normalizeSubordinates(action.payload as Record<string, any>) };
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
    case EAuthActions.SetToken:
      return { ...state, token: action.payload };
    case EAuthActions.SetUserPhoto:
      return { ...state, photo: action.payload };
    case EAuthActions.LogoutUserSuccess: {
      return { ...state, loggedState: ELoggedState.LoggedOut };
    }
    case setCurrentPlan.type: {
      const { billingPlan, planExpiration } = action.payload;

      return produce(state, (draftState) => {
        draftState.account.billingPlan = billingPlan;
        draftState.account.planExpiration = planExpiration;
      });
    }
    case EAuthActions.VacationSuccess:
      return {
        ...state,
        vacation: action.payload.vacation,
      };

    case changeUserManager.type: {
      const { id: userId, managerId } = action.payload as { id: number; managerId: number | null };

      return produce(state, (draftState) => {
        if (state.id === userId) {
          draftState.managerId = managerId;
        }
        if (state.reportIds && state.reportIds.includes(userId) && state.id !== managerId) {
          draftState.reportIds = state.reportIds.filter(id => id !== userId);
        }
        if (state.id === managerId && (!state.reportIds || !state.reportIds.includes(userId))) {
          draftState.reportIds = [...(state.reportIds || []), userId];
        }
      });
    }

    case changeUserReports.type: {
      const { id: userId, reportIds } = action.payload as { id: number; reportIds: number[] };

      return produce(state, (draftState) => {
        if (state.id === userId) {
          draftState.reportIds = reportIds;
        }

        if (state.id !== userId && state.reportIds) {
          const filtered = state.reportIds.filter(rId => !reportIds.includes(rId));
          if (filtered.length !== state.reportIds.length) {
            draftState.reportIds = filtered;
          }
        }

        if (reportIds.includes(state.id)) {
          draftState.managerId = userId;
        } else if (state.managerId === userId && !reportIds.includes(state.id)) {
          draftState.managerId = null;
        }
      });
    }

    default:
      return { ...state };
  }
};
