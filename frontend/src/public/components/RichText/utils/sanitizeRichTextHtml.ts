import DOMPurify from 'dompurify';

import { setRichTextDirection } from './setRichTextDirection';

const RICH_TEXT_SANITIZE_CONFIG: DOMPurify.Config = {
  ADD_TAGS: ['iframe', 'video'],
  ADD_ATTR: [
    'allowfullscreen',
    'mozallowfullscreen',
    'webkitallowfullscreen',
    'frameborder',
    'allowtransparency',
    'scrolling',
    'preload',
    'controls',
    'target',
  ],
};

export const sanitizeRichTextHtml = (html: string): string => {
  const content = DOMPurify.sanitize(html, { ...RICH_TEXT_SANITIZE_CONFIG, RETURN_DOM_FRAGMENT: true });
  setRichTextDirection(content);

  const container = content.ownerDocument.createElement('div');
  container.appendChild(content);

  return container.innerHTML;
};
