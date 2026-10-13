import type MarkdownIt from 'markdown-it';

import { mentionsRegex } from '../../../../constants/defaultValues';
import { unescapeMarkdownLinkText } from '../../../RichEditor/utils/converters/markdownLinkText';

interface IMentionPluginOptions {
  className: string;
}

const MENTION_INLINE_RE = new RegExp(`^${mentionsRegex.source}`);

export const mentionPlugin = (md: MarkdownIt, { className }: IMentionPluginOptions): void => {
  md.inline.ruler.before('link', 'pneumatic_mention', (state, silent) => {
    const match = MENTION_INLINE_RE.exec(state.src.slice(state.pos));

    if (!match) {
      return false;
    }

    if (!silent) {
      const token = state.push('pneumatic_mention', '', 0);
      const [, mentionName] = match;
      token.content = unescapeMarkdownLinkText(mentionName ?? '');
    }

    state.pos += match[0].length;

    return true;
  });

  md.renderer.rules.pneumatic_mention = (tokens, idx) => {
    const name = tokens[idx].content;

    return `<span class="${className}">@${md.utils.escapeHtml(name)}</span>`;
  };
};
