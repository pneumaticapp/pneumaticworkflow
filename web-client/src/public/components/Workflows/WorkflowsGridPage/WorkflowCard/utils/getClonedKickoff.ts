/* eslint-disable */
/* prettier-ignore */
import { copyAttachment } from '../../../../../api/copyAttachment';
import { IExtraField, IExtraFieldSelection, IKickoff, TExtraFieldValue } from '../../../../../types/template';
import { IWorkflowDetailsKickoff } from '../../../../../types/workflow';
import { TUploadedFile } from '../../../../../utils/uploadFiles';
import { getEditKickoff } from '../../../../../utils/workflows';

export async function getClonedKickoff(
  workflowKickoff: IWorkflowDetailsKickoff,
  templateKickoff: IKickoff,
): Promise<IKickoff> {
  const kickoff = getEditKickoff(workflowKickoff);
  const normalizedKickoffFieldsPromises = kickoff.fields.map(field => {
    const templateField = templateKickoff.fields.find(templateField => templateField.apiName === field.apiName);
    if (!templateField) {
      return null;
    }

    return cloneAttachments(cloneFieldSelections(field, templateField));
  });
  const normalizedKickoffFields = await Promise
    .all(normalizedKickoffFieldsPromises)
    .then(fields => fields.filter(Boolean)) as IExtraField[];

  return { ...kickoff, fields: normalizedKickoffFields };
}

function cloneFieldSelections(field: IExtraField, templateField: IExtraField): IExtraField {
  if (!field.selections) {
    return field;
  }

  const selectionIdMap = new Map(field.selections.map(selection => {
    const templateSelection = templateField.selections
      ?.find(templateSelection => templateSelection.apiName === selection.apiName);

    return templateSelection ? [selection.id as number, templateSelection.id as number] as const : null;
  }).filter(Boolean) as (readonly [number, number])[]);

  const normalizedSelections = field.selections.map(selection => {
    const newId = selectionIdMap.get(selection.id as number);

    return newId ? { ...selection, id: newId } : null;
  }).filter(Boolean) as IExtraFieldSelection[];

  const normalizedValue = Array.isArray(field.value) ? (field.value.map(selectedId => {
    const newValue = selectionIdMap.get(Number(selectedId));

    return newValue ? String(newValue) : null;
  }).filter(Boolean) as TExtraFieldValue) : field.value;

  return { ...field, selections: normalizedSelections, value: normalizedValue };
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

  const normalizedAttachments = field.attachments.map(attachment => {
    return { ...attachment, id: attachmentsMap.get(attachment.id) } as TUploadedFile;
  }) as TUploadedFile[];

  const normalizedValue = Array.isArray(field.value) ? (field.value.map(fileId => {
    const newValue = attachmentsMap.get(Number(fileId));

    return newValue ? String(newValue) : null;
  }).filter(Boolean) as TExtraFieldValue) : field.value;

  return { ...field, attachments: normalizedAttachments, value: normalizedValue };
}
