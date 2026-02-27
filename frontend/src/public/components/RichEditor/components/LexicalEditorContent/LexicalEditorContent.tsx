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
  SubmitOnKeyPlugin,
  LinkTooltipPlugin,
  VariableTooltipPlugin,
  ChecklistPlugin,
  MentionsPlugin,
  PasteAttachmentPlugin,
} from '../../plugins';
import { EditorControls } from '../EditorControls/EditorControls';
import { EditorToolbar } from '../EditorToolbar/EditorToolbar';
import { Loader } from '../../../UI/Loader';
import type { ILexicalEditorContentProps } from '../../types';

import styles from './LexicalEditorContent.css';



export function LexicalEditorContent({
  placeholder = '',
  withChecklists,
  multiline,
  withToolbar,
  withMentions,
  mentions,
  isModal,
  isUploading,
  onUploadAttachments,
  onPasteFiles,
  editorRef,
  editorContainerRef,
  onChange,
  onSubmit,
  onCancel,
  submitIcon,
  cancelIcon,
  withControls = false,
}: ILexicalEditorContentProps): React.ReactElement {
  const showMentions = withMentions && Boolean(mentions?.length);

  return (
    <div
      ref={editorContainerRef as React.RefObject<HTMLDivElement>}
      className={classnames(
        styles['editor'],
        multiline && styles['editor-multiline'],
        isUploading && styles['editor-uploading'],
      )}
    >
      <Loader isLoading={isUploading} />
      <RichTextPlugin
        contentEditable={
          <ContentEditable
            className={styles['content-editable']}
            aria-placeholder={placeholder}
            data-testid="rich-editor-contenteditable"
            placeholder={<div className={styles['placeholder']}>{placeholder}</div>}
          />
        }
        ErrorBoundary={LexicalErrorBoundary}
      />
      {(withToolbar || withControls) && (
        <div className={styles['controls-wrapper']}>
          {withToolbar && (
            <EditorToolbar
              withChecklists={withChecklists}
              isModal={isModal}
              onUploadAttachments={onUploadAttachments}
            />
          )}
          {withControls && onSubmit && (
            <EditorControls
              onSubmit={onSubmit}
              onCancel={onCancel}
              handleSubmit={onSubmit}
              handleCancel={onCancel ?? (() => {})}
              shouldSubmitAfterFileLoaded={false}
              submitIcon={submitIcon}
              cancelIcon={cancelIcon}
            />
          )}
        </div>
      )}

      <HistoryPlugin />
      <ListPlugin />
      <SetEditorRefPlugin editorRef={editorRef} />
      {withControls && onSubmit ? (
        <SubmitOnKeyPlugin onSubmit={onSubmit} />
      ) : null}
      <OnChangePlugin onChange={onChange} />
      <MarkdownShortcutPlugin transformers={ELEMENT_TRANSFORMERS} />

      <LinkPlugin />
      <LinkTooltipPlugin />
      <VariableTooltipPlugin />
      {withChecklists && <ChecklistPlugin />}
      <InsertAttachmentPlugin />
      {onPasteFiles ? (
        <PasteAttachmentPlugin onPasteFiles={onPasteFiles} />
      ) : null}
      {showMentions && mentions ? <MentionsPlugin mentions={mentions} /> : null}
    </div>
  );
}
