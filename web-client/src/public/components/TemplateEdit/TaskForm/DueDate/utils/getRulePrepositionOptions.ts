import { TDueDateRulePreposition, TDueDateRuleTarget } from "../../../../../types/template";
import { TDropdownOptionBase } from "../../../../UI";

export type TRulePrepositionOption = TDropdownOptionBase & {
  rulePreposition: TDueDateRulePreposition;
};


export const getRulePrepositionOptions = (ruleTarget: TDueDateRuleTarget | null): TRulePrepositionOption[] => {
  const beforePreposition: TRulePrepositionOption = {
    label: 'before',
    rulePreposition: 'before',
  };
  const afterPreposition: TRulePrepositionOption = {
    label: 'after',
    rulePreposition: 'after',
  };

  if (!ruleTarget || ruleTarget === 'field') {
    return [beforePreposition, afterPreposition];
  }

  return [afterPreposition];
} 
