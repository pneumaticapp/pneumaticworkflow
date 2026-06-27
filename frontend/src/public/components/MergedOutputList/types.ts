import { IExtraField } from '../../types/template';
import { IFieldsetRuntime } from '../../types/fieldset';
import { EInputNameBackgroundColor } from '../../types/workflow';

export interface IMergedOutputListProps {
  fields: IExtraField[];
  fieldsets?: IFieldsetRuntime[];
  onEditField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  onEditFieldsetField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  labelBackgroundColor: EInputNameBackgroundColor;
  fieldClassName?: string;
  accountId: number;
}
