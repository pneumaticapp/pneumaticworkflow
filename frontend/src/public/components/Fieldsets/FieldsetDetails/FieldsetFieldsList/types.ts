import { IExtraField } from '../../../../types/template';
import { EFieldLabelPosition } from '../../../../types/fieldset';

export interface IFieldsetFieldsListProps {
  fields: IExtraField[];
  onFieldsChange: (fields: IExtraField[]) => void;
  isReadOnly: boolean;
  labelPosition: EFieldLabelPosition;
  accountId: number;
  datasetOptions: { label: string; value: string }[];
}
