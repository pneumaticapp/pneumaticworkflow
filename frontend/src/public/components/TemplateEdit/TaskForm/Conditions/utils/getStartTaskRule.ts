import { createConditionRuleApiName, createConditionPredicateApiName } from '../../../../../utils/createId';
import { EConditionLogicOperations, EConditionOperators } from '../../../../../types/templateTaskConditions';
import type { TConditionRule } from '../../../../../types/templateTaskConditions';
import { EStartingType } from '../../../../../types/template';

export function getBaseStartRule(field: any): TConditionRule {
  return {
    predicateApiName: createConditionPredicateApiName(),
    ruleApiName: createConditionRuleApiName(),
    logicOperation: EConditionLogicOperations.And,
    field,
    fieldType: EStartingType.Task,
    operator: EConditionOperators.Completed,
    value: null,
  } as TConditionRule;
}
