import * as React from 'react';
import ReactDOMServer from 'react-dom/server';
import { Remarkable } from 'remarkable';
import { LinkCloseToken } from 'remarkable/lib';

import {
  youtubeVideoRegexp,
  loomVideoRegexp,
  wistiaVideoRegexp,
} from '../../../constants/defaultValues';
import { DocumentAttachment } from '../../Attachments/DocumentAttachment';
import {
  linksRemarkablePlugin,
  TCustomLinkToken,
} from '../../RichEditor/utils/converters/customMarkdownPlugins';
import { ECustomEditorEntities } from '../../RichEditor/utils/types';

interface IAttachmentRendererStyles {
  video: string;
}

export const createAttachmentRenderer = (
  embedVideoLinks: boolean,
  styles: IAttachmentRendererStyles,
  hideIcon?: boolean,
) => {
  const renderLink = (url: string, name: string) => {
    const defaultLinkHtml = `<a href="${url}" target="_blank">${name}</a>`;
    if (!embedVideoLinks) {
      return defaultLinkHtml;
    }

    const renderRules = [
      {
        regExp: loomVideoRegexp,
        replaceLogic: (_match: string, group1: string) => {
          return '<div><iframe'
            + ` class="${styles.video}"`
            + ' frameBorder="0"'
            + ` src="https://www.useloom.com/embed/${group1}"`
            + ' webkitallowfullscreen mozallowfullscreen allowfullscreen'
            + '></iframe></div>';
        },
      },
      {
        regExp: youtubeVideoRegexp,
        replaceLogic: (_match: string, group1: string) => {
          return '<div><iframe'
            + ` class="${styles.video}"`
            + ' frameBorder="0"'
            + ` src="//www.youtube.com/embed/${group1}"`
            + ' webkitallowfullscreen mozallowfullscreen allowfullscreen'
            + '></iframe></div>';
        },
      },
      {
        regExp: wistiaVideoRegexp,
        replaceLogic: (_match: string, videoId: string) => {
          const videoUrl = `https://fast.wistia.com/embed/medias/${videoId}`;

          return '<div><iframe'
            + ` class="${styles.video}"`
            + ' allowtransparency="true" frameborder="0" scrolling="no"'
            + ` src="${videoUrl}"`
            + ' webkitallowfullscreen mozallowfullscreen allowfullscreen'
            + '></iframe></div>';
        },
      },
    ];

    const renderVideoLogic = renderRules.find(({ regExp }) => regExp.test(url));
    if (renderVideoLogic) {
      return url.replace(renderVideoLogic.regExp, renderVideoLogic.replaceLogic);
    }

    return defaultLinkHtml;
  };

  return (md: Remarkable) => {
    md.inline.ruler.disable(['links']);
    md.use(linksRemarkablePlugin, {});

    // @ts-expect-error remarkable token type extended by custom plugin
    md.renderer.rules.link_open = (tokens: TCustomLinkToken[], idx: number) => {
      const { url, name, entityType, isLinkified } = tokens[idx];

      if (isLinkified || !entityType) {
        return renderLink(url, name);
      }

      const renderMap: Record<ECustomEditorEntities, string> = {
        [ECustomEditorEntities.Link]: `<a href="${url}" target="_blank">`,
        [ECustomEditorEntities.Image]: `<img src=${url} />`,
        [ECustomEditorEntities.Video]: ReactDOMServer.renderToStaticMarkup(
          // eslint-disable-next-line jsx-a11y/media-has-caption
          <video src={url} preload="auto" controls />,
        ),
        [ECustomEditorEntities.File]: ReactDOMServer.renderToStaticMarkup(
          <DocumentAttachment name={name} url={url} isEdit={false} hideIcon={hideIcon} />,
        ),
        [ECustomEditorEntities.Variable]: '',
        [ECustomEditorEntities.Mention]: '',
      };

      return renderMap[entityType];
    };

    md.renderer.rules.link_close = (tokens: LinkCloseToken[], idx: number) => {
      const { entityType } = tokens[idx] as LinkCloseToken & { entityType?: string };
      if (entityType === 'LINK') {
        return '</a>';
      }

      return '';
    };
  };
};
