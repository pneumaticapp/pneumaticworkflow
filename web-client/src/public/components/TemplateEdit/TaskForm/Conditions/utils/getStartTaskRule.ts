import { createConditionRuleApiName, createConditionPredicateApiName } from '../../../../../utils/createId';
import { EConditionLogicOperations, EConditionOperators, TConditionRule } from '../types';
import { EStartingType } from './getDropdownOperators';

export function getBaseStartRule(field: any): TConditionRule {
  return {
    predicateApiName: createConditionPredicateApiName(),
    ruleApiName: createConditionRuleApiName(),
    logicOperation: EConditionLogicOperations.And,
    field,
    fieldType: EStartingType.Task,
    operator: EConditionOperators.Completed,
    value: null
  } as TConditionRule;
}
