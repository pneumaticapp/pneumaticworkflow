import { EExtraFieldType, IExtraField, TExtraFieldValue } from '../../../types/template';
import { parseMarkdownLinks } from '../../../utils/parseMarkdownFiles';

function normalizeEmptyValue(value: TExtraFieldValue | undefined): TExtraFieldValue {
  if (value == null || value === '' || (Array.isArray(value) && value.length === 0)) {
    return null;
  }

  return value;
}

type TCanonicalAttachment = {
  name: string;
  url: string;
};

// The same file set may arrive as markdown links, as an attachment list, or in any order.
function getCanonicalAttachments(field: IExtraField): TCanonicalAttachment[] {
  const fromField = (field.attachments ?? [])
    .filter(({ isRemoved }) => !isRemoved)
    .map(({ name, url }) => ({ name, url }));
  const byUrl = new Map<string, TCanonicalAttachment>();

  [...fromField, ...parseMarkdownLinks(field.markdownValue)].forEach((file) => {
    if (!byUrl.has(file.url)) {
      byUrl.set(file.url, file);
    }
  });

  return [...byUrl.values()].sort((firstFile, secondFile) => firstFile.url.localeCompare(secondFile.url));
}

export function getTaskOutputFingerprint(output: IExtraField[]): string {
  return JSON.stringify(
    output
      .map((field) => {
        const { apiName, value, userId, groupId, markdownValue, attachments, type } = field;
        const normalized = {
          apiName,
          value: normalizeEmptyValue(value),
          userId,
          groupId,
        };

        if (type === EExtraFieldType.File) {
          return { ...normalized, markdownValue: '', attachments: getCanonicalAttachments(field) };
        }

        return {
          ...normalized,
          markdownValue: markdownValue || '',
          attachments: (attachments ?? []).map(({ name, url, isRemoved }) => ({
            name,
            url,
            isRemoved: Boolean(isRemoved),
          })),
        };
      })
      .sort((firstField, secondField) => firstField.apiName.localeCompare(secondField.apiName)),
  );
}
