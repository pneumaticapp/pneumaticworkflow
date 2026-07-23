import { EFieldLabelPosition } from '../../../../types/fieldset';
import { IExtraField } from '../../../../types/template';

export interface IExtraFieldFileTemplateProps {
  field: IExtraField;
  isDisabled: boolean;
  namePlaceholder: string;
  labelPosition?: EFieldLabelPosition;
  editField(changedProps: Partial<IExtraField>): void;
}
