/* prettier-ignore */
import { EConditionLogicOperations } from '../../types/templateTaskConditions';
import type {
  ICondition,
  IConditionAPI,
  IConditionRuleAPI,
  TConditionRule,
  TConditionRulePredicateAPI,
} from '../../types/templateTaskConditions';
import { flatten } from '../helpers';

export const normalizeConditiosForFrontend = (conditions: IConditionAPI[]): ICondition[] => {
  const getConditionRule = (
    rule: IConditionRuleAPI,
    predicate: TConditionRulePredicateAPI,
    logicOperation: TConditionRule['logicOperation'],
  ): TConditionRule => {
    return {
      ruleId: rule.id,
      ruleApiName: rule.apiName,
      predicateId: predicate.id,
      predicateApiName: predicate.apiName,
      logicOperation,
      field: predicate.field,
      operator: predicate.operator,
      value: predicate.value,
      fieldType: predicate.fieldType,
    } as TConditionRule;
  };

  const getNormalizedCondition = (condition: IConditionAPI): ICondition => {
    const normalizedRules = condition.rules.map((rule, ruleIndex) => {
      const { predicates } = rule;

      return predicates.map((predicate, predicateIndex) => {
        if (predicateIndex === 0 && ruleIndex === 0) {
          return getConditionRule(rule, predicate, EConditionLogicOperations.And);
        }

        if (predicateIndex === 0) {
          return getConditionRule(rule, predicate, EConditionLogicOperations.Or);
        }

        return getConditionRule(rule, predicate, EConditionLogicOperations.And);
      });
    });

    return {
      id: condition.id,
      apiName: condition.apiName,
      order: condition.order,
      rules: flatten(normalizedRules),
      action: condition.action,
    };
  };

  return conditions.map(getNormalizedCondition);
};
