/* eslint-disable */
/* prettier-ignore */
import { ICondition } from '..';
import { isArrayWithItems } from '../../../../../utils/helpers';

export function shoudShowPaywall(conditions: ICondition[], isSubscribed: boolean) {
  if (isSubscribed) {
    return false;
  }

  if (!isArrayWithItems(conditions)) {
    return true;
  }

  return conditions.every(({ rules }) => !isArrayWithItems(rules));
}
