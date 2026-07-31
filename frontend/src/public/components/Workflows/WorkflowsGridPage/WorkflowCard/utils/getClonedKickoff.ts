/* eslint-disable */
/* prettier-ignore */
import {
  EExtraFieldType,
  IExtraField,
  IKickoffClient,
  TExtraFieldValue,
  IFieldsetBindingClient,
} from '../../../../../types/template';
import { IWorkflowDetailsKickoff } from '../../../../../types/workflow';
import { getEditKickoff } from '../../../../../utils/workflows';
import { normalizeSelections } from '../../../../TemplateEdit/utils/normalizeSelections';
import { normalizeCheckboxValue } from '../../../../../utils/fields';
import { IFieldsetField } from '../../../../../types/fieldset';

function normalizeKickoffFields(
  fields: (IExtraField | IFieldsetField)[] = [],
  templateKickoffFields: (IExtraField | IFieldsetField)[] = [],
): IExtraField[] {
  return fields
    .map((field) => {
      const templateField = templateKickoffFields.find((templateField) => templateField.apiName === field.apiName);
      if (!templateField) {
        return null;
      }

      return cloneFieldSelections(field as IExtraField, templateField as IExtraField);
    })
    .filter(Boolean) as IExtraField[];
}

export function getClonedKickoff(
  workflowKickoff: IWorkflowDetailsKickoff,
  templateKickoff: IKickoffClient,
): IKickoffClient {
  const kickoff = getEditKickoff(workflowKickoff);
  const finalFields = normalizeKickoffFields(kickoff.fields, templateKickoff.fields);

  const finalFieldsets = (kickoff.fieldsets || [])
    .map((fieldset) => {
      // TODO (Technical Debt): Backend workflow fieldsets contain raw properties (id, apiName),
      // while client-side template fieldsets expect apiNameBinding.
      // We fall back to fieldset.apiName to safely match template fieldsets.
      const fieldsetApiName = fieldset.apiNameBinding || (fieldset as any).apiName;

      const templateFieldset = (templateKickoff.fieldsets || []).find(
        (fieldsetFromTemplate) => fieldsetFromTemplate.apiNameBinding === fieldsetApiName,
      );

      if (!templateFieldset) {
        return null;
      }

      return {
        ...fieldset,
        fields: normalizeKickoffFields(fieldset.fields, templateFieldset.fields),
      };
    })
    .filter(Boolean);

  // TODO (Technical Debt): IKickoffClient.fieldsets is typed as IFieldsetBindingClient[] (template editor shape),
  // but runtime workflow execution components expect IFieldsetRuntime[] (with IExtraField[]).
  // Cast is required until IKickoffClient type is separated/narrowed between editor and runtime contexts.
  return {
    ...kickoff,
    fields: finalFields,
    fieldsets: finalFieldsets as unknown as IFieldsetBindingClient[],
  };
}

function cloneFieldSelections(field: IExtraField, templateField: IExtraField): IExtraField {
  if (!templateField.selections?.length) {
    return field;
  }
  const templateValues = normalizeSelections(templateField.selections);
  let normalizedValue = field.value;

  if (normalizedValue) {
    const parts = normalizeCheckboxValue(normalizedValue);
    const filtered = parts.filter((value) => templateValues.includes(value));

    if (field.type === EExtraFieldType.Checkbox) {
      normalizedValue = filtered as TExtraFieldValue;
    } else {
      normalizedValue = filtered.length > 0 ? filtered[0] : null;
    }
  }

  return { ...field, selections: templateValues, value: normalizedValue };
}
