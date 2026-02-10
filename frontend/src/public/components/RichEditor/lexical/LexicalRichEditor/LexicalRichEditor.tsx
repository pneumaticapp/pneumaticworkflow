import React, {
  forwardRef,
  useImperativeHandle,
  useRef,
} from 'react';
import classnames from 'classnames';
import type { EditorState, LexicalEditor } from 'lexical';
import {
  $createTextNode,
  $getSelection,
  $insertNodes,
  $isRangeSelection,
  $isTextNode,
} from 'lexical';
import { LexicalComposer } from '@lexical/react/LexicalComposer';

import { LinkPluginProvider } from '../plugins';
import { $createVariableNode } from '../nodes/VariableNode';
import { applyMarkdownToEditor, convertLexicalToMarkdown } from '../converters';
import { prepareChecklistsForAPI } from '../../../../utils/checklists/prepareChecklistsForAPI';
import { EditorHeader } from './EditorHeader';
import { LexicalEditorContent } from './LexicalEditorContent/LexicalEditorContent';
import { useAttachmentUpload } from './hooks';
import type { ILexicalRichEditorHandle, ILexicalRichEditorProps } from './types';
import { lexicalTheme } from '../theme';
import { LEXICAL_NODES } from '../nodes';

import styles from './LexicalRichEditor.css';



export const EDITOR_NAMESPACE = 'LexicalRichEditor';

function resolveUploadHandler(
  propHandler: ILexicalRichEditorProps['onUploadAttachments'],
  builtInHandler?: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>,
): ILexicalRichEditorProps['onUploadAttachments'] {
  return propHandler ?? builtInHandler ?? undefined;
}

export const LexicalRichEditor = forwardRef<
  ILexicalRichEditorHandle,
  ILexicalRichEditorProps
>(function LexicalRichEditor(
  {
    foregroundColor = 'white',
    placeholder,
    className,
    title,
    multiline = true,
    defaultValue,
    handleChange,
    handleChangeChecklists,
    withToolbar = false,
    withMentions = false,
    mentions,
    templateVariables,
    isModal,
    accountId,
    onUploadAttachments: onUploadAttachmentsProp,
    children,
  },
  ref,
) {
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
      const spaceNode = $createTextNode(' ');

      $insertNodes([variableNode, spaceNode]);
      const nodeAfterVariable = variableNode.getNextSibling();
      if (nodeAfterVariable && $isTextNode(nodeAfterVariable)) {
        nodeAfterVariable.selectEnd();
      } else {
        variableNode.selectNext();
      }
    });
  };

  useImperativeHandle(
    ref,
    () => ({
      focus(): void {
        editorRef.current?.focus();
      },
      insertVariable(apiName, variableTitle, subtitle): void {
        if (!apiName?.trim() || !variableTitle?.trim() || !subtitle?.trim()) return;
        insertVariableToEditor(apiName, variableTitle, subtitle);
      },
      getEditor(): LexicalEditor | undefined {
        return editorRef.current ?? undefined;
      },
    }),
    [insertVariableToEditor],
  );



  return (
    <div className={classnames(
      styles['lexical-wrapper'],
      title && styles['lexical-wrapper_with-title'],
      multiline && styles['lexical-wrapper_multiline'],
      className,
    )}>
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
          />
        </LinkPluginProvider>
      </LexicalComposer>
      {children}
    </div>
  );
});
