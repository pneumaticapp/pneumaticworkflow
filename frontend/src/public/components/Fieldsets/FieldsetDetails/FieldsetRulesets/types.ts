import { IExtraField } from '../../../../types/template';
import { IFieldsetRuleSet } from '../../../../types/fieldset';

export type TRulePath = {
  rulesetApiName: string;
  ruleGroupOrApiName: string;
  ruleGroupAndApiName: string;
};

export type TFieldsetRulesetsProps = {
  rulesets: IFieldsetRuleSet[];
  fields: IExtraField[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
};
