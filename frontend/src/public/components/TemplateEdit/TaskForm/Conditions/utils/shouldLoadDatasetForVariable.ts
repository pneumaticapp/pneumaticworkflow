import type { TTaskVariable } from '../../../../../types/template';
import { EExtraFieldType } from '../../../../../types/template';

export function shouldLoadDatasetForVariable(variable: TTaskVariable): boolean {
  const isFieldWithOptions = [EExtraFieldType.Checkbox, EExtraFieldType.Radio, EExtraFieldType.Creatable].includes(
    variable.type as EExtraFieldType,
  );

  const hasDatasetId = Boolean(variable.datasetId);

  return isFieldWithOptions && hasDatasetId;
}
