/* eslint-disable */
/* prettier-ignore */
import { EConditionLogicOperations, TConditionRule } from '..';
import { createConditionRuleApiName } from '../../../../../utils/createId';

export const setRulesApiNamesAndIds = (rules: TConditionRule[]) => {
  let ruleApiName = '';
  let ruleId: number | undefined;

  return rules.map((rule, ruleIndex) => {
    if (ruleIndex === 0 || rule.logicOperation === EConditionLogicOperations.Or) {
      ruleApiName = ruleApiName !== rule.ruleApiName ? rule.ruleApiName : createConditionRuleApiName();
      ruleId = ruleId !== rule.ruleId ? rule.ruleId : undefined;
    }

    return { ...rule, ruleApiName, ruleId };
  });
};
