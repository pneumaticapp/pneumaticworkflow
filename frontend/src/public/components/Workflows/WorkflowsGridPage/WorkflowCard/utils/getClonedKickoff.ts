/* eslint-disable */
/* prettier-ignore */
import { copyAttachment } from '../../../../../api/copyAttachment';
import { EExtraFieldType, IExtraField, IKickoff, TExtraFieldValue } from '../../../../../types/template';
import { IWorkflowDetailsKickoff } from '../../../../../types/workflow';
import { TUploadedFile } from '../../../../../utils/uploadFiles';
import { getEditKickoff } from '../../../../../utils/workflows';
import { normalizeSelections } from '../../../../TemplateEdit/utils/getRunnableWorkflow';

export async function getClonedKickoff(
  workflowKickoff: IWorkflowDetailsKickoff,
  templateKickoff: IKickoff,
): Promise<IKickoff> {
  const kickoff = getEditKickoff(workflowKickoff);
  const normalizedKickoffFieldsPromises = kickoff.fields.map((field) => {
    const templateField = templateKickoff.fields.find((templateField) => templateField.apiName === field.apiName);
    if (!templateField) {
      return null;
    }

    return cloneAttachments(cloneFieldSelections(field, templateField));
  });
  const normalizedKickoffFields = (await Promise.all(normalizedKickoffFieldsPromises).then((fields) =>
    fields.filter(Boolean),
  )) as IExtraField[];

  const finalFields = normalizedKickoffFields.map((field) => {
    if (field.type !== EExtraFieldType.Checkbox) {
      return field;
    }

    if (Array.isArray(field.value)) {
      return field;
    }

    const arrayValue = typeof field.value === 'string' && field.value !== ''
      ? field.value.split(', ')
      : [];

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
    const parts = Array.isArray(normalizedValue)
      ? normalizedValue
      : (normalizedValue as string).split(', ');
    const filtered = parts.filter((value) => templateValues.includes(value));

    if (field.type === EExtraFieldType.Checkbox) {
      normalizedValue = filtered as TExtraFieldValue;
    } else {
      normalizedValue = filtered.length > 0 ? filtered[0] : null;
    }
  }

  return { ...field, selections: templateValues, value: normalizedValue };
}

async function cloneAttachments(field: IExtraField): Promise<IExtraField> {
  if (!field.attachments) {
    return field;
  }

  const attachmentsMap = new Map();
  for (const attachment of field.attachments) {
    const newAttachment = await copyAttachment(attachment.id);
    attachmentsMap.set(attachment.id, newAttachment?.id);
  }

  const normalizedAttachments = field.attachments.map((attachment) => {
    return { ...attachment, id: attachmentsMap.get(attachment.id) } as TUploadedFile;
  }) as TUploadedFile[];

  const normalizedValue = (field.type === EExtraFieldType.File && Array.isArray(field.value))
    ? (field.value
        .map((fileId) => {
          const newValue = attachmentsMap.get(Number(fileId));

          return newValue ? String(newValue) : null;
        })
        .filter(Boolean) as TExtraFieldValue)
    : field.value;

  return { ...field, attachments: normalizedAttachments, value: normalizedValue };
}
