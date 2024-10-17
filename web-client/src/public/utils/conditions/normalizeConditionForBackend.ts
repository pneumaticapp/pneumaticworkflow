/* eslint-disable */
/* prettier-ignore */
import { EConditionLogicOperations, EConditionOperators, ICondition } from '../../components/TemplateEdit/TaskForm/Conditions';
import { getFilledConditions } from '../../components/TemplateEdit/TaskForm/Conditions/utils/conditionsValidators';
import { IConditionResponse, IConditionRuleResponse, TConditionRulePredicateResponse } from '../../types/template';
import { isArrayWithItems } from '../helpers';

export const normalizeConditionForBackend = (conditions: ICondition[]): IConditionResponse[] => {
  const normalizeCondition = (condition: ICondition, index: number): IConditionResponse | null => {
    if (!isArrayWithItems(condition.rules)) {
      return null;
    }

    const normalizedRules: IConditionRuleResponse[] = condition.rules.reduce((acc, item) => {
      const newPredicate = {
        id: item.predicateId,
        apiName: item.predicateApiName,
        field: item.field,
        operator: item.operator as EConditionOperators,
        fieldType: item.fieldType,
        value: item.value,
      } as TConditionRulePredicateResponse;

      const [lastRule] = acc.slice(-1);

      if (item.logicOperation === EConditionLogicOperations.Or || !lastRule) {
        const newRule = {
          id: item.ruleId,
          apiName: item.ruleApiName,
          predicates: [newPredicate],
        } as IConditionRuleResponse;

        return [...acc, newRule];
      }

      const newLastRule = {
        ...lastRule,
        predicates: [...lastRule.predicates, newPredicate],
      } as IConditionRuleResponse;

      return [...acc.slice(0, -1), newLastRule];
    }, [] as IConditionRuleResponse[]);

    return {
      id: condition.id,
      apiName: condition.apiName,
      order: index + 1,
      rules: normalizedRules,
      action: condition.action,
    };
  };

  return getFilledConditions(conditions)
    .map(normalizeCondition)
    .filter(Boolean) as IConditionResponse[];
};
