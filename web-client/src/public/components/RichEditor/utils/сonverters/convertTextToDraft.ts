/* eslint-disable */
/* prettier-ignore */
import { markdownToDraft } from 'markdown-draft-js';
import { convertFromRaw, EditorState } from 'draft-js';
// @ts-ignore
import { CHECKABLE_LIST_ITEM } from 'draft-js-checkable-list-item';

import { REMARKABLE_DISIBLE_MARKDOWN_OPTIONS } from '../../../../constants/defaultValues';
import { TTaskVariable } from '../../../TemplateEdit/types';
import { prepareChecklistsForRendering } from '../../../../utils/checklists/prepareChecklistsForRendering';
import { normalizeDraftRaw } from './normalizeDraftRaw';
import { isArrayWithItems } from '../../../../utils/helpers';
import { ECustomEditorEntities, TEditorAttachment } from '../types';
import {
  linksRemarkablePlugin,
  createVariableRemarkablePlugin,
  mentionRemarkablePlugin,
  TCustomLinkToken,
  TMentionToken,
  TVariableToken,
  checklistsRemarkablePlugin,
} from './customMarkdownPlugins';

export const getInitialEditorState = (text: string = '', variables: TTaskVariable[] = [], isMarkdownEnabled = true) => {
  const rawDraftJSObject = convertTextToDraft(text, variables, isMarkdownEnabled);
  const normalizedRaw = normalizeDraftRaw(rawDraftJSObject);

  const editorContent = convertFromRaw(normalizedRaw);
  const editorState = EditorState.createWithContent(editorContent);

  return editorState;
};

export function convertTextToDraft(text: string, variables: TTaskVariable[], isMarkdownEnabled: boolean) {
  const defaultRemarkableOptions = {
    disable: {
      inline: ['links'],
      block: ['heading', 'code', 'hr'],
    },
  };

  const rawDraftJSObject = markdownToDraft(prepareChecklistsForRendering(text), {
    preserveNewlines: true,
    remarkablePlugins: [
      isArrayWithItems(variables) && createVariableRemarkablePlugin(variables),
      mentionRemarkablePlugin,
      linksRemarkablePlugin,
      checklistsRemarkablePlugin,
    ].filter(Boolean),
    remarkableOptions: isMarkdownEnabled ? defaultRemarkableOptions : REMARKABLE_DISIBLE_MARKDOWN_OPTIONS,
    blockTypes: {
      clist_open: (item: any) => {
        return {
          type: CHECKABLE_LIST_ITEM,
          text: item.value,
          data: {
            listApiName: item.listApiName,
            itemApiName: item.itemApiName,
          }
        };
      },
    },
    blockEntities: {
      variable_open: (item: TVariableToken) => {
        return {
          type: ECustomEditorEntities.Variable,
          mutability: 'IMMUTABLE',
          data: {
            title: item.title,
            subtitle: item.subtitle,
            apiName: item.apiName,
          },
        };
      },
      mention_open: (item: TMentionToken) => {
        return {
          type: ECustomEditorEntities.Mention,
          mutability: 'IMMUTABLE',
          data: {
            mention: {
              id: item.id,
              name: item.name,
            },
          },
        };
      },
      link_open: (item: TCustomLinkToken) => {
        return {
          type: item.entityType,
          mutability: item.entityType === ECustomEditorEntities.Link ? 'MUTABLE' : 'IMMUTABLE',
          data: {
            id: item.id,
            url: item.url,
            name: item.name,
          } as TEditorAttachment,
        };
      },
    },
  });

  return rawDraftJSObject;
}
