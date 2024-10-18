import { ESubscriptionPlan } from '../types/account';

export enum EPlanActions {
  Upgrade = 'upgrade',
  ChoosePlan = 'choose_plan',
}

export function getPlanPendingActions(
  billingPlan: ESubscriptionPlan,
  isSubscribed: boolean,
  isBlocked?: boolean,
): EPlanActions[] {
  const actionsMap = [
    {
      action: EPlanActions.Upgrade,
      isActive: billingPlan === ESubscriptionPlan.Free || isBlocked,
    },
    {
      action: EPlanActions.ChoosePlan,
      isActive:
        (billingPlan === ESubscriptionPlan.Premium ||
          billingPlan === ESubscriptionPlan.Unlimited ||
          billingPlan === ESubscriptionPlan.FractionalCOO) &&
        !isSubscribed,
    },
  ];

  const actions = actionsMap.filter(({ isActive }) => isActive).map(({ action }) => action);

  return actions;
}
