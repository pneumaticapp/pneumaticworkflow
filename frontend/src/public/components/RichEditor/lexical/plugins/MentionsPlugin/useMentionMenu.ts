import { useMemo, useState, useCallback, useRef, useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { mergeRegister } from '@lexical/utils';
import {
  $createTextNode,
  $getSelection,
  $getNodeByKey,
  $isRangeSelection,
  $isTextNode,
  $createRangeSelection,
  $setSelection,
  getDOMSelection,
  KEY_ARROW_DOWN_COMMAND,
  KEY_ARROW_UP_COMMAND,
  KEY_ENTER_COMMAND,
  KEY_ESCAPE_COMMAND,
  KEY_TAB_COMMAND,
  COMMAND_PRIORITY_CRITICAL,
} from 'lexical';
import { $createMentionNode } from '../../nodes/MentionNode';
import type { MenuState, MentionMenuOption } from './types';
import { buildOptions, filterOptions, TRIGGER_REGEX } from './mentionOptions';

export function useMentionMenu(mentions: { id?: number; name: string; link?: string }[]) {
  const [editor] = useLexicalComposerContext();
  const [menuState, setMenuState] = useState<MenuState | null>(null);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const optionsRef = useRef<MentionMenuOption[]>([]);
  const menuStateRef = useRef<MenuState | null>(null);
  const highlightedIndexRef = useRef(0);
  menuStateRef.current = menuState;
  highlightedIndexRef.current = highlightedIndex;

  const allOptions = useMemo(() => buildOptions(mentions), [mentions]);
  const filteredOptions = useMemo(
    () => filterOptions(allOptions, menuState?.query ?? null),
    [allOptions, menuState?.query],
  );
  optionsRef.current = filteredOptions;

  const closeMenu = useCallback(() => {
    setMenuState(null);
  }, []);

  const applyMention = useCallback(
    (option: MentionMenuOption) => {
      const state = menuStateRef.current;
      if (!state) return;

      const { anchorKey, replaceableString } = state;
      const { id, name, link } = option;

      closeMenu();
      editor.getRootElement()?.focus();

      editor.update(
        () => {
          let anchorNode = $getNodeByKey(anchorKey);
          if (!anchorNode) {
            const sel = $getSelection();
            if ($isRangeSelection(sel) && sel.anchor.type === 'text') {
              anchorNode = sel.anchor.getNode();
            }
          }
          if (!anchorNode || !$isTextNode(anchorNode) || !anchorNode.isSimpleText()) return;

          const text = anchorNode.getTextContent();
          const idx = text.indexOf(replaceableString);
          if (idx < 0) return;

          const endIdx = Math.min(idx + replaceableString.length, text.length);
          const selection = $createRangeSelection();
          selection.setTextNodeRange(anchorNode, idx, anchorNode, endIdx);
          $setSelection(selection);

          const mentionNode = $createMentionNode({ id, name, link });
          const spaceNode = $createTextNode(' ');
          $getSelection()?.insertNodes([mentionNode, spaceNode]);
          const nodeAfterMention = mentionNode.getNextSibling();
          if (nodeAfterMention && $isTextNode(nodeAfterMention)) {
            nodeAfterMention.selectEnd();
          } else {
            mentionNode.selectNext();
          }
        },
        { tag: 'mention-insert' },
      );
    },
    [editor, closeMenu],
  );

  useEffect(() => {
    if (mentions.length === 0) return undefined;

    return mergeRegister(
      editor.registerUpdateListener(({ editorState }) => {
        editorState.read(() => {
          const selection = $getSelection();
          if (!$isRangeSelection(selection) || !selection.isCollapsed()) {
            closeMenu();
            return;
          }
          const { anchor } = selection;
          if (anchor.type !== 'text') {
            closeMenu();
            return;
          }
          const anchorNode = anchor.getNode();
          if (!anchorNode.isSimpleText()) {
            closeMenu();
            return;
          }
          const textUpToCursor = anchorNode.getTextContent().slice(0, anchor.offset);
          const match = TRIGGER_REGEX.exec(textUpToCursor);
          if (!match) {
            closeMenu();
            return;
          }
          const replaceableString = match[2];
          const query = match[3] ?? '';

          const domSelection = getDOMSelection(window);
          if (!domSelection?.anchorNode) {
            closeMenu();
            return;
          }

          const range = window.document.createRange();
          const leadOffset = anchor.offset - replaceableString.length;
          try {
            range.setStart(domSelection.anchorNode, leadOffset);
            range.setEnd(domSelection.anchorNode, anchor.offset);
          } catch {
            closeMenu();
            return;
          }

          const rect = range.getBoundingClientRect();
          highlightedIndexRef.current = 0;
          setHighlightedIndex(0);
          setMenuState({
            rect,
            anchorKey: anchorNode.getKey(),
            anchorOffset: anchor.offset,
            replaceableString,
            query,
          });
        });
      }),

      editor.registerCommand(
        KEY_ARROW_DOWN_COMMAND,
        (event: KeyboardEvent) => {
          if (menuStateRef.current && optionsRef.current.length > 0) {
            event.preventDefault();
            setHighlightedIndex((i) => {
              const next = (i + 1) % optionsRef.current.length;
              highlightedIndexRef.current = next;
              return next;
            });
            return true;
          }
          return false;
        },
        COMMAND_PRIORITY_CRITICAL,
      ),
      editor.registerCommand(
        KEY_ARROW_UP_COMMAND,
        (event: KeyboardEvent) => {
          if (menuStateRef.current && optionsRef.current.length > 0) {
            event.preventDefault();
            setHighlightedIndex((i) => {
              const next = i <= 0 ? optionsRef.current.length - 1 : i - 1;
              highlightedIndexRef.current = next;
              return next;
            });
            return true;
          }
          return false;
        },
        COMMAND_PRIORITY_CRITICAL,
      ),
      editor.registerCommand(
        KEY_ENTER_COMMAND,
        (event: KeyboardEvent) => {
          if (menuStateRef.current && optionsRef.current.length > 0) {
            const option = optionsRef.current[highlightedIndexRef.current];
            if (option) {
              event.preventDefault();
              applyMention(option);
              return true;
            }
          }
          return false;
        },
        COMMAND_PRIORITY_CRITICAL,
      ),
      editor.registerCommand(
        KEY_TAB_COMMAND,
        (event: KeyboardEvent) => {
          if (menuStateRef.current && optionsRef.current.length > 0) {
            const option = optionsRef.current[highlightedIndexRef.current];
            if (option) {
              event.preventDefault();
              applyMention(option);
              return true;
            }
          }
          return false;
        },
        COMMAND_PRIORITY_CRITICAL,
      ),
      editor.registerCommand(
        KEY_ESCAPE_COMMAND,
        (event: KeyboardEvent) => {
          if (menuStateRef.current) {
            event.preventDefault();
            closeMenu();
            return true;
          }
          return false;
        },
        COMMAND_PRIORITY_CRITICAL,
      ),
    );
  }, [editor, mentions.length, closeMenu, applyMention]);

  return {
    menuState,
    filteredOptions,
    highlightedIndex,
    setHighlightedIndex,
    closeMenu,
    applyMention,
  };
}
