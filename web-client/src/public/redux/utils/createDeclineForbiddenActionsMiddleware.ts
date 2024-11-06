import { Middleware } from 'redux';
import { IApplicationState } from '../../types/redux';
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

const isTrialEnded = (getState: () => IApplicationState) => {
  const {
    authUser: {
      account: { billingPlan, isSubscribed, isBlocked },
    },
  }: IApplicationState = getState();

  const pendingActions = getPlanPendingActions(billingPlan, isSubscribed, isBlocked);

  return pendingActions.includes(EPlanActions.ChoosePlan);
};
