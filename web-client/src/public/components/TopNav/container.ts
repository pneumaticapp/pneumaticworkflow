import { connect } from 'react-redux';

import { ITopNavDispatchProps, ITopNavProps, TopNav } from './TopNav';
import { IApplicationState } from '../../types/redux';
import {
  logoutUser,
  setNotificationsListIsOpen,
  showPlanExpiredMessage,
  returnFromSupermode,
  redirectToCustomerPortal,
} from '../../redux/actions';
import { getPaywallType } from './utils/getPaywallType';
import { getIsUserSubsribed, getUserPendingActions } from '../../redux/selectors/user';
import { getBrowserConfig } from '../../utils/getConfig';

type TStoreProps = Pick<
  ITopNavProps,
  | 'paywallType'
  | 'pendingActions'
  | 'unreadNotificationsCount'
  | 'isSubscribed'
  | 'isSupermode'
  | 'tenantName'
  | 'leaseLevel'
  | 'isAccountOwner'
  | 'accountOwnerPlan'
>;

const mapStateToProps = (state: IApplicationState): TStoreProps => {
  const { authUser, notifications, accounts } = state;
  const { billingPlan } = accounts.planInfo;
  const { unreadItemsCount: unreadNotificationsCount } = notifications;

  const { user } = getBrowserConfig();
  const paywallType = getPaywallType(billingPlan, authUser.account.isBlocked);
  const pendingActions = getUserPendingActions(state);
  const isSubscribed = getIsUserSubsribed(state);
  const isSupermode = Boolean(authUser.isSupermode);

  return {
    paywallType,
    pendingActions,
    unreadNotificationsCount,
    isSubscribed,
    isSupermode,
    tenantName: authUser.account.tenantName,
    leaseLevel: authUser.account.leaseLevel,
    isAccountOwner: authUser.isAccountOwner,
    accountOwnerPlan: user.account || authUser.account,
  };
};

const mapDispatchToProps: ITopNavDispatchProps = {
  logoutUser,
  setNotificationsListIsOpen,
  showPlanExpiredMessage,
  returnFromSupermode,
  redirectToCustomerPortal,
};

export const TopNavContainer = connect(mapStateToProps, mapDispatchToProps)(TopNav);
