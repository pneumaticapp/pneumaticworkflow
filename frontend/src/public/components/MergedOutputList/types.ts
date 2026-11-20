import type { IExtraField } from '../../types/template';
import type { IFieldsetRuntime } from '../../types/fieldset';
import type { EInputNameBackgroundColor } from '../../types/workflow';

export interface IMergedOutputListProps {
  fields: IExtraField[];
  fieldsets?: IFieldsetRuntime[];
  onEditField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  onEditFieldsetField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  labelBackgroundColor: EInputNameBackgroundColor;
  fieldClassName?: string;
  accountId: number;
  isDisabled?: boolean;
  onUploadStateChange?(apiName: string, isUploading: boolean): void;
}
