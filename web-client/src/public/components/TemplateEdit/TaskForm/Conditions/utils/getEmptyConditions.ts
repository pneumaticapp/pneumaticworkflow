/* eslint-disable */
/* prettier-ignore */
import { createConditionApiName } from '../../../../../utils/createId';
import { EConditionAction, ICondition } from '../types';
import { getEmptyRule } from './getEmptyRule';

export function getEmptyConditions(isSubscribed: boolean): ICondition[] {
  const rules = isSubscribed ? [getEmptyRule()] : [];

  return [
    {
      order: 1,
      apiName: createConditionApiName(),
      rules,
      action: EConditionAction.EndProcess,
    },
  ];
}
