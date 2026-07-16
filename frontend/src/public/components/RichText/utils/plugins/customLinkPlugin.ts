import type MarkdownIt from 'markdown-it';

import {
  parseAttachmentMarkdownFromStart,
  parseGeneralMarkdownLinkFromStart,
  unescapeMarkdownLinkText,
} from '../../../RichEditor/utils/converters/markdownLinkText';
import {
  getAttachmentEntityType,
  getAttachmentEntityTypeByFilename,
} from '../../../RichEditor/utils/getAttachmentEntityType';
import { ECustomEditorEntities } from '../../../RichEditor/utils/types';
import { renderAttachmentHtml } from '../renderAttachmentHtml';
import { IRenderEmbedVideoHtmlOptions, renderLinkHtml } from '../renderEmbedVideoHtml';

interface ICustomLinkPluginOptions extends IRenderEmbedVideoHtmlOptions {
  embedVideos: boolean;
  hideIcon?: boolean;
}

interface IPneumaticLinkMeta {
  url: string;
  name: string;
  entityType: ECustomEditorEntities;
  isLinkified: boolean;
}

const getLinkEntityType = (
  url: string,
  entityType: string | undefined,
  name?: string,
  isImageMarkdown = false,
): ECustomEditorEntities => {
  const googleBucket = 'https://storage.googleapis.com/';
  const attachmentEntityTypes = [
    ECustomEditorEntities.Image,
    ECustomEditorEntities.File,
    ECustomEditorEntities.Video,
  ];

  if (entityType) {
    return attachmentEntityTypes.includes(entityType as ECustomEditorEntities)
      ? (entityType as ECustomEditorEntities)
      : getAttachmentEntityType(url);
  }

  if (name) {
    const entityTypeByName = getAttachmentEntityTypeByFilename(name);
    if (entityTypeByName !== ECustomEditorEntities.Link) {
      return entityTypeByName;
    }
  }

  if (isImageMarkdown) {
    return ECustomEditorEntities.Image;
  }

  if (url.includes(googleBucket)) {
    return getAttachmentEntityType(url);
  }

  return ECustomEditorEntities.Link;
};

export const customLinkPlugin = (
  md: MarkdownIt,
  { embedVideos, hideIcon, ...embedVideoOptions }: ICustomLinkPluginOptions,
): void => {
  md.inline.ruler.before('link', 'pneumatic_link', (state, silent) => {
    const src = state.src.slice(state.pos);
    const attachmentMatch = parseAttachmentMarkdownFromStart(src);
    const generalMatch = attachmentMatch ? null : parseGeneralMarkdownLinkFromStart(src);
    const match = attachmentMatch ?? generalMatch;

    if (!match) {
      return false;
    }

    const [, nameRaw, url, , entityTypeRaw] = match;
    const name = unescapeMarkdownLinkText(nameRaw ?? '');
    const isImageMarkdown = match[0].startsWith('![');
    const entityType = getLinkEntityType(url, entityTypeRaw, name, isImageMarkdown);

    if (!silent) {
      const token = state.push('pneumatic_link', '', 0);
      token.meta = {
        url,
        name,
        entityType,
        isLinkified: false,
      } satisfies IPneumaticLinkMeta;
    }

    state.pos += match[0].length;

    return true;
  });

  md.renderer.rules.pneumatic_link = (tokens, idx) => {
    const { url, name, entityType, isLinkified } = tokens[idx].meta as IPneumaticLinkMeta;

    if (isLinkified || entityType === ECustomEditorEntities.Link) {
      return renderLinkHtml(url, name, embedVideos, embedVideoOptions);
    }

    return renderAttachmentHtml({
      url,
      name,
      entityType,
      hideIcon,
    });
  };
};

export type { IPneumaticLinkMeta };
