import * as React from 'react';
import { useMemo, useCallback, RefObject } from 'react';
import { composeDecorators } from '@draft-js-plugins/editor';
import createLinkifyPlugin from '@draft-js-plugins/linkify';
import createMentionPlugin from 'draft-js-mention-plugin';
import createFocusPlugin from '@draft-js-plugins/focus';
import positionSuggestions from 'draft-js-mention-plugin/lib/utils/positionSuggestions';
import createToolbarPlugin from '@draft-js-plugins/static-toolbar';
import { ContentBlock } from 'draft-js';
import createLinkPlugin from '../utils/linksPlugin';
import createAttachmentPlugin from '../utils/AttachmentsPlugin';
import createCheckableListPlugin from '../utils/checklistsPlugin';
import { Image } from '../utils/AttachmentsPlugin/Image';
import { File } from '../utils/AttachmentsPlugin/File';
import { Video } from '../utils/AttachmentsPlugin/Video';
import { toolbarConfig } from '../toolbarSettings';
import { IPositionSuggestionsParams } from '../RichEditor.props';
import mentionsStyles from '../MentionStyles.css';
import focusStyles from '../FocusStyles.css';

type RichEditorPlugins = {
  linkifyPlugin: ReturnType<typeof createLinkifyPlugin>;
  linkPlugin: ReturnType<typeof createLinkPlugin>;
  toolbarPlugin: ReturnType<typeof createToolbarPlugin>;
  focusPlugin: ReturnType<typeof createFocusPlugin>;
  attachmentPlugin: ReturnType<typeof createAttachmentPlugin>;
  checkableListPlugin: ReturnType<typeof createCheckableListPlugin>;
  mentionPlugin: ReturnType<typeof createMentionPlugin>;
};

export function useRichEditorPlugins(
  isModal: boolean | undefined,
  editorContainerRef: RefObject<HTMLDivElement | null>,
  deleteAttachmentRef: RefObject<(block: ContentBlock) => void>,
): RichEditorPlugins {
  const linkifyPlugin = useMemo(() => createLinkifyPlugin(), []);
  const linkPlugin = useMemo(() => createLinkPlugin({ isModal }), [isModal]);
  const toolbarPlugin = useMemo(() => createToolbarPlugin(toolbarConfig), []);
  const focusPlugin = useMemo(
    () =>
      createFocusPlugin({
        theme: {
          focused: focusStyles['focused'],
          unfocused: focusStyles['unfocused'],
        },
      }),
    [],
  );

  const attachmentPlugin = useMemo(
    () =>
      createAttachmentPlugin({
        /* eslint-disable react/no-unstable-nested-components -- plugin API requires component factories */
        imageComponent: (p) => <Image {...p} deleteAttachment={(block) => deleteAttachmentRef.current?.(block)} />,
        fileComponent: (p) => <File {...p} deleteAttachment={(block) => deleteAttachmentRef.current?.(block)} />,
        videoComponent: (p) => <Video {...p} deleteAttachment={(block) => deleteAttachmentRef.current?.(block)} />,
        /* eslint-enable react/no-unstable-nested-components */
        decorator: composeDecorators(focusPlugin.decorator),
      }),
    [focusPlugin.decorator, deleteAttachmentRef],
  );

  // sameWrapperAsUnorderedListItem: false so default unordered-list-item and ordered-list-item from Draft.js are kept
  const checkableListPlugin = useMemo(() => createCheckableListPlugin(), []);

  const customPositionSuggestions = useCallback(({ decoratorRect, popover, state, props: suggestionProps }: IPositionSuggestionsParams) => {
    const { left, ...restProps } = positionSuggestions({ decoratorRect, popover, state, props: suggestionProps });
    const container = editorContainerRef.current;
    const editorWidth = container?.offsetWidth ?? 0;
    const popoverWidth = popover.offsetWidth;
    const newLeft = parseFloat(String(left)) + popoverWidth > editorWidth ? `${editorWidth - popoverWidth}px` : left;
    return { left: newLeft, ...restProps };
  }, [editorContainerRef]);

  const mentionPlugin = useMemo(
    () =>
      createMentionPlugin({
        mentionTrigger: '@',
        entityMutability: 'IMMUTABLE',
        supportWhitespace: false,
        mentionPrefix: '@',
        theme: mentionsStyles,
        positionSuggestions: customPositionSuggestions,
      }),
    [customPositionSuggestions],
  );

  return {
    linkifyPlugin,
    linkPlugin,
    toolbarPlugin,
    focusPlugin,
    attachmentPlugin,
    checkableListPlugin,
    mentionPlugin,
  } as const;
}
