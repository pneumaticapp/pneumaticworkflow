import DOMPurify from 'dompurify';

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

export const sanitizeRichTextHtml = (html: string): string => (
  DOMPurify.sanitize(html, RICH_TEXT_SANITIZE_CONFIG)
);
