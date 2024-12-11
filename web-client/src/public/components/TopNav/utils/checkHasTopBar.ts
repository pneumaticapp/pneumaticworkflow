import { ESubscriptionPlan } from "../../../types/account";

export const checkHasTopBar = (isBlocked: boolean, plan: ESubscriptionPlan, isSupermode: boolean) => {
  return isBlocked || isSupermode;
}
