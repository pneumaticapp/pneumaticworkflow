import { IExtraField } from '../../../types/template';

export function getTaskOutputFingerprint(output: IExtraField[]): string {
  return JSON.stringify(
    output.map((field) => ({
      apiName: field.apiName,
      order: field.order,
      type: field.type,
      value: field.value,
      markdownValue: field.markdownValue,
      userId: field.userId,
      groupId: field.groupId,
      attachments: field.attachments?.map(({ id, name, url, isRemoved }) => ({
        id,
        name,
        url,
        isRemoved,
      })),
    })),
  );
}
