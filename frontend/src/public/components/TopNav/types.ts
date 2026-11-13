import type { ReactNode } from 'react';

import type { EPaywallReminderType } from './utils/getPaywallType';
import type { EPlanActions } from '../../utils/getPlanPendingActions';
import type { ESubscriptionPlan } from '../../types/account';
import type { IAccount, TAccountLeaseLevel } from '../../types/user';
import type { EWorkflowsView } from '../../types/workflow';

export interface ITopNavProps {
  leftContent?: ReactNode;
  isFromWorkflowsLayout?: boolean;
  workflowsView?: EWorkflowsView;
}

export interface ITopNavStateProps {
  pendingActions: EPlanActions[];
  paywallType: EPaywallReminderType | null;
  plan: ESubscriptionPlan;
  unreadNotificationsCount: number;
  isSupermode: boolean;
  tenantName: string;
  leaseLevel: TAccountLeaseLevel;
  isAccountOwner: boolean;
  accountOwnerPlan: IAccount;
  isAdmin: boolean;
  firstName: string;
  lastName: string;
}

export interface ITopNavDispatchProps {
  logoutUser(): void;
  setNotificationsListIsOpen(isOpen: boolean): void;
  returnFromSupermode(): void;
  redirectToCustomerPortal(): void;
}

export type TTopNavContentProps = ITopNavProps & ITopNavStateProps & ITopNavDispatchProps;

export type TProfileDropdownProps = Pick<
  TTopNavContentProps,
  | 'firstName'
  | 'lastName'
  | 'leaseLevel'
  | 'plan'
  | 'isAccountOwner'
  | 'isAdmin'
  | 'logoutUser'
  | 'redirectToCustomerPortal'
>;
