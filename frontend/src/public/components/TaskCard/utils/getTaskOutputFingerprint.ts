import { IExtraField } from '../../../types/template';

export function getTaskOutputFingerprint(output: IExtraField[]): string {
  return JSON.stringify(
    output
      .map(({ apiName, value, userId, groupId, markdownValue, attachments }) => ({
        apiName,
        value,
        userId,
        groupId,
        markdownValue,
        attachments: attachments?.map(({ name, url, isRemoved }) => ({
          name,
          url,
          isRemoved,
        })),
      }))
      .sort((firstField, secondField) => firstField.apiName.localeCompare(secondField.apiName)),
  );
}
