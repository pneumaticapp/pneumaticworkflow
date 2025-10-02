import { createConditionApiName } from '../../../../../utils/createId';
import { EConditionAction, ICondition } from '../types';
import { getEmptyRule } from './getEmptyRule';

export function getEmptyConditions(isSubscribed: boolean): ICondition[] {
  const newCondition = getOneEmptyCondition(isSubscribed);
  return [newCondition];
}

export function getOneEmptyCondition(isSubscribed: boolean, order?: number, startTask?: boolean): ICondition {
  const rules = isSubscribed ? [getEmptyRule()] : [];
  return {
    order: order || 1,
    apiName: createConditionApiName(),
    rules,
    action: startTask ? EConditionAction.StartTask : EConditionAction.SkipTask,
  };
}
