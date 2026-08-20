import { IExtraField, TExtraFieldValue } from '../../../types/template';

function normalizeEmptyValue(value: TExtraFieldValue | undefined): TExtraFieldValue {
  if (value == null || value === '' || (Array.isArray(value) && value.length === 0)) {
    return null;
  }

  return value;
}

export function getTaskOutputFingerprint(output: IExtraField[]): string {
  return JSON.stringify(
    output
      .map(({ apiName, value, userId, groupId, markdownValue, attachments }) => ({
        apiName,
        value: normalizeEmptyValue(value),
        userId,
        groupId,
        markdownValue: markdownValue || '',
        attachments: (attachments ?? []).map(({ name, url, isRemoved }) => ({
          name,
          url,
          isRemoved: Boolean(isRemoved),
        })),
      }))
      .sort((firstField, secondField) => firstField.apiName.localeCompare(secondField.apiName)),
  );
}
