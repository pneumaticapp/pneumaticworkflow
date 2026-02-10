import React from 'react';
import classnames from 'classnames';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { LexicalErrorBoundary } from '@lexical/react/LexicalErrorBoundary';
import { LinkPlugin } from '@lexical/react/LexicalLinkPlugin';
import { ListPlugin } from '@lexical/react/LexicalListPlugin';
import { MarkdownShortcutPlugin } from '@lexical/react/LexicalMarkdownShortcutPlugin';
import { ELEMENT_TRANSFORMERS } from '@lexical/markdown';

import {
  InsertAttachmentPlugin,
  SetEditorRefPlugin,
  LinkTooltipPlugin,
  VariableTooltipPlugin,
  ChecklistPlugin,
  MentionsPlugin,
} from '../../plugins';
import { EditorToolbar } from '../EditorToolbar/EditorToolbar';
import type { ILexicalEditorContentProps } from '../types';

import styles from './LexicalEditorContent.css';



export function LexicalEditorContent({
  placeholder,
  multiline,
  withToolbar,
  withMentions,
  mentions,
  isModal,
  onUploadAttachments,
  editorRef,
  editorContainerRef,
  onChange,
}: ILexicalEditorContentProps): React.ReactElement {
  const showMentions = withMentions && Boolean(mentions?.length);

  return (
    <div
      ref={editorContainerRef as React.RefObject<HTMLDivElement>}
      className={classnames(styles['editor'], multiline && styles['editor-multiline'])}
    >
      <RichTextPlugin
        contentEditable={
          <ContentEditable
            className={styles['content-editable']}
            aria-placeholder={placeholder}
            placeholder={<div className={styles['placeholder']}>{placeholder}</div>}
          />
        }
        ErrorBoundary={LexicalErrorBoundary}
      />
      {withToolbar && <EditorToolbar isModal={isModal} onUploadAttachments={onUploadAttachments} />}

      <HistoryPlugin />
      <ListPlugin />
      <SetEditorRefPlugin editorRef={editorRef} />
      <OnChangePlugin onChange={onChange} />
      <MarkdownShortcutPlugin transformers={ELEMENT_TRANSFORMERS} />

      <LinkPlugin />
      <LinkTooltipPlugin />
      <VariableTooltipPlugin />
      <ChecklistPlugin />
      <InsertAttachmentPlugin />
      {showMentions && mentions ? <MentionsPlugin mentions={mentions} /> : null}
    </div>
  );
}
