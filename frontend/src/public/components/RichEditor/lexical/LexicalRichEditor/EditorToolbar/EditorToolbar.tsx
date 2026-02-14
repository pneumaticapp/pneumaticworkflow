import React, { useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { FORMAT_TEXT_COMMAND } from 'lexical';
import {
  INSERT_ORDERED_LIST_COMMAND,
  INSERT_UNORDERED_LIST_COMMAND,
} from '@lexical/list';
import { TOGGLE_LINK_COMMAND } from '@lexical/link';

import {
  BoldButtonIcon,
  ItalicButtonIcon,
  OrderedListButtonIcon,
  UnorderedListButtonIcon,
  LinkButtonIcon,
  ImageAttachmentButtonIcon,
  VideoAttachmentButtonIcon,
  FileAttachmentButtonIcon,
  ChecklistIcon,
} from '../../../../icons';
import { INSERT_CHECKLIST_COMMAND } from '../../plugins/ChecklistPlugin';
import { useCheckDevice } from '../../../../../hooks/useCheckDevice';
import { useLinkPlugin } from '../../plugins/LinkPlugin';
import { useToolbarState } from './useToolbarState';
import { ToolbarButton } from './ToolbarButton';
import { AttachmentToolbarButton } from './AttachmentToolbarButton';
import { TOOLBAR_LABELS, ATTACHMENT_ACCEPT } from './constants';
import type { IEditorToolbarProps } from './types';

import styles from './EditorToolbar.css';



export function EditorToolbar({
  withChecklists,
  isModal,
  onUploadAttachments,
}: IEditorToolbarProps): React.ReactElement {
  const [editor] = useLexicalComposerContext();
  const { isMobile } = useCheckDevice();
  const { openLinkForm } = useLinkPlugin();
  const { isBold, isItalic, listType, isLink } = useToolbarState(editor);
  const linkButtonRef = useRef<HTMLButtonElement>(null);

  const applyBold = () => editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'bold');
  const applyItalic = () => editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'italic');
  const applyOrderedList = () => editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined);
  const applyUnorderedList = () => editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined);
  const applyChecklist = () => editor.dispatchCommand(INSERT_CHECKLIST_COMMAND, undefined);

  const toggleLink = () => {
    if (isLink) {
      editor.dispatchCommand(TOGGLE_LINK_COMMAND, null);
      return;
    }
    const nativeSelection = window.getSelection();
    const isCollapsed = nativeSelection?.isCollapsed ?? true;
    const range = nativeSelection?.rangeCount ? nativeSelection.getRangeAt(0) : null;
    const rect = range?.getBoundingClientRect?.() ?? null;
    const mode = isCollapsed ? 'create-link-from-scratch' : 'create-link-at-selection';
    openLinkForm(rect, mode, linkButtonRef);
  };

  const handleAttachmentUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onUploadAttachments) await onUploadAttachments(e);
  };

  const formatButtons = [
    { Icon: BoldButtonIcon, labels: TOOLBAR_LABELS.bold, isActive: isBold, onMouseDown: applyBold, ref: undefined },
    { Icon: ItalicButtonIcon, labels: TOOLBAR_LABELS.italic, isActive: isItalic, onMouseDown: applyItalic, ref: undefined },
    {
      Icon: OrderedListButtonIcon,
      labels: TOOLBAR_LABELS.orderedList,
      isActive: listType === 'number',
      onMouseDown: applyOrderedList,
      ref: undefined,
    },
    {
      Icon: UnorderedListButtonIcon,
      labels: TOOLBAR_LABELS.unorderedList,
      isActive: listType === 'bullet',
      onMouseDown: applyUnorderedList,
      ref: undefined,
    },
    { Icon: LinkButtonIcon, labels: TOOLBAR_LABELS.link, isActive: isLink, onMouseDown: toggleLink, ref: linkButtonRef },
    ...(withChecklists
      ? [{ Icon: ChecklistIcon, labels: TOOLBAR_LABELS.checklist, isActive: false, onMouseDown: applyChecklist, ref: undefined }]
      : [])
  ];

  const allAttachmentButtons = [
    {
      Icon: ImageAttachmentButtonIcon,
      labels: TOOLBAR_LABELS.attachImage,
      accept: ATTACHMENT_ACCEPT.image,
      attachmentType: 'image' as const,
    },
    {
      Icon: VideoAttachmentButtonIcon,
      labels: TOOLBAR_LABELS.attachVideo,
      accept: ATTACHMENT_ACCEPT.video,
      attachmentType: 'video' as const,
    },
    {
      Icon: FileAttachmentButtonIcon,
      labels: TOOLBAR_LABELS.attachFile,
      accept: undefined,
      attachmentType: 'file' as const,
    },
  ];

  const attachmentButtons = isMobile
    ? allAttachmentButtons.filter((btn) => btn.attachmentType === 'file')
    : allAttachmentButtons;

  return (
    <div className={styles['toolbar-wrapper']}>
      <div
        className={styles['toolbar']}
        role="toolbar"
        tabIndex={-1}
        onMouseDown={(e: React.MouseEvent<HTMLDivElement>) => e.preventDefault()}
        onKeyDown={(e: React.KeyboardEvent<HTMLDivElement>) => e.preventDefault()}
      >
        {!isMobile && (
          <>
            <div className={styles['toolbar-format']}>
              {formatButtons.map(({ Icon, labels, isActive, onMouseDown, ref: btnRef }) => (
                <ToolbarButton
                  key={labels.aria}
                  ref={btnRef}
                  isActive={isActive}
                  tooltipText={labels.tooltip}
                  ariaLabel={labels.aria}
                  isModal={isModal}
                  onMouseDown={onMouseDown}
                >
                  <Icon />
                </ToolbarButton>
              ))}
            </div>
            <div className={styles['separator']} aria-hidden />
          </>
        )}
        {attachmentButtons.map(({ Icon, labels, accept }) => (
          <AttachmentToolbarButton
            key={labels.aria}
            tooltipText={labels.tooltip}
            ariaLabel={labels.aria}
            accept={accept}
            isModal={isModal}
            onFileChange={handleAttachmentUpload}
          >
            <Icon />
          </AttachmentToolbarButton>
        ))}
      </div>
    </div>
  );
}
