import React, {
  forwardRef,
  useCallback,
  useImperativeHandle,
  useRef,
  useState,
} from 'react';
import classnames from 'classnames';
import type { EditorState, LexicalEditor } from 'lexical';
import {
  $createParagraphNode,
  $createTextNode,
  $getRoot,
  $getSelection,
  $insertNodes,
  $isRangeSelection,
  $isTextNode,
} from 'lexical';
import { LexicalComposer } from '@lexical/react/LexicalComposer';

import { EditorHeader } from './components/EditorHeader';
import { useAttachmentUpload, usePasteUpload } from './hooks';
import type { IRichEditorHandle, IRichEditorProps } from './types';
import { lexicalTheme } from './theme';
import { LEXICAL_NODES } from './nodes';
import { applyMarkdownToEditor, convertLexicalToMarkdown } from './converters';
import { prepareChecklistsForAPI } from '../../utils/checklists/prepareChecklistsForAPI';
import { LinkPluginProvider } from './plugins';
import { LexicalEditorContent } from './components/LexicalEditorContent/LexicalEditorContent';
import { $createVariableNode } from './nodes/VariableNode';
import { resolveUploadHandler } from './utils/resolveUploadHandler';

import styles from './RichEditor.css';



export const RichEditor = forwardRef<
  IRichEditorHandle,
  IRichEditorProps
>(function RichEditor(
  {
    className,
    withChecklists = false,
    withToolbar = true,
    withMentions = true,
    title,
    children,
    multiline = true,
    foregroundColor = 'white',
    handleChange,
    handleChangeChecklists,
    accountId,
    mentions,
    defaultValue,
    isModal,
    isInTaskDescriptionEditor,
    templateVariables,
    onUploadAttachments: onUploadAttachmentsProp,
    placeholder = '',
    onSubmit,
    onCancel,
    submitIcon,
    cancelIcon,
  },
  ref,
) {
  const editorRef = useRef<LexicalEditor | null>(null);
  const editorContainerRef = useRef<HTMLDivElement | null>(null);
  const templateVariablesRef = useRef(templateVariables);
  templateVariablesRef.current = templateVariables;

  const initialConfig = {
    namespace: 'RichEditor',
    theme: lexicalTheme,
    nodes: LEXICAL_NODES,
    onError: (error: Error) => {
      console.error('❌ Error loading markdown into editor:', error);
    },
    editorState:
      defaultValue != null && defaultValue.trim() !== ''
        ? (editor: LexicalEditor) => {
          applyMarkdownToEditor(editor, defaultValue, {
            tag: 'history-merge',
            templateVariables: templateVariablesRef.current,
          });
        }
        : undefined,
  };

  const [isUploading, setIsUploading] = useState(false);

  const rawUpload = useAttachmentUpload(editorRef, accountId);
  const builtInUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      setIsUploading(true);
      try {
        await rawUpload(e);
      } finally {
        setIsUploading(false);
      }
    },
    [rawUpload],
  );

  const rawPasteUpload = usePasteUpload(editorRef, accountId);
  const onPasteFiles = useCallback(
    async (files: File[]) => {
      setIsUploading(true);
      try {
        await rawPasteUpload(files);
      } finally {
        setIsUploading(false);
      }
    },
    [rawPasteUpload],
  );

  const onUploadAttachments = resolveUploadHandler(
    onUploadAttachmentsProp,
    accountId != null ? builtInUpload : undefined,
  );

  const onChange = (editorState: EditorState): void => {
    const markdown = convertLexicalToMarkdown(editorState);

    if (handleChangeChecklists) {
      const checklistsData = prepareChecklistsForAPI(markdown);
      handleChangeChecklists(checklistsData);
    }

    handleChange(markdown);
  };

  const insertVariableToEditor = (
    apiName: string,
    variableTitle: string,
    subtitle: string,
  ): void => {
    const editor = editorRef.current;
    if (!editor) return;

    editor.update(() => {
      const selection = $getSelection();
      if (!$isRangeSelection(selection)) return;

      const variableNode = $createVariableNode({
        apiName,
        title: variableTitle,
        subtitle,
      });

      const needSpace = ((): boolean => {
        if (!selection.isCollapsed()) return true;
        const {anchor} = selection;
        const node = anchor.getNode();
        if ($isTextNode(node)) {
          const text = node.getTextContent();
          if (anchor.offset < text.length && text[anchor.offset] === ' ') return false;
        }
        const nextNode = node.getNextSibling();
        if (nextNode && $isTextNode(nextNode) && nextNode.getTextContent().startsWith(' ')) {
          return false;
        }
        return true;
      })();

      if (needSpace) {
        $insertNodes([variableNode, $createTextNode(' ')]);
        const after = variableNode.getNextSibling();
        if (after && $isTextNode(after)) after.selectEnd();
        else variableNode.selectNext();
      } else {
        $insertNodes([variableNode]);
        variableNode.selectNext();
      }
    });
  };

  const clearContent = useCallback((): void => {
    const editor = editorRef.current;
    if (!editor) return;
    editor.update(() => {
      const root = $getRoot();
      root.clear();
      const paragraph = $createParagraphNode();
      root.append(paragraph);
      paragraph.selectStart();
    });
  }, []);

  useImperativeHandle(
    ref,
    () => ({
      focus(): void {
        editorRef.current?.focus();
      },
      insertVariable(apiName: string, variableTitle: string, subtitle: string): void {
        if (!apiName?.trim() || !variableTitle?.trim() || !subtitle?.trim()) return;
        insertVariableToEditor(apiName, variableTitle, subtitle);
      },
      getEditor(): LexicalEditor | undefined {
        return editorRef.current ?? undefined;
      },
      clearContent,
    }),
    [insertVariableToEditor, clearContent],
  );



  return (
    <div
      data-testid="rich-editor-root"
      className={classnames(
        styles['lexical-wrapper'],
        isInTaskDescriptionEditor && styles['lexical-wrapper_in-task-description-editor'],
        title && styles['lexical-wrapper_with-title'],
        multiline && styles['lexical-wrapper_multiline'],
        className,
      )}
    >
      <EditorHeader title={title} foregroundColor={foregroundColor} />
      <LexicalComposer initialConfig={initialConfig}>
        <LinkPluginProvider editorContainerRef={editorContainerRef}>
          <LexicalEditorContent
            placeholder={placeholder}
            multiline={multiline}
            withToolbar={withToolbar}
            withMentions={withMentions}
            mentions={mentions}
            isModal={isModal}
            isUploading={isUploading}
            onUploadAttachments={onUploadAttachments}
            onPasteFiles={accountId != null ? onPasteFiles : undefined}
            editorRef={editorRef}
            editorContainerRef={editorContainerRef}
            onChange={onChange}
            withChecklists={withChecklists}
            onSubmit={onSubmit}
            onCancel={onCancel}
            submitIcon={submitIcon}
            cancelIcon={cancelIcon}
            withControls={Boolean(onSubmit)}
          />
        </LinkPluginProvider>
      </LexicalComposer>
      {children}
    </div>
  );
});
