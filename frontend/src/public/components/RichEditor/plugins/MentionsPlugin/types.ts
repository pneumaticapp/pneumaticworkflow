import type { TMentionData } from '../../types';

export type MenuState = {
  rect: DOMRect;
  anchorKey: string;
  anchorOffset: number;
  replaceableString: string;
  query: string;
};

export type MentionMenuOption = {
  key: string;
  id: number;
  name: string;
  link?: string;
};

export type MentionsPluginProps = {
  mentions: TMentionData[];
};
