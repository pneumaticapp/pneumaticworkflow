import { IExtraField, IFieldsetData } from '../../types/template';
import { EInputNameBackgroundColor } from '../../types/workflow';

export interface IMergedOutputListProps {
  fields: IExtraField[];
  fieldsets?: IFieldsetData[];
  onEditField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  onEditFieldsetField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  labelBackgroundColor: EInputNameBackgroundColor;
  fieldClassName?: string;
  accountId: number;
}
