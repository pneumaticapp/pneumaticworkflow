import { IExtraField } from '../../../../types/template';

export interface IExtraFieldFileTemplateProps {
  field: IExtraField;
  isDisabled: boolean;
  namePlaceholder: string;
  editField(changedProps: Partial<IExtraField>): void;
}
