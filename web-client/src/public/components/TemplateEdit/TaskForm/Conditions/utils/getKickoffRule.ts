import { createConditionRuleApiName, createConditionPredicateApiName } from '../../../../../utils/createId';
import { EConditionLogicOperations, EConditionOperators, TConditionRule } from '../types';
import { EStartingType } from './getDropdownOperators';

export function getKickoffRule(): TConditionRule {
  return {
    predicateApiName: createConditionPredicateApiName(),
    ruleApiName: createConditionRuleApiName(),
    logicOperation: EConditionLogicOperations.And,
    field: null,
    fieldType: EStartingType.Kickoff,
    operator: EConditionOperators.Completed,
    value: null
  } as TConditionRule;
}
