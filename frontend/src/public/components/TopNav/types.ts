import type { ReactNode } from 'react';

import { EPaywallReminderType } from './utils/getPaywallType';
import { EPlanActions } from '../../utils/getPlanPendingActions';
import { ESubscriptionPlan } from '../../types/account';
import { IAccount, TAccountLeaseLevel } from '../../types/user';
import { EWorkflowsView } from '../../types/workflow';

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
