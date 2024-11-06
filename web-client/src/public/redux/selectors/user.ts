import { createSelector } from 'reselect';
import { IAccounts, IApplicationState, IAuthUser, IGenericTemplatesStore } from '../../types/redux';
import { TUserListItem } from '../../types/user';
import { getPlanPendingActions } from '../../utils/getPlanPendingActions';

export const getAuthUser = ({ authUser }: IApplicationState) => ({ authUser });

export const getSubscriptionPlan = ({
  authUser: {
    account: { billingPlan },
  },
}: IApplicationState) => billingPlan;

export const getTrialEnded = ({
  authUser: {
    account: { trialEnded },
  },
}: IApplicationState) => trialEnded;

export const getIsBlocked = ({
  authUser: {
    account: { isBlocked },
  },
}: IApplicationState) => isBlocked;

export const getIsAdmin = ({ authUser }: IApplicationState) => authUser.isAdmin || false;

export const getIsUserSubsribed = ({
  authUser: {
    account: { isSubscribed },
  },
}: IApplicationState) => {
  return isSubscribed;
};

export const getUserPendingActions = createSelector(
  getSubscriptionPlan,
  getIsUserSubsribed,
  getIsBlocked,
  getPlanPendingActions,
);

export const getUserToken = (state: IApplicationState): Pick<IAuthUser, 'token'> => ({
  token: state.authUser.token || '',
});

export const getInvitedUser = (state: IApplicationState): Pick<IAuthUser, 'invitedUser'> => ({
  invitedUser: state.authUser.invitedUser || {},
});

export const getAccountsStore = (state: IApplicationState): IAccounts => state.accounts;

export const getSelectedGenericTemplates = (state: IApplicationState): Pick<IGenericTemplatesStore, 'selected'> => ({
  selected: state.genericTemplates.selected,
});

export const getUsers = (state: IApplicationState): TUserListItem[] => state.accounts.users;

export const getUserApiKey = (state: IApplicationState) => state.integrations.apiKey;

export const getLanguage = ({ authUser }: IApplicationState) => (authUser.language);

