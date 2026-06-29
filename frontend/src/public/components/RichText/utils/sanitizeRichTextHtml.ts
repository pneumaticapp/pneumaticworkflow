import * as DOMPurifyModule from 'dompurify';
import type { Config } from 'dompurify';

type TDOMPurify = typeof import('dompurify');

const getDOMPurify = (): TDOMPurify => {
  const moduleExport = DOMPurifyModule as unknown as TDOMPurify & ((window?: Window) => TDOMPurify);

  if (typeof moduleExport.sanitize === 'function') {
    return moduleExport;
  }

  return moduleExport(typeof window !== 'undefined' ? window : undefined as unknown as Window);
};

const RICH_TEXT_SANITIZE_CONFIG: Config = {
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
  getDOMPurify().sanitize(html, RICH_TEXT_SANITIZE_CONFIG)
);
