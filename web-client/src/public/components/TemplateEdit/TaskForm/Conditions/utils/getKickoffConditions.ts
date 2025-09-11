import { createConditionApiName } from '../../../../../utils/createId';
import { EConditionAction, ICondition } from '../types';
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
