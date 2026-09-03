import { IExtraField } from '../../../../types/template';
import { IFieldsetRuleSet } from '../../../../types/fieldset';

export type TRulesetsParams = {
  rulesets: IFieldsetRuleSet[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
};

export type TRulesetParams = TRulesetsParams & {
  rulesetApiName: string;
};

export type TFieldsetRulesetsProps = {
  rulesets: IFieldsetRuleSet[];
  fields: IExtraField[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
  isReadOnly?: boolean;
};
