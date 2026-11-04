import { Middleware } from 'redux';
import type { RootState } from '../store';
import { EPlanActions, getPlanPendingActions } from '../../utils/getPlanPendingActions';
import { ENotificationsActions, ETemplatesActions } from '../actions';

export function createDeclineForbiddenActionsMiddleware(): Middleware {
  return ({ getState }) =>
    (next) =>
    (action) => {
      const TRIAL_ENDED_FORBIDDEN_ACTIONS = [ETemplatesActions.LoadTemplatesSystem, ENotificationsActions.LoadList];

      if (!TRIAL_ENDED_FORBIDDEN_ACTIONS.includes(action.type)) {
        next(action);
        return;
      }

      if (isTrialEnded(getState)) {
        return;
      }

      next(action);
    };
}

const isTrialEnded = (getState: () => RootState) => {
  const {
    authUser: {
      account: { billingPlan, isSubscribed, isBlocked },
    },
  }: RootState = getState();

  const pendingActions = getPlanPendingActions(billingPlan, isSubscribed, isBlocked);

  return pendingActions.includes(EPlanActions.ChoosePlan);
};
