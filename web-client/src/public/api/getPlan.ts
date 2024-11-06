import { commonRequest } from './commonRequest';
import { IAccountPlan } from '../types/redux';

export type TGetPlanResponse = IAccountPlan;

export function getPlan() {
  return commonRequest<TGetPlanResponse>(
    'getPlan',
    {},
    {shouldThrow: true},
  );
}
