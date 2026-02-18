import React from 'react';
import { createPortal } from 'react-dom';
import { useMentionMenu } from './useMentionMenu';
import { MentionMenuList } from './MentionMenuList';
import type { MentionsPluginProps } from './types';

export type { MentionMenuOption, MentionsPluginProps } from './types';

export function MentionsPlugin({ mentions }: MentionsPluginProps): React.ReactElement | null {
  const {
    menuState,
    filteredOptions,
    highlightedIndex,
    setHighlightedIndex,
    applyMention,
  } = useMentionMenu(mentions);

  if (mentions.length === 0) return null;
  if (!menuState) return null;
  if (filteredOptions.length === 0) return null;

  const menuContent = (
    <MentionMenuList
      rect={menuState.rect}
      options={filteredOptions}
      highlightedIndex={highlightedIndex}
      onSelect={applyMention}
      onHighlight={setHighlightedIndex}
    />
  );

  return createPortal(menuContent, document.body);
}
