import { IExtraField } from '../../../../types/template';
import { IFieldsetRuleSet } from '../../../../types/fieldset';

export type TRulesetsParams = {
  rulesets: IFieldsetRuleSet[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
};

export type TRulesetParams = TRulesetsParams & {
  rulesetApiName: string;
};

export type TFieldsetRulesetsListProps = {
  rulesets: IFieldsetRuleSet[];
  fields: IExtraField[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
  isReadOnly?: boolean;
};

export type TFieldsetRulesetItemProps = {
  ruleSet: IFieldsetRuleSet;
  rulesets: IFieldsetRuleSet[];
  fields: IExtraField[];
  numericFields: IExtraField[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
  isReadOnly?: boolean;
};
