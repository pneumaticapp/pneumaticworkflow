import { Remarkable } from 'remarkable';

import { checklistsRemarkablePlugin } from '../../RichEditor/utils/converters/customMarkdownPlugins';
import { createChecklistRenderer } from '../../TaskCard/checklist/createChecklistRenderer';
import { createCheckPlaceholderId } from '../../TaskCard/checklist/createCheckPlaceholderId';
import { createProgressbarPlaceholderId } from '../../TaskCard/checklist/createProgressbarPlaceholderId';
import { linkify } from '../linkify';
import { createAttachmentRenderer } from './attachmentRenderer';

interface ICreateRichTextRemarkableOptions {
  embedVideos: boolean;
  hideIcon?: boolean;
  interactiveChecklists?: boolean;
  checkboxPlaceholderClassName: string;
  videoClassName: string;
}

export const createRichTextRemarkable = ({
  embedVideos,
  hideIcon,
  interactiveChecklists,
  checkboxPlaceholderClassName,
  videoClassName,
}: ICreateRichTextRemarkableOptions): Remarkable => {
  return new Remarkable({
    html: true,
    breaks: true,
  })
    .use(checklistsRemarkablePlugin)
    .use(linkify)
    .use(createAttachmentRenderer(embedVideos, { video: videoClassName }, hideIcon))
    .use(
      createChecklistRenderer({
        renderCheck: (listApiName, itemApiName) => {
          if (interactiveChecklists) {
            return `<div id="${createCheckPlaceholderId(listApiName, itemApiName)}"></div>`;
          }

          return `<div class="${checkboxPlaceholderClassName}"></div>`;
        },
        renderProgressbar: (listApiName) => {
          if (!interactiveChecklists) {
            return '';
          }

          return `<div id="${createProgressbarPlaceholderId(listApiName)}"></div>`;
        },
        interactiveChecklist: interactiveChecklists,
      }),
    );
};
