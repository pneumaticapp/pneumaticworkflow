import React, {
  forwardRef,
  useImperativeHandle,
  useRef,
  useMemo,
  useCallback,
} from 'react';
import classnames from 'classnames';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { LexicalErrorBoundary } from '@lexical/react/LexicalErrorBoundary';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import type { EditorState, LexicalEditor } from 'lexical';
import { LEXICAL_NODES } from '../nodes';
import { lexicalTheme } from '../theme';
import { convertLexicalToMarkdown, applyMarkdownToEditor } from '../converters';
import { prepareChecklistsForAPI } from '../../../../utils/checklists/prepareChecklistsForAPI';
import type { ILexicalRichEditorHandle, ILexicalRichEditorProps } from './types';
import styles from './LexicalRichEditor.css';

function onError(error: Error): void {
  console.error('[LexicalRichEditor]', error);
}

function SetEditorRefPlugin({
  editorRef,
}: {
  editorRef: React.MutableRefObject<LexicalEditor | null>;
}): null {
  const [editor] = useLexicalComposerContext();
  editorRef.current = editor;
  return null;
}

export const LexicalRichEditor = forwardRef<
  ILexicalRichEditorHandle,
  ILexicalRichEditorProps
>(function LexicalRichEditor(
  {
    placeholder,
    className,
    title,
    multiline = true,
    defaultValue,
    handleChange,
    handleChangeChecklists,
    children,
  },
  ref,
) {
  const editorRef = useRef<LexicalEditor | null>(null);

  const onChange = useCallback(
    (editorState: EditorState) => {
      const markdown = convertLexicalToMarkdown(editorState);
      if (handleChangeChecklists) {
        handleChangeChecklists(prepareChecklistsForAPI(markdown));
      }
      handleChange(markdown);
    },
    [handleChange, handleChangeChecklists],
  );

  useImperativeHandle(
    ref,
    () => ({
      focus(): void {
        editorRef.current?.focus();
      },
      insertVariable(): void {
        // Stub until stage 4
      },
      getEditor(): LexicalEditor | undefined {
        return editorRef.current ?? undefined;
      },
    }),
    [],
  );

  const initialConfig = useMemo(
    () => ({
      namespace: 'LexicalRichEditor',
      theme: lexicalTheme,
      nodes: LEXICAL_NODES,
      onError,
      editorState:
        defaultValue != null && defaultValue.trim() !== ''
          ? (editor: LexicalEditor) => {
            applyMarkdownToEditor(editor, defaultValue, { tag: 'history-merge' });
          }
          : undefined,
    }),
    [defaultValue],
  );

  return (
    <div className={classnames(styles.wrapper, className)}>
      {title ? (
        <div className={styles.title} aria-hidden>
          {title}
        </div>
      ) : null}
      <LexicalComposer initialConfig={initialConfig}>
        <SetEditorRefPlugin editorRef={editorRef} />
        <OnChangePlugin onChange={onChange} />
        <div
          className={classnames(styles.editor, multiline && styles['editor-multiline'])}
        >
          <RichTextPlugin
            contentEditable={
              <ContentEditable
                className={styles['content-editable']}
                aria-placeholder={placeholder}
                placeholder={<div className={styles.placeholder}>{placeholder}</div>}
              />
            }
            placeholder={
              <div className={styles.placeholder}>{placeholder}</div>
            }
            ErrorBoundary={LexicalErrorBoundary}
          />
          <HistoryPlugin />
        </div>
      </LexicalComposer>
      {children}
    </div>
  );
});
