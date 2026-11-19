import type { EFieldLabelPosition } from '../../../../types/fieldset';
import type { IExtraField } from '../../../../types/template';

export interface IExtraFieldFileTemplateProps {
  field: IExtraField;
  isDisabled: boolean;
  namePlaceholder: string;
  labelPosition?: EFieldLabelPosition;
  editField(changedProps: Partial<IExtraField>): void;
}
