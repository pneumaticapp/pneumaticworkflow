import { createSelector } from 'reselect';
import { IAccounts, IAuthUser, IGenericTemplatesStore } from '../../types/redux';
import type { RootState } from '../store';
import { TUserListItem } from '../../types/user';
import { getPlanPendingActions } from '../../utils/getPlanPendingActions';

export const getAuthUser = ({ authUser }: RootState) => ({ authUser });

export const getSubscriptionPlan = ({
  authUser: {
    account: { billingPlan },
  },
}: RootState) => billingPlan;

export const getTrialEnded = ({
  authUser: {
    account: { trialEnded },
  },
}: RootState) => trialEnded;

export const getIsBlocked = ({
  authUser: {
    account: { isBlocked },
  },
}: RootState) => isBlocked;

export const getIsAdmin = ({ authUser }: RootState) => authUser.isAdmin || false;

/** Mirrors UserIsAdminOrAccountOwner on /templates/integrations, which 403s for anyone else. */
export const getCanAccessTemplateIntegrations = ({ authUser }: RootState) =>
  authUser?.isAdmin || authUser?.isAccountOwner || false;

export const getCanAccessWorkflows = ({ authUser }: RootState) =>
  authUser?.isAdmin || authUser?.hasWorkflowViewerAccess || authUser?.hasWorkflowStarterAccess || false;

export const getHasExtendedInterface = ({ authUser }: RootState) =>
  authUser?.isAdmin || authUser?.hasWorkflowViewerAccess || false;

export const getHasBasicInterface = ({ authUser }: RootState) =>
  (authUser?.hasWorkflowStarterAccess && !authUser?.hasWorkflowViewerAccess && !authUser?.isAdmin) || false;

export const getIsUserSubsribed = ({
  authUser: {
    account: { isSubscribed },
  },
}: RootState) => {
  return isSubscribed;
};

export const getUserPendingActions = createSelector(
  getSubscriptionPlan,
  getIsUserSubsribed,
  getIsBlocked,
  getPlanPendingActions,
);

export const getUserToken = (state: RootState): Pick<IAuthUser, 'token'> => ({
  token: state.authUser.token || '',
});

export const getInvitedUser = (state: RootState): Pick<IAuthUser, 'invitedUser'> => ({
  invitedUser: state.authUser.invitedUser || {},
});

export const getAccountsStore = (state: RootState): IAccounts => state.accounts;

export const getSelectedGenericTemplates = (state: RootState): Pick<IGenericTemplatesStore, 'selected'> => ({
  selected: state.genericTemplates.selected,
});

export const getGroupsStore = ({ groups }: RootState) => groups;

export const getUsers = (state: RootState): TUserListItem[] => state.accounts.users;

export const getUserApiKeys = (state: RootState) => state.integrations.apiKeys;

export const getUserApiKey = createSelector(getUserApiKeys, (apiKeys) => ({
  isLoading: apiKeys.isLoading,
  data: apiKeys.data[0]?.prefix || '',
}));

export const getUserTimezone = (state: RootState): string => state.authUser.timezone;

export const getLanguage = ({ authUser }: RootState) => authUser.language;

export const getAccountId = (state: RootState): number => state.authUser.account?.id ?? -1;
