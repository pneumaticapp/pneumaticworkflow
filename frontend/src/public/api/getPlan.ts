import { commonRequest } from './commonRequest';
import type { IAccountPlan } from '../types/account';

export type TGetPlanResponse = IAccountPlan;

export function getPlan() {
  return commonRequest<TGetPlanResponse>('getPlan', {}, { shouldThrow: true });
}
