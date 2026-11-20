import { createConditionRuleApiName, createConditionPredicateApiName } from '../../../../../utils/createId';
import { EConditionLogicOperations } from '../../../../../types/templateTaskConditions';
import type { TConditionRule } from '../../../../../types/templateTaskConditions';

export function getEmptyRule(): TConditionRule {
  return {
    predicateApiName: createConditionPredicateApiName(),
    ruleApiName: createConditionRuleApiName(),
    logicOperation: EConditionLogicOperations.And,
    field: '',
    operator: null,
  } as TConditionRule;
}
