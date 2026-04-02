import { EExtraFieldType } from '../../../../../types/template';
import { TTaskVariable } from '../../../types';

export function shouldLoadDatasetForVariable(variable: TTaskVariable): boolean {
  const isFieldWithOptions = [
    EExtraFieldType.Checkbox,
    EExtraFieldType.Radio,
    EExtraFieldType.Creatable,
  ].includes(variable.type as EExtraFieldType);
  
  const hasDatasetId = Boolean(variable.datasetId);

  return isFieldWithOptions && hasDatasetId;
}
