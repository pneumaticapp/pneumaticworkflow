import { createConditionApiName } from '../../../../../utils/createId';
import { EConditionAction, ICondition } from '../types';
import { getBaseStartRule } from './getStartTaskRule';

export function getStartTaskConditions(field: any): ICondition[] {
  return [
    {
      order: 1,
      apiName: createConditionApiName(),
      rules: [getBaseStartRule(field)],
      action: EConditionAction.StartTask,
    },
  ];
}
