import React, {
  forwardRef,
  useImperativeHandle,
  useRef,
  useMemo,
  useEffect,
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
import { $getRoot, $createParagraphNode, $createTextNode } from 'lexical';
import { LEXICAL_NODES } from '../nodes';
import { lexicalTheme } from '../theme';
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

function InitialContentPlugin({ defaultValue }: { defaultValue?: string }): null {
  const [editor] = useLexicalComposerContext();
  useEffect(() => {
    if (!defaultValue?.trim()) return;
    editor.update(
      () => {
        const root = $getRoot();
        if (root.getChildrenSize() > 0) return;
        const paragraph = $createParagraphNode();
        paragraph.append($createTextNode(defaultValue.trim()));
        root.append(paragraph);
      },
      { tag: 'history-merge' },
    );
  }, [editor, defaultValue]);
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
      editorState.read(() => {
        const root = $getRoot();
        const text = root.getTextContent();
        handleChange(text);
        handleChangeChecklists?.([]);
      });
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
    }),
    [],
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
        <InitialContentPlugin defaultValue={defaultValue} />
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
