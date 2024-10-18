import { ESubscriptionPlan } from '../../../types/account';

export enum EPaywallReminderType {
  Free = 'paywall-free',
  Blocked = 'paywall-blocked',
}

export function getPaywallType(billingPlan: ESubscriptionPlan, isBlocked?: boolean,): EPaywallReminderType | null {
  if (isBlocked) {
    return EPaywallReminderType.Blocked;
  }

  const noPaywallPlans = [
    ESubscriptionPlan.Unlimited,
    ESubscriptionPlan.FractionalCOO,
    ESubscriptionPlan.Premium,
    ESubscriptionPlan.Unknown,
  ];
  if (noPaywallPlans.some((noPaywalPlan) => noPaywalPlan === billingPlan)) {
    return null;
  }

  return EPaywallReminderType.Free;
}
