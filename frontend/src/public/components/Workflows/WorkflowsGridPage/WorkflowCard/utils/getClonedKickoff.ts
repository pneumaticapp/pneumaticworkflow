/* eslint-disable */
/* prettier-ignore */
import {
  EExtraFieldType,
  IExtraField,
  IKickoffClient,
  TExtraFieldValue,
} from '../../../../../types/template';
import { IWorkflowDetailsKickoff } from '../../../../../types/workflow';
import { getEditKickoff } from '../../../../../utils/workflows';
import { normalizeSelections } from '../../../../TemplateEdit/utils/normalizeSelections';

export function getClonedKickoff(
  workflowKickoff: IWorkflowDetailsKickoff,
  templateKickoff: IKickoffClient,
): IKickoffClient {
  const kickoff = getEditKickoff(workflowKickoff);
  const normalizedKickoffFields = kickoff.fields
    .map((field) => {
      const templateField = templateKickoff.fields.find((templateField) => templateField.apiName === field.apiName);
      if (!templateField) {
        return null;
      }

      return cloneFieldSelections(field, templateField);
    })
    .filter(Boolean) as IExtraField[];

  const finalFields = normalizedKickoffFields.map((field) => {
    if (field.type !== EExtraFieldType.Checkbox) {
      return field;
    }

    if (Array.isArray(field.value)) {
      return field;
    }

    const arrayValue = typeof field.value === 'string' && field.value !== '' ? field.value.split(', ') : [];

    return { ...field, value: arrayValue as TExtraFieldValue };
  });

  return { ...kickoff, fields: finalFields };
}

function cloneFieldSelections(field: IExtraField, templateField: IExtraField): IExtraField {
  if (!templateField.selections?.length) {
    return field;
  }
  const templateValues = normalizeSelections(templateField.selections);
  let normalizedValue = field.value;

  if (normalizedValue) {
    const parts = Array.isArray(normalizedValue) ? normalizedValue : (normalizedValue as string).split(', ');
    const filtered = parts.filter((value) => templateValues.includes(value));

    if (field.type === EExtraFieldType.Checkbox) {
      normalizedValue = filtered as TExtraFieldValue;
    } else {
      normalizedValue = filtered.length > 0 ? filtered[0] : null;
    }
  }

  return { ...field, selections: templateValues, value: normalizedValue };
}
