/* eslint-disable */
/* prettier-ignore */
import { ContentState, convertToRaw } from 'draft-js';
import { draftToMarkdown } from 'markdown-draft-js';
// @ts-ignore
import { CHECKABLE_LIST_ITEM } from 'draft-js-checkable-list-item';

import { TMentionData } from '../..';
import { ECustomEditorEntities, TEditorAttachment } from '../types';
import { TChecklistItemData } from '../checklistsPlugin/types';

export function convertDraftToText(contentState: ContentState): string {
  const rawObject = convertToRaw(contentState);

  const markdown = draftToMarkdown(rawObject, {
    preserveNewlines: true,
    styleItems: {
      ITALIC: {
        open: () => '*',
        close: () => '*',
      },
      [CHECKABLE_LIST_ITEM]: {
        open: (entity?: any) => {
          const { listApiName, itemApiName } = entity.data as TChecklistItemData;

          return `[clist:${listApiName}|${itemApiName}]`;
        },
        close: () => `[/clist]`,
      },
    },
    entityItems: {
      [ECustomEditorEntities.Mention]: {
        open: () => '[',
        // tslint:disable-next-line: no-any
        close: (entity?: any) => `|${(entity.data.mention as TMentionData).id}]`,
      },
      [ECustomEditorEntities.Variable]: {
        // tslint:disable-next-line: no-any
        open: (entity?: any) => `{{${entity.data.apiName}}}[variable_name:`,
        close: () => ']',
      },
      CODE: {
        open: () => '',
        close: () => '',
      },
      [ECustomEditorEntities.Image]: {
        open: () => '',
        close: ({ data }: { data: TEditorAttachment }) => createAttachmentMarkdown({
          data,
          isImage: true,
          entityType: ECustomEditorEntities.Image,
        }),
      },
      [ECustomEditorEntities.Video]: {
        open: () => '',
        close: ({ data }: { data: TEditorAttachment }) => createAttachmentMarkdown({
          data,
          entityType: ECustomEditorEntities.Video,
        }),
      },
      [ECustomEditorEntities.File]: {
        open: () => '',
        close: ({ data }: { data: TEditorAttachment }) => createAttachmentMarkdown({
          data,
          entityType: ECustomEditorEntities.File,
        }),
      },
    },
  });

  const fixVariablesRegex = /(\{\{\s?([а-яa-z0-9\-_]+)\s?\}\})(\[variable_name:[^\n^\]]+\])/gi;
  const fixMentionsRegex = /\[@([^\n\|]+)\|([0-9]+)\]/gi;
  const emptyCheckItemsRegex = /\n\[clist:([\w-]+)\|([\w-]+)\]\[\/clist]/g;

  const result = markdown
    .replace(fixVariablesRegex, (match, variable) => variable)
    .replace(fixMentionsRegex, (match, userName, userId) => `[${userName}|${userId}]`)
    .replace(emptyCheckItemsRegex, '');

  return result;
}

type TCrateAttachmentMarkdown = {
  data: TEditorAttachment;
  isImage?: boolean;
  entityType: ECustomEditorEntities.File | ECustomEditorEntities.Image | ECustomEditorEntities.Video;
};
const createAttachmentMarkdown = ({ data, isImage, entityType }: TCrateAttachmentMarkdown) => {
  const {name, url, id } = data;
  const attachmentId = id ? `attachment_id:${id} ` : '';
  const markdown = `${isImage ? '!' : ''}[${name || url}](${url} "${attachmentId}entityType:${entityType}")`;

  return markdown;
};
