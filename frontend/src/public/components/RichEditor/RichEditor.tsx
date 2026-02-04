import * as React from 'react';
import { forwardRef, useCallback, useImperativeHandle, useMemo, useRef, useState, useEffect } from 'react';
import classnames from 'classnames';
import {
  EditorState,
  ContentState,
  getDefaultKeyBinding,
  RichUtils,
  ContentBlock,
  convertFromHTML,
  DefaultDraftBlockRenderMap,
} from 'draft-js';
import Editor from '@draft-js-plugins/editor';
import { removeBlock } from './utils/removeBlock';
import { stripUnsupportedStyles } from './utils/stripUnsupportedStyles';
import { getSuggestionByValue } from './utils/getSuggestionByValue';
import { handlePressTab } from './utils/handlePressTab';
import { trackAddVideo } from './utils/trackAddVideo';
import { convertDraftToText, getInitialEditorState } from './utils/converters';
import { handlePasteAttachments } from './utils/handlePasteAttachments';
import { removeOrphanedEntities } from './utils/removeOrphanedEntities';
import { applyListShortcut } from './utils/applyListShortcut';
import { handleUploadAttachments } from './utils/handleUploadAttachments';
import { deleteAttachment } from '../../api/deleteAttachment';
import { TEditorAttachment } from './utils/types';
import { cloneChecklist, setChecklistApiNames } from './utils/checklistsPlugin/setChecklistApiNames';
import { prepareChecklistsForAPI } from '../../utils/checklists/prepareChecklistsForAPI';
import { shouldHidePlaceholder } from './utils/shouldHidePlaceholder';
import { getForegroundClass } from '../UI/Fields/common/utils/getForegroundClass';
import { getSelectionExtendedForSafari } from './utils/getSelectionExtendedForSafari';
import { insertSelectedContent } from './utils/insertSelectedContent';
import { isSafari } from './utils/isSafari';
import { removeAllExcept } from './utils/removeAllExcept';
import { contentStateFromPastedText, isPastedContentWithVariables } from './utils/clipboardUtils';
import {
  stripHtmlToText,
  getSelectedContentForCopy,
  writeContentStateToClipboard,
} from './utils/editorCopyUtils';

import { ENTER_KEY_CODE } from '../../constants/defaultValues';
import { Loader } from '../UI';
import { IRichEditorProps, EEditorKeyCommand, IRichEditorHandle } from './RichEditor.props';
import { useRichEditorPlugins } from './hooks/useRichEditorPlugins';
import { EditorToolbar, IEditorToolbarProps } from './EditorToolbar';
import { EditorControls } from './EditorControls';

import styles from './RichEditor.css';
import 'draft-js/dist/Draft.css';

const ECommandState = { Handled: 'handled', NotHandled: 'not-handled' } as const;

export const RichEditor = forwardRef<IRichEditorHandle, IRichEditorProps>(function RichEditor(props, ref) {
  const {
    className,
    withChecklists = true,
    withMentions = true,
    withToolbar = true,
    title,
    decorators,
    children,
    submitIcon,
    cancelIcon,
    multiline = true,
    foregroundColor = 'white',
    onSubmit,
    onCancel,
    handleChange: handleChangeProp,
    handleChangeChecklists,
    accountId,
    mentions,
    defaultValue,
    initialState: initialStateProp,
    isModal,
    isInTaskDescriptionEditor,
    stripPastedFormatting,
    templateVariables = [],
  } = props;

  const [isLoading, setIsLoading] = useState(false);
  const [shouldSubmitAfterFileLoaded, setShouldSubmitAfterFileLoaded] = useState(false);
  const [editorState, setEditorState] = useState<EditorState>(
    () => initialStateProp ?? getInitialEditorState(defaultValue),
  );
  const [suggestions, setSuggestions] = useState(mentions);
  const [areSuggestionsOpened, setAreSuggestionsOpened] = useState(false);

  const editorContainerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<Editor>(null);
  const latestEditorStateRef = useRef<EditorState | null>(null);
  const lastTabKeyEventRef = useRef<React.KeyboardEvent | null>(null);
  const lastCopiedPlainTextRef = useRef('');
  const onChangeRef = useRef<(nextState: EditorState) => Promise<void>>(null as unknown as (nextState: EditorState) => Promise<void>);
  const editorStateRef = useRef(editorState);
  const deleteAttachmentRef = useRef<(block: ContentBlock) => void>(null as unknown as (block: ContentBlock) => void);

  latestEditorStateRef.current = editorState;
  editorStateRef.current = editorState;

  const onChange = useCallback(
    async (nextState: EditorState) => {
      const nextStateWithListShortcut = applyListShortcut(nextState);
      const normalizedNextState = removeOrphanedEntities(
        stripUnsupportedStyles(nextStateWithListShortcut, editorStateRef.current),
      );
      latestEditorStateRef.current = normalizedNextState;
      const prevContent = editorStateRef.current.getCurrentContent();
      const newContent = normalizedNextState.getCurrentContent();

      setEditorState(normalizedNextState);

      if (prevContent === newContent) return;

      const stateWithChecklists = setChecklistApiNames(normalizedNextState);
      const contentWithChecklists = stateWithChecklists.getCurrentContent();
      latestEditorStateRef.current = stateWithChecklists;
      editorStateRef.current = stateWithChecklists;
      setEditorState(stateWithChecklists);

      const plainText = convertDraftToText(contentWithChecklists);
      if (withChecklists && handleChangeChecklists) {
        handleChangeChecklists(prepareChecklistsForAPI(plainText));
      }
      await handleChangeProp(plainText);
    },
    [handleChangeProp, handleChangeChecklists, withChecklists],
  );

  onChangeRef.current = onChange;

  const doDeleteAttachment = useCallback((block: ContentBlock) => {
    const state = editorStateRef.current;
    const content = state.getCurrentContent();
    const entityKey = block.getEntityAt(0);
    const data = content.getEntity(entityKey).getData() as TEditorAttachment;
    if (data.id) deleteAttachment(data.id);
    onChangeRef.current(removeBlock(state, block.getKey()));
  }, []);

  deleteAttachmentRef.current = doDeleteAttachment;

  const {
    linkifyPlugin,
    linkPlugin,
    toolbarPlugin,
    focusPlugin,
    attachmentPlugin,
    checkableListPlugin,
    mentionPlugin,
  } = useRichEditorPlugins(isModal, editorContainerRef, deleteAttachmentRef);

  useEffect(() => {
    setSuggestions(mentions);
  }, [mentions]);

  useEffect(() => {
    const container = editorContainerRef.current;
    if (!container) return undefined;
    const handlePaste = (e: ClipboardEvent) =>
      handlePasteAttachments(
        e,
        accountId,
        editorStateRef.current,
        attachmentPlugin.addAttachment,
        () => setIsLoading(true),
        async (newState) => {
          await onChangeRef.current(newState);
          setIsLoading(false);
        },
      );
    container.onpaste = handlePaste;
    return () => {
      container.onpaste = null;
    };
  }, [accountId, attachmentPlugin.addAttachment]);

  const prevLoadingRef = useRef(isLoading);
  useEffect(() => {
    const prevIsLoading = prevLoadingRef.current;
    prevLoadingRef.current = isLoading;
    const loadingFinished = prevIsLoading && !isLoading;

    if (loadingFinished && shouldSubmitAfterFileLoaded && onSubmit) {
      onSubmit();
      setShouldSubmitAfterFileLoaded(false);
      const emptyContent = ContentState.createFromText('');
      setEditorState(EditorState.moveFocusToEnd(EditorState.push(editorStateRef.current, emptyContent, 'remove-range')));
    }

    const container = editorContainerRef.current;
    if (!container) return;
    if (!prevIsLoading && isLoading) container.onkeydown = () => false;
    if (loadingFinished) container.onkeydown = null;
  }, [isLoading, shouldSubmitAfterFileLoaded, onSubmit]);

  const resetEditor = useCallback(() => {
    const emptyContent = ContentState.createFromText('');
    setEditorState(EditorState.moveFocusToEnd(EditorState.push(editorStateRef.current, emptyContent, 'remove-range')));
  }, []);

  const handleSubmit = useCallback(() => {
    if (!onSubmit) return;
    if (isLoading) {
      setShouldSubmitAfterFileLoaded(true);
      return;
    }
    onSubmit();
    setShouldSubmitAfterFileLoaded(false);
    resetEditor();
  }, [onSubmit, isLoading, resetEditor]);

  const handleCancel = useCallback(() => {
    if (!onCancel) return;
    if (isLoading) {
      setShouldSubmitAfterFileLoaded(true);
      return;
    }
    onCancel();
    setShouldSubmitAfterFileLoaded(false);
    resetEditor();
  }, [onCancel, isLoading, resetEditor]);

  const customKeyBindingFn = useCallback((e: React.KeyboardEvent) => {
    if (e.keyCode === ENTER_KEY_CODE && (e.ctrlKey || e.metaKey)) return EEditorKeyCommand.Enter;
    if (e.key === 'Tab' || e.keyCode === 9) {
      lastTabKeyEventRef.current = e;
      return EEditorKeyCommand.Tab;
    }
    return getDefaultKeyBinding(e);
  }, []);

  // Plugin Editor strips keyBindingFn from props; provide it as first plugin so Enter (split-block), Tab, etc. work for lists
  const keyBindingPlugin = useMemo(
    () => ({ keyBindingFn: customKeyBindingFn }),
    [customKeyBindingFn],
  );

  const handleKeyCommand = useCallback(
    (command: EEditorKeyCommand) => {
      if (command === EEditorKeyCommand.Enter && onSubmit) {
        handleSubmit();
        return ECommandState.Handled;
      }
      if (command === EEditorKeyCommand.Tab) {
        const tabEvent = lastTabKeyEventRef.current;
        lastTabKeyEventRef.current = null;
        if (tabEvent) {
          handlePressTab(tabEvent, editorStateRef.current, onChangeRef.current);
          return ECommandState.Handled;
        }
      }
      const newState = RichUtils.handleKeyCommand(editorStateRef.current, command);
      if (newState) {
        onChangeRef.current(newState);
        return ECommandState.Handled;
      }
      return ECommandState.NotHandled;
    },
    [onSubmit, handleSubmit],
  );

  const handlePastedText = useCallback(
    (text: string, html: string | undefined, currentEditorState: EditorState): 'handled' | 'not-handled' => {
      trackAddVideo(text);
      let fallbackText = (text || (html ? stripHtmlToText(html) : '') || '').trim();
      if (fallbackText === '' && isSafari() && lastCopiedPlainTextRef.current) {
        fallbackText = lastCopiedPlainTextRef.current.trim();
      }

      const applyPastedContentState = (contentState: ContentState, stripStyles = false) => {
        let newEditorState = insertSelectedContent(currentEditorState, contentState);
        if (stripStyles && stripPastedFormatting) {
          newEditorState = removeAllExcept(newEditorState, new Set([]), new Set(['variable']));
        }
        setEditorState(newEditorState);
        const stateWithChecklists = cloneChecklist(newEditorState);
        setEditorState(stateWithChecklists);
        const plainText = convertDraftToText(stateWithChecklists.getCurrentContent());
        if (withChecklists && handleChangeChecklists) handleChangeChecklists(prepareChecklistsForAPI(plainText));
        handleChangeProp(plainText);
      };

      // Prefer variable parsing when pasted text contains {{...}} so variables stay as entities
      if (fallbackText && templateVariables.length > 0 && isPastedContentWithVariables(fallbackText)) {
        const contentStateFromText = contentStateFromPastedText(fallbackText, templateVariables);
        if (contentStateFromText) {
          applyPastedContentState(contentStateFromText, stripPastedFormatting ?? false);
          return 'handled';
        }
      }

      // Otherwise prefer HTML from clipboard so bold/italic are preserved when pasting between editors
      const htmlTrimmed = html?.trim();
      if (htmlTrimmed) {
        try {
          const htmlResult = convertFromHTML(htmlTrimmed);
          if (htmlResult?.contentBlocks?.length) {
            const contentStateFromHtml = ContentState.createFromBlockArray(
              htmlResult.contentBlocks,
              htmlResult.entityMap,
            );
            applyPastedContentState(contentStateFromHtml, stripPastedFormatting ?? false);
            return 'handled';
          }
        } catch {
          // Fall through to plain text handling
        }
      }

      if (fallbackText && templateVariables.length > 0) {
        const contentStateFromText = contentStateFromPastedText(fallbackText, templateVariables);
        if (contentStateFromText) {
          applyPastedContentState(contentStateFromText, stripPastedFormatting ?? false);
          return 'handled';
        }
      }
      if (fallbackText === '') return 'handled';
      // Parse pasted text as markdown (bold, italic, variables, mentions) so **text** and *text* are recognized
      try {
        const pastedContentState = getInitialEditorState(
          fallbackText,
          templateVariables ?? [],
          true,
        ).getCurrentContent();
        applyPastedContentState(pastedContentState, false);
      } catch {
        applyPastedContentState(ContentState.createFromText(fallbackText), false);
      }
      return 'handled';
    },
    [stripPastedFormatting, templateVariables, withChecklists, handleChangeChecklists, handleChangeProp],
  );

  const uploadAttachments = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      await handleUploadAttachments(
        e,
        accountId,
        editorStateRef.current,
        attachmentPlugin.addAttachment,
        () => setIsLoading(true),
        async (newState) => {
          await onChangeRef.current(newState);
          setIsLoading(false);
        },
        () => setIsLoading(false),
      );
    },
    [accountId, attachmentPlugin.addAttachment],
  );

  const handleCopy = useCallback((e: React.ClipboardEvent<HTMLInputElement>) => {
    const editorStateToUse = isSafari()
      ? editorStateRef.current
      : (latestEditorStateRef.current ?? editorStateRef.current);
    const selectionToUse = getSelectionExtendedForSafari(editorStateToUse);
    const selectedContentState = getSelectedContentForCopy(editorStateToUse, selectionToUse);
    if (!selectedContentState) return;
    e.preventDefault();
    lastCopiedPlainTextRef.current = writeContentStateToClipboard(selectedContentState, e);
  }, []);

  const onSearchChange = useCallback(({ value }: { value: string }) => {
    setSuggestions(getSuggestionByValue(value, mentions));
  }, [mentions]);

  const focus = useCallback(() => {
    editorRef.current?.focus();
  }, []);

  useImperativeHandle(
    ref,
    () => ({
      focus,
      getEditorState: () => editorStateRef.current,
      onChange: (state: EditorState) => onChangeRef.current(state),
    }),
    [focus],
  );

  const { MentionSuggestions } = mentionPlugin;
  const { Toolbar } = toolbarPlugin;
  const { LinkButton, AddLinkForm } = linkPlugin;
  const { ChecklistButton } = checkableListPlugin;
  const hidePlaceholder = shouldHidePlaceholder(editorState);

  // Explicit blockRenderMap so unordered-list-item and ordered-list-item from Draft.js are always present
  const blockRenderMap = useMemo(
    () =>
      DefaultDraftBlockRenderMap.merge(
        checkableListPlugin.blockRenderMap ?? DefaultDraftBlockRenderMap,
      ),
    [checkableListPlugin.blockRenderMap],
  );

  const plugins = useMemo(
    () =>
      [
        !areSuggestionsOpened && keyBindingPlugin,
        checkableListPlugin,
        linkifyPlugin,
        focusPlugin,
        attachmentPlugin,
        linkPlugin,
        withMentions && mentionPlugin,
        withToolbar && toolbarPlugin,
      ].filter(Boolean),
    [
      areSuggestionsOpened,
      keyBindingPlugin,
      checkableListPlugin,
      linkifyPlugin,
      focusPlugin,
      attachmentPlugin,
      linkPlugin,
      withMentions,
      mentionPlugin,
      withToolbar,
      toolbarPlugin,
    ],
  );

  const withControls = Boolean(onSubmit);

  return (
    <div
      className={classnames(
        styles['editor-wrapper'],
        title && styles['editor-wrapper_with-title'],
        hidePlaceholder && styles['editor-wrapper_hide-placeholder'],
      )}
    >
      {title && <span className={classnames(styles['title'], getForegroundClass(foregroundColor))}>{title}</span>}
      {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions */}
      <div
        ref={editorContainerRef}
        className={classnames(
          styles['editor'],
          isLoading && styles['editor_loading'],
          multiline && styles['editor_multiline'],
          isInTaskDescriptionEditor && styles['editor_task__description-mobile'],
          styles['editor-common'],
          className,
        )}
        onClick={focus}
        onCopyCapture={handleCopy}
      >
        <Loader isLoading={isLoading} />
        <Editor
          ref={editorRef}
          editorState={editorState}
          onChange={onChange}
          plugins={plugins}
          blockRenderMap={blockRenderMap}
          defaultKeyBindings
          defaultKeyCommands
          handleKeyCommand={handleKeyCommand}
          // @ts-ignore
          handlePastedText={handlePastedText}
          decorators={decorators}
          {...props}
        />
        {withMentions && (
          <MentionSuggestions
            onSearchChange={onSearchChange}
            suggestions={suggestions}
            onOpen={() => setAreSuggestionsOpened(true)}
            onClose={() => setAreSuggestionsOpened(false)}
          />
        )}
        <div className={styles['controls-wrapper']}>
          {withToolbar && (
            <EditorToolbar
              Toolbar={Toolbar as unknown as IEditorToolbarProps['Toolbar']}
              LinkButton={LinkButton as unknown as IEditorToolbarProps['LinkButton']}
              ChecklistButton={ChecklistButton as unknown as IEditorToolbarProps['ChecklistButton']}
              isModal={isModal}
              withChecklists={withChecklists}
              uploadAttachments={uploadAttachments}
            />
          )}
          {withControls && (
            <EditorControls
              onSubmit={onSubmit}
              onCancel={onCancel}
              handleSubmit={handleSubmit}
              handleCancel={handleCancel}
              shouldSubmitAfterFileLoaded={shouldSubmitAfterFileLoaded}
              submitIcon={submitIcon}
              cancelIcon={cancelIcon}
            />
          )}
        </div>
        {children}
      </div>
      <AddLinkForm />
    </div>
  );
});
