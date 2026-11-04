import type { ICondition } from '../../TaskForm/Conditions/types';
import { getFilledConditions } from '../../TaskForm/Conditions/utils/conditionsValidators';

export function getConditionsCount(conditions: ICondition[]) {
  return getFilledConditions(conditions).reduce((acc, condition) => acc + condition.rules.length, 0);
}
