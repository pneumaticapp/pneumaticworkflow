/* eslint-disable */
/* prettier-ignore */
import { ICondition } from '../../TaskForm/Conditions';
import { getFilledConditions } from '../../TaskForm/Conditions/utils/conditionsValidators';

export function getConditionsCount(conditions: ICondition[]) {
  return getFilledConditions(conditions).reduce((acc, condition) => acc + condition.rules.length, 0);
}
