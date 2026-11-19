import { createConditionApiName } from '../../../../../utils/createId';
import { EConditionAction } from '../../../../../types/templateTaskConditions';
import type { ICondition } from '../../../../../types/templateTaskConditions';
import { getKickoffRule } from './getKickoffRule';

export function getKickoffConditions(): ICondition[] {
  return [
    {
      order: 1,
      apiName: createConditionApiName(),
      rules: [getKickoffRule()],
      action: EConditionAction.StartTask,
    },
  ];
}
