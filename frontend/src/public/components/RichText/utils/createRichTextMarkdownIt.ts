import { IntlShape } from 'react-intl';
import markdownit from 'markdown-it'

import { TTaskVariable } from '../../TemplateEdit/types';
import { createCheckPlaceholderId } from '../../TaskCard/checklist/createCheckPlaceholderId';
import { createProgressbarPlaceholderId } from '../../TaskCard/checklist/createProgressbarPlaceholderId';
import { checklistPlugin } from './plugins/checklistPlugin';
import { linkifyPlugin } from './plugins/linkifyPlugin';
import { customLinkPlugin } from './plugins/customLinkPlugin';
import { mentionPlugin } from './plugins/mentionPlugin';
import { variablePlugin } from './plugins/variablePlugin';
import type { IRenderEmbedVideoHtmlOptions } from './renderEmbedVideoHtml';

export interface ICreateRichTextMarkdownItOptions extends IRenderEmbedVideoHtmlOptions {
  embedVideos: boolean;
  hideIcon?: boolean;
  interactiveChecklists?: boolean;
  checkboxPlaceholderClassName: string;
  mentionClassName: string;
  variables?: TTaskVariable[];
  formatMessage: IntlShape['formatMessage'];
  badgeClassName: string;
  specificityBadgeClassName: string;
}

export const createRichTextMarkdownIt = ({
  embedVideos,
  hideIcon,
  interactiveChecklists,
  checkboxPlaceholderClassName,
  videoClassName,
  videoContainerClassName,
  mentionClassName,
  variables,
  formatMessage,
  badgeClassName,
  specificityBadgeClassName,
}: ICreateRichTextMarkdownItOptions): any => {
  const md = markdownit({
    html: true,
    linkify: false,
  });

  md.disable(['link', 'image']);

  md.use(mentionPlugin, { className: mentionClassName });
  md.use(variablePlugin, {
    variables,
    formatMessage,
    badgeClassName,
    specificityBadgeClassName,
  });
  md.use(customLinkPlugin, {
    embedVideos,
    hideIcon,
    videoClassName,
    videoContainerClassName,
  });
  md.use(checklistPlugin, {
    interactiveChecklists,
    checkboxPlaceholderClassName,
    renderCheckPlaceholder: (listApiName, itemApiName) => {
      if (interactiveChecklists) {
        return `<div id="${createCheckPlaceholderId(listApiName, itemApiName)}"></div>`;
      }

      return `<div class="${checkboxPlaceholderClassName}"></div>`;
    },
    renderProgressbarPlaceholder: (listApiName) => {
      if (!interactiveChecklists) {
        return '';
      }

      return `<div id="${createProgressbarPlaceholderId(listApiName)}"></div>`;
    },
  });
  md.use(linkifyPlugin, { embedVideos, videoClassName, videoContainerClassName });

  return md;
};
