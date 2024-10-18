/* eslint-disable */
/* prettier-ignore */
import { createConditionRuleApiName, createConditionPredicateApiName } from '../../../../../utils/createId';
import { EConditionLogicOperations, TConditionRule } from '../types';

export function getEmptyRule(): TConditionRule {
  return {
    predicateApiName: createConditionPredicateApiName(),
    ruleApiName: createConditionRuleApiName(),
    logicOperation: EConditionLogicOperations.And,
    field: '',
    operator: null,
  } as TConditionRule;
}
