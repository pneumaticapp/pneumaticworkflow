/* eslint-disable */
/* prettier-ignore */
import { EConditionLogicOperations, ICondition, TConditionRule } from '../../components/TemplateEdit/TaskForm/Conditions';
import { IConditionResponse, IConditionRuleResponse, TConditionRulePredicateResponse } from '../../types/template';
import { flatten } from '../helpers';

export const normalizeConditiosForFrontend = (conditions: IConditionResponse[]): ICondition[] => {
  const getConditionRule = (
    rule: IConditionRuleResponse,
    predicate: TConditionRulePredicateResponse,
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

  const getNormalizedCondition = (condition: IConditionResponse): ICondition => {
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
