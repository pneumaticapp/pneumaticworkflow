import type { TMentionData } from '../../LexicalRichEditor/types';
import type { MentionMenuOption } from './types';

export const MENTION_TRIGGER = '@';

export const TRIGGER_REGEX = new RegExp(
  `(^|\\s|\\()(${MENTION_TRIGGER}([^\\s@]*))$`,
);

export function buildOptions(mentions: TMentionData[]): MentionMenuOption[] {
  return mentions.map((m) => ({
    key: String(m.id ?? 0),
    id: m.id ?? 0,
    name: m.name,
    link: m.link,
  }));
}

export function filterOptions(
  options: MentionMenuOption[],
  query: string | null,
): MentionMenuOption[] {
  if (!query || !query.trim()) return options;
  const q = query.toLowerCase();
  return options.filter((opt) => opt.name.toLowerCase().includes(q));
}
