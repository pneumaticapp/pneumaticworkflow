import { IExtraField } from '../../../../types/template';
import { EFieldLabelPosition, IFieldRuleSet, IFieldsetRuleSet } from '../../../../types/fieldset';

export interface IFieldsetFieldsListProps {
  fields: IExtraField[];
  onFieldsChange: (fields: IExtraField[]) => void;
  isReadOnly: boolean;
  labelPosition: EFieldLabelPosition;
  accountId: number;
  datasetOptions: { label: string; value: string }[];
  rulesets: IFieldsetRuleSet[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
  onOpenFieldRule?: (fieldApiName: string, ruleset?: IFieldRuleSet) => void;
  onDeleteFieldRuleset?: (fieldApiName: string, rulesetApiName: string) => void;
}
