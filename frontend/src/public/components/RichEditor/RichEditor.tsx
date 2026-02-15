import React, {
  forwardRef,
  useCallback,
  useImperativeHandle,
  useRef,
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
import { useAttachmentUpload } from './hooks';
import type { IRichEditorHandle, IRichEditorProps } from './types';
import { lexicalTheme } from './theme';
import { LEXICAL_NODES } from './nodes';
import { applyMarkdownToEditor, convertLexicalToMarkdown } from './converters';
import { prepareChecklistsForAPI } from '../../utils/checklists/prepareChecklistsForAPI';
import { LinkPluginProvider } from './plugins';
import { LexicalEditorContent } from './components/LexicalEditorContent/LexicalEditorContent';
import { $createVariableNode } from './nodes/VariableNode';

import styles from './RichEditor.css';



export const EDITOR_NAMESPACE = 'RichEditor';

function resolveUploadHandler(
  propHandler: IRichEditorProps['onUploadAttachments'],
  builtInHandler?: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>,
): IRichEditorProps['onUploadAttachments'] {
  return propHandler ?? builtInHandler ?? undefined;
}

export const RichEditor = forwardRef<
  IRichEditorHandle,
  IRichEditorProps
>(function RichEditor(
  {
    className,
    withChecklists,
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
  const withControls = Boolean(onSubmit);
  const editorRef = useRef<LexicalEditor | null>(null);
  const editorContainerRef = useRef<HTMLDivElement | null>(null);
  const templateVariablesRef = useRef(templateVariables);
  templateVariablesRef.current = templateVariables;

  const initialConfig = {
    namespace: EDITOR_NAMESPACE,
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

  const builtInUpload = useAttachmentUpload(editorRef, accountId);
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
            onUploadAttachments={onUploadAttachments}
            editorRef={editorRef}
            editorContainerRef={editorContainerRef}
            onChange={onChange}
            withChecklists={withChecklists}
            onSubmit={onSubmit}
            onCancel={onCancel}
            submitIcon={submitIcon}
            cancelIcon={cancelIcon}
            withControls={withControls}
          />
        </LinkPluginProvider>
      </LexicalComposer>
      {children}
    </div>
  );
});
