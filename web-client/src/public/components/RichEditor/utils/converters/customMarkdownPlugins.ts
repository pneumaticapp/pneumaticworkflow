/* eslint-disable */
/* prettier-ignore */
import { Remarkable } from 'remarkable';

import { mentionsRegex, variableRegex } from '../../../../constants/defaultValues';
import { TTaskVariable } from '../../../TemplateEdit/types';
import { TMentionData } from '../..';
import { ECustomEditorEntities } from '../types';
import { getAttachmentEntityType } from '../AttachmentsPlugin/modifiers/addAttachment';
import { ContentToken } from 'remarkable/lib';

export type TVariableToken = {
  title: string;
  subtitle: string;
  apiName: string;
} & Remarkable.ContentToken;

export type TMentionToken = TMentionData & Remarkable.ContentToken;

export type TCustomLinkToken = {
  id?: number;
  url: string;
  name: string;
  isLinkified: boolean;
  entityType: ECustomEditorEntities;
} & Remarkable.ContentToken;

export const createVariableRemarkablePlugin = (variables: TTaskVariable[]) => (remarkable: Remarkable) => {
  remarkable.inline.ruler.push(
    'variable',
    function variable(state: Remarkable.StateInline, silent: boolean) {
      // it is surely not our rule, so we could stop early
      if (!state.src || typeof state.pos !== 'number') {
        return false;
      }

      const regEx = new RegExp(`^${variableRegex.source}`, variableRegex.flags);
      const match = regEx.exec(state.src.slice(state.pos));
      if (!match) {
        return false;
      }

      const [matchString, variableApiName] = match;

      // valid match found, now we need to advance cursor
      state.pos += matchString.length;

      // don't insert any tokens in silent mode
      if (silent) {
        return true;
      }

      const variable = variables.find((variable) => variableApiName === variable.apiName);
      if (!variable) {
        return true;
      }

      state.push({
        type: 'variable_open',
        title: variable.title,
        subtitle: variable.richSubtitle || variable.subtitle,
        apiName: variableApiName,
        level: state.level,
      } as Remarkable.ContentToken);

      state.push({
        type: 'text',
        content: variable.title,
        level: state.level + 1,
      });

      state.push({
        type: 'variable_close',
        level: state.level,
      });

      return true;
    },
    {},
  );
};

export const mentionRemarkablePlugin = (remarkable: Remarkable) => {
  remarkable.inline.ruler.push(
    'mention',
    function mention(state: Remarkable.StateInline, silent: boolean) {
      // it is surely not our rule, so we could stop early
      if (!state.src || typeof state.pos !== 'number') {
        return false;
      }

      const regEx = new RegExp(`^${mentionsRegex.source}`, mentionsRegex.flags);
      const match = regEx.exec(state.src.slice(state.pos));
      if (!match) {
        return false;
      }

      const [matchString, userName, userId] = match;

      // valid match found, now we need to advance cursor
      state.pos += matchString.length;

      // don't insert any tokens in silent mode
      if (silent) {
        return true;
      }

      state.push({
        type: 'mention_open',
        id: userId,
        name: userName,
        level: state.level,
      } as Remarkable.ContentToken);

      state.push({
        type: 'text',
        content: `@${userName}`,
        level: state.level + 1,
      });

      state.push({
        type: 'mention_close',
        level: state.level,
      });

      return true;
    },
    {},
  );
};

export const linksRemarkablePlugin = (remarkable: Remarkable) => {
  remarkable.inline.ruler.push(
    'links',
    function links(state: Remarkable.StateInline, silent: boolean) {
      // it is surely not our rule, so we could stop early
      if (!state.src || typeof state.pos !== 'number') {
        return false;
      }

      const regEx =
        /^!?\[([^\]]*)\]\((.*?)\s*(?:"(?:attachment_id:(\d*))?(?:\s+)?(?:entityType:([^"\s]*))?(?:[^"]*)?")?\s*\)/;
      const match = regEx.exec(state.src.slice(state.pos));

      if (!match) {
        return false;
      }

      const [matchString, name, url, id, type] = match;

      // valid match found, now we need to advance cursor
      state.pos += matchString.length;

      // don't insert any tokens in silent mode
      if (silent) {
        return true;
      }

      const entityType = getLinkEntityType(url, type);

      const linkOpenToken: TCustomLinkToken = {
        type: 'link_open',
        id: id ? Number(id) : undefined,
        url,
        name,
        isLinkified: false,
        entityType,
        level: state.level,
      };

      state.push(linkOpenToken);

      state.push({
        type: 'text',
        content: entityType === ECustomEditorEntities.Link ? name : ' ',
        level: state.level + 1,
      });

      state.push({
        type: 'link_close',
        level: state.level,
        entityType,
      } as ContentToken);

      return true;
    },
    {},
  );
};

const getLinkEntityType = (url: string, entityType: string) => {
  const googleBucket = 'https://storage.googleapis.com/';

  const attachmentEntityTypes = [ECustomEditorEntities.Image, ECustomEditorEntities.File, ECustomEditorEntities.Video];

  if (entityType) {
    return attachmentEntityTypes.includes(entityType as ECustomEditorEntities)
      ? (entityType as ECustomEditorEntities)
      : getAttachmentEntityType(url);
  }

  // for legacy attachments with no entityType
  if (url.includes(googleBucket)) {
    return getAttachmentEntityType(url);
  }

  return ECustomEditorEntities.Link;
};

const getCheklistItemStartMatch = (line: string) => {
  const regEx = /^\[clist:([\w-]+)\|([\w-]+)\]/;

  return regEx.exec(line);
};

const getCheklistItemEndMatch = (line: string) => {
  const regEx = /\[\/clist\]/;

  return regEx.exec(line);
};

export const checklistsRemarkablePlugin = (remarkable: Remarkable) => {
  remarkable.block.ruler.before(
    'list',
    'checklist',
    function checklists(state, startLine, endLine, silent) {
      const getLineText = (line: number) => {
        return state.src.slice(state.bMarks[line], state.eMarks[line]);
      };

      const pos = state.bMarks[startLine] + state.tShift[startLine];
      const max = state.eMarks[startLine];

      if (pos >= max) {
        return false;
      }

      const match = getCheklistItemStartMatch(getLineText(startLine));
      if (!match) {
        return false;
      }

      const [, listApiName, itemApiName] = match;

      if (silent) {
        return true;
      }

      state.line = startLine + 1;
      const listLines: [number, number] = [startLine, state.line];
      state.tokens.push({
        type: 'clist_open',
        lines: listLines,
        level: state.level,
        // @ts-ignore
        listApiName,
        itemApiName,
      });

      // collecting checkbox label content
      let currentLine = startLine;
      let totalLabelContent = '';
      while (currentLine < state.lineMax) {
        const lineText = getLineText(currentLine);
        const blockEndMatch = getCheklistItemEndMatch(lineText);

        const currentContentStart = currentLine === startLine ? match[0].length : 0;
        const currentContentEnd = blockEndMatch ? blockEndMatch.index : lineText.length;

        const currentContent = lineText.slice(currentContentStart, currentContentEnd);
        totalLabelContent += currentContent;

        if (blockEndMatch) {
          break;
        }

        currentLine++;
      }

      state.tokens.push({
        type: 'inline',
        content: totalLabelContent,
        level: state.level + 1,
        lines: [startLine, currentLine],
        children: [],
      });

      state.tokens.push({ type: 'clist_close', level: state.level });

      state.line = currentLine + 1;
      listLines[1] = state.line;

      return true;
    },
    {},
  );
};
