const ATTACHMENT_LINK_SUFFIX_RE =
  /^\]\((.*?)\s*"(?:attachment_id:(\d*)\s*)?entityType:(image|video|file)[^"]*"\)/;

const GENERAL_LINK_SUFFIX_RE =
  /^\]\((.*?)\s*(?:"(?:attachment_id:(\d*))?(?:\s+)?(?:entityType:([^"\s]*))?(?:[^"]*)?")?\s*\)/;

const MARKDOWN_LINK_PREFIX_RE = /^!?\[/;

type TMarkdownLinkParser = (text: string) => RegExpMatchArray | null;

function toRegExpMatchArray(
  match: RegExpMatchArray,
  index: number,
  input: string,
): RegExpMatchArray {
  const result = [...match] as RegExpMatchArray;
  result.index = index;
  result.input = input;

  return result;
}

function createMarkdownLinkMatcher(
  matchAt: (text: string) => RegExpMatchArray | null,
): RegExp {
  const matcher = {
    exec(text: string): RegExpMatchArray | null {
      const match = matchAt(text);

      if (!match) {
        return null;
      }

      return toRegExpMatchArray(match, match.index ?? 0, text);
    },
    [Symbol.match](text: string): RegExpMatchArray | null {
      return matcher.exec(text);
    },
  };

  return matcher as RegExp;
}

/**
 * Finds the closing `]` of markdown link alt text (the one immediately before `(`).
 * Respects backslash escapes in alt text.
 */
function findMarkdownLinkAltCloseIndex(src: string, openBracketIndex: number): number | null {
  let index = openBracketIndex + 1;

  while (index < src.length) {
    const char = src[index];

    if (char === '\\' && index + 1 < src.length) {
      index += 2;
    } else if (char === ']' && src[index + 1] === '(') {
      return index;
    } else {
      index += 1;
    }
  }

  return null;
}

function buildMarkdownLinkMatch(
  src: string,
  openBracketIndex: number,
  closeBracketIndex: number,
  suffixMatch: RegExpMatchArray,
): RegExpMatchArray {
  const nameRaw = src.slice(openBracketIndex + 1, closeBracketIndex);
  const fullMatch = src.slice(0, closeBracketIndex + suffixMatch[0].length);
  const match = [fullMatch, nameRaw, ...suffixMatch.slice(1)] as RegExpMatchArray;
  match.index = 0;

  return match;
}

function parseMarkdownLinkWithSuffix(
  src: string,
  suffixRegExp: RegExp,
): RegExpMatchArray | null {
  const prefixMatch = MARKDOWN_LINK_PREFIX_RE.exec(src);

  if (!prefixMatch) {
    return null;
  }

  const openBracketIndex = prefixMatch[0].length - 1;
  const closeBracketIndex = findMarkdownLinkAltCloseIndex(src, openBracketIndex);

  if (closeBracketIndex === null) {
    return null;
  }

  const suffixMatch = suffixRegExp.exec(src.slice(closeBracketIndex));

  if (!suffixMatch) {
    return null;
  }

  return buildMarkdownLinkMatch(src, openBracketIndex, closeBracketIndex, suffixMatch);
}

export function parseAttachmentMarkdownFromStart(src: string): RegExpMatchArray | null {
  return parseMarkdownLinkWithSuffix(src, ATTACHMENT_LINK_SUFFIX_RE);
}

export function parseGeneralMarkdownLinkFromStart(src: string): RegExpMatchArray | null {
  return parseMarkdownLinkWithSuffix(src, GENERAL_LINK_SUFFIX_RE);
}

export function parseMarkdownLinkFromStart(src: string): RegExpMatchArray | null {
  return parseAttachmentMarkdownFromStart(src) ?? parseGeneralMarkdownLinkFromStart(src);
}

function isMarkdownLinkStart(text: string, index: number): boolean {
  if (text[index] === '[') {
    return true;
  }

  return text[index] === '!' && text[index + 1] === '[';
}

function createMarkdownLinkSearchRegExp(parseFromStart: TMarkdownLinkParser): RegExp {
  return createMarkdownLinkMatcher((text) => {
    for (let index = 0; index < text.length; index += 1) {
      if (isMarkdownLinkStart(text, index)) {
        const match = parseFromStart(text.slice(index));

        if (match) {
          return toRegExpMatchArray(match, index, text);
        }
      }
    }

    return null;
  });
}

function createMarkdownLinkLineRegExp(parseFromStart: TMarkdownLinkParser): RegExp {
  return createMarkdownLinkMatcher((text) => {
    const match = parseFromStart(text);

    if (match && match[0].length === text.length) {
      return toRegExpMatchArray(match, 0, text);
    }

    return null;
  });
}

function createMarkdownLinkStartRegExp(parseFromStart: TMarkdownLinkParser): RegExp {
  return createMarkdownLinkMatcher((text) => {
    const match = parseFromStart(text);

    if (!match) {
      return null;
    }

    return toRegExpMatchArray(match, 0, text);
  });
}

/** @deprecated Use parseAttachmentMarkdownFromStart. Kept for tests comparing RegExp API. */
export const ATTACHMENT_MARKDOWN_INLINE_RE = createMarkdownLinkSearchRegExp(parseAttachmentMarkdownFromStart);

/** @deprecated Use parseAttachmentMarkdownFromStart with full-line check. */
export const ATTACHMENT_MARKDOWN_LINE_RE = createMarkdownLinkLineRegExp(parseAttachmentMarkdownFromStart);

/** @deprecated Use parseGeneralMarkdownLinkFromStart. */
export const GENERAL_MARKDOWN_LINK_RE = createMarkdownLinkStartRegExp(parseGeneralMarkdownLinkFromStart);

/** @deprecated Use parseGeneralMarkdownLinkFromStart via search RegExp. */
export const GENERAL_MARKDOWN_LINK_IMPORT_RE = createMarkdownLinkSearchRegExp(parseGeneralMarkdownLinkFromStart);

/** Full-line match for block-level general link import. */
export const GENERAL_MARKDOWN_LINK_LINE_RE = createMarkdownLinkLineRegExp(parseGeneralMarkdownLinkFromStart);

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

export function getMarkdownLinkMatchEndIndex(text: string, startIndex: number, parser: TMarkdownLinkParser): number | false {
  const match = parser(text.slice(startIndex));

  if (!match) {
    return false;
  }

  return startIndex + match[0].length;
}
