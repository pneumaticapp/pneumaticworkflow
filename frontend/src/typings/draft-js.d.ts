// @todo flesh out component type
declare module 'draft-js-emoji-plugin' {
  function createEmojiPlugin(config?: object): any;
  export type EmojiSuggestions = any;
  export default createEmojiPlugin;
}

declare module 'draft-js-mention-plugin' {
  // @todo missing defaultTheme
  // @todo missing defaultSuggestionsFilter

  type Props = {
    suggestions: any[];
    onAddMention(mention: any): void;
    entryComponent(...props: any[]): JSX.Element;
    entityMutability: string;
  };

  type State = {
    isActive: boolean;
    focusedOptionIndex: number;
  };

  export type MentionSuggestions = React.Component<Props, State>;
  export function defaultSuggestionsFilter<T>(value: string, suggestions: T[]): any;
  export default function createMentionPlugin(config?: object): any;
}

declare module 'draft-js-mention-plugin/lib/utils/positionSuggestions' {
  export default function positionSuggestions(value: any): any;
}

declare module 'draft-js-single-line-plugin' {
  export default function createSingleLinePlugin(): any;
}

type EditorState = import('draft-js').EditorState;
declare module 'draftjs-filters' {
  export function filterEditorState(
    config: {
      blocks: string[];
      styles: string[];
      entities: {
        type: string;
        attributes?: string[];
        allowlist?: {
          [attribute: string]: string | boolean;
        };
      }[];
      maxNesting: number;
      whitespacedCharacters: string[];
    },
    initialState: EditorState,
  ): EditorState;
}
