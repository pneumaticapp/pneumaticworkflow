/**
 * Greedy link-text capture. Works for alt text with unescaped [ and ] because
 * parsing backtracks to the last ]( before the URL/title suffix.
 */
export const MARKDOWN_LINK_TEXT_CAPTURE = '(.*)';

export const ATTACHMENT_MARKDOWN_BODY =
  `!?\\[${MARKDOWN_LINK_TEXT_CAPTURE}\\]\\((.*?)\\s*"(?:attachment_id:(\\d*)\\s*)?entityType:(image|video|file)[^"]*"\\)?`;

export const ATTACHMENT_MARKDOWN_LINE_RE = new RegExp(`^${ATTACHMENT_MARKDOWN_BODY}$`);

export const ATTACHMENT_MARKDOWN_INLINE_RE = new RegExp(ATTACHMENT_MARKDOWN_BODY);

export const GENERAL_MARKDOWN_LINK_BODY =
  `!?\\[${MARKDOWN_LINK_TEXT_CAPTURE}\\]\\((.*?)\\s*(?:"(?:attachment_id:(\\d*))?(?:\\s+)?(?:entityType:([^"\\s]*))?(?:[^"]*)?")?\\s*\\)`;

export const GENERAL_MARKDOWN_LINK_RE = new RegExp(`^${GENERAL_MARKDOWN_LINK_BODY}`);

export const GENERAL_MARKDOWN_LINK_IMPORT_RE = new RegExp(GENERAL_MARKDOWN_LINK_BODY);

/**
 * Escapes ] and \\ for markdown link alt text.
 */
export function escapeMarkdownLinkText(text: string): string {
  return text.replace(/\\/g, '\\\\').replace(/]/g, '\\]');
}

/**
 * Unescapes markdown link alt text (e.g. file\[1\] → file[1]).
 * Plain names without escapes are returned unchanged.
 */
export function unescapeMarkdownLinkText(raw: string): string {
  return raw.replace(/\\(.)/g, (_, char: string) => char);
}
