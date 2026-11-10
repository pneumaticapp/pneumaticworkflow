import { createConditionApiName } from '../../../../../utils/createId';
import { EConditionAction } from '../../../../../types/templateTaskConditions';
import type { ICondition } from '../../../../../types/templateTaskConditions';
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
