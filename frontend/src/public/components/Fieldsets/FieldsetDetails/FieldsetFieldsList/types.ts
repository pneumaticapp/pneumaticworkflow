import { IExtraField } from '../../../../types/template';
import { EFieldLabelPosition, IFieldRuleSet } from '../../../../types/fieldset';

export interface IFieldsetFieldsListProps {
  fields: IExtraField[];
  onFieldsChange: (fields: IExtraField[]) => void;
  isReadOnly: boolean;
  labelPosition: EFieldLabelPosition;
  accountId: number;
  datasetOptions: { label: string; value: string }[];
  onOpenFieldRule?: (fieldApiName: string, ruleset?: IFieldRuleSet) => void;
}
