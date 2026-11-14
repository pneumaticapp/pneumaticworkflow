import { EConditionLogicOperations } from '../../types/templateTaskConditions';
import type {
  EConditionOperators,
  ICondition,
  IConditionAPI,
  IConditionRuleAPI,
  TConditionRulePredicateAPI,
} from '../../types/templateTaskConditions';
import { getFilledConditions } from '../../components/TemplateEdit/TaskForm/Conditions/utils/conditionsValidators';
import { isArrayWithItems } from '../helpers';

export const normalizeConditionForBackend = (conditions: ICondition[]): IConditionAPI[] => {
  const normalizeCondition = (condition: ICondition, index: number): IConditionAPI | null => {
    if (!isArrayWithItems(condition.rules)) {
      return null;
    }

    const normalizedRules: IConditionRuleAPI[] = condition.rules.reduce((acc, item) => {
      const newPredicate = {
        id: item.predicateId,
        apiName: item.predicateApiName,
        field: item.field,
        operator: item.operator as EConditionOperators,
        fieldType: item.fieldType,
        value: item.fieldType === 'number' && item?.value ? String(item.value).replace(',', '.') : item.value,
      } as TConditionRulePredicateAPI;

      const [lastRule] = acc.slice(-1);

      if (item.logicOperation === EConditionLogicOperations.Or || !lastRule) {
        const newRule = {
          id: item.ruleId,
          apiName: item.ruleApiName,
          predicates: [newPredicate],
        } as IConditionRuleAPI;

        return [...acc, newRule];
      }

      const newLastRule = {
        ...lastRule,
        predicates: [...lastRule.predicates, newPredicate],
      } as IConditionRuleAPI;

      return [...acc.slice(0, -1), newLastRule];
    }, [] as IConditionRuleAPI[]);

    return {
      id: condition.id,
      apiName: condition.apiName,
      order: index + 1,
      rules: normalizedRules,
      action: condition.action,
    };
  };

  return getFilledConditions(conditions).map(normalizeCondition).filter(Boolean) as IConditionAPI[];
};
