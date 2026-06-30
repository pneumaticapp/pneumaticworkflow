/* eslint-disable @typescript-eslint/no-explicit-any, no-restricted-syntax, no-continue, no-plusplus */
import Autolinker from 'autolinker';
import type MarkdownIt from 'markdown-it';

import { createMarkdownToken, IMarkdownToken } from '../createMarkdownToken';
import { IRenderEmbedVideoHtmlOptions, renderLinkHtml } from '../renderEmbedVideoHtml';

const LINK_SCAN_RE = /www|@|:\/\//;

interface ICollectedLink {
  text: string;
  url: string;
}

const collectLinks = (text: string): ICollectedLink[] => {
  const links: ICollectedLink[] = [];

  Autolinker.link(text, {
    stripPrefix: false,
    urls: true,
    email: true,
    replaceFn: (match) => {
      if (match.getType() === 'url') {
        links.push({
          text: match.getMatchedText(),
          url: (match as any).getUrl(),
        });
      } else if (match.getType() === 'email') {
        links.push({
          text: match.getMatchedText(),
          url: `mailto:${(match as any).getEmail().replace(/^mailto:/i, '')}`,
        });
      }

      return false;
    },
  });

  return links;
};

export const linkifyInlineChildren = (
  children: IMarkdownToken[],
  embedVideos: boolean,
  embedVideoOptions: IRenderEmbedVideoHtmlOptions,
): IMarkdownToken[] => {
  const result: IMarkdownToken[] = [];
  let linkDepth = 0;

  for (const token of children) {
    if (token.type === 'link_open') {
      linkDepth += 1;
      result.push(token);
      continue;
    }

    if (token.type === 'link_close') {
      linkDepth = Math.max(0, linkDepth - 1);
      result.push(token);
      continue;
    }

    if (linkDepth > 0 || token.type !== 'text' || !LINK_SCAN_RE.test(token.content)) {
      result.push(token);
      continue;
    }

    const links = collectLinks(token.content);

    if (!links.length) {
      result.push(token);
      continue;
    }

    let text = token.content;
    let {level} = token;

    for (const link of links) {
      const pos = text.indexOf(link.text);

      if (pos < 0) {
        continue;
      }

      if (pos > 0) {
        const textToken = createMarkdownToken('text', '', 0);
        textToken.content = text.slice(0, pos);
        textToken.level = level;
        result.push(textToken);
      }

      const embedHtml = embedVideos
        ? renderLinkHtml(link.url, link.text, true, embedVideoOptions)
        : null;

      if (embedHtml?.includes('<iframe')) {
        const htmlToken = createMarkdownToken('html_inline', '', 0);
        htmlToken.content = embedHtml;
        htmlToken.level = level;
        result.push(htmlToken);
      } else {
        const linkOpen = createMarkdownToken('link_open', 'a', 1);
        linkOpen.attrs = [['href', link.url], ['target', '_blank']];
        linkOpen.level = level++;

        const linkText = createMarkdownToken('text', '', 0);
        linkText.content = link.text;
        linkText.level = level;

        const linkClose = createMarkdownToken('link_close', 'a', -1);
        linkClose.level = --level;

        result.push(linkOpen, linkText, linkClose);
      }

      text = text.slice(pos + link.text.length);
    }

    if (text.length) {
      const textToken = createMarkdownToken('text', '', 0);
      textToken.content = text;
      textToken.level = level;
      result.push(textToken);
    }
  }

  return result;
};

export const linkifyPlugin = (
  md: MarkdownIt,
  { embedVideos, ...embedVideoOptions }: IRenderEmbedVideoHtmlOptions & { embedVideos: boolean },
): void => {
  md.core.ruler.after('inline', 'pneumatic_linkify', (state) => {
    for (const token of state.tokens) {
      if (token.type !== 'inline' || !token.children) {
        continue;
      }

      token.children = linkifyInlineChildren(
        token.children as unknown as IMarkdownToken[],
        embedVideos,
        embedVideoOptions,
      ) as unknown as typeof token.children;
    }
  });
};
