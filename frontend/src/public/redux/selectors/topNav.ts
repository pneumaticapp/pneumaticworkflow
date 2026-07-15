import { createSelector } from 'reselect';

import { IApplicationState } from '../../types/redux';
import { getBrowserConfig } from '../../utils/getConfig';
import { getPaywallType } from '../../components/TopNav/utils/getPaywallType';
import { getAccountPlan } from './accounts';
import { getCurrentUser } from './authUser';
import { getNotificationsStore } from './notifications';
import { getSubscriptionPlan, getUserPendingActions } from './user';

const getAccountOwnerPlan = (state: IApplicationState) =>
  getBrowserConfig().user.account || getCurrentUser(state).account;

export const getTopNavState = createSelector(
  [
    getAccountPlan,
    getCurrentUser,
    getNotificationsStore,
    getUserPendingActions,
    getSubscriptionPlan,
    getAccountOwnerPlan,
  ],
  (accountPlan, authUser, notifications, pendingActions, plan, accountOwnerPlan) => ({
    paywallType: getPaywallType(accountPlan.billingPlan, authUser.account.isBlocked),
    pendingActions,
    unreadNotificationsCount: notifications.unreadItemsCount,
    plan,
    isSupermode: Boolean(authUser.isSupermode),
    tenantName: authUser.account.tenantName,
    leaseLevel: authUser.account.leaseLevel,
    isAccountOwner: authUser.isAccountOwner,
    accountOwnerPlan,
    isAdmin: authUser.isAdmin ?? false,
    firstName: authUser.firstName,
    lastName: authUser.lastName,
  }),
);
