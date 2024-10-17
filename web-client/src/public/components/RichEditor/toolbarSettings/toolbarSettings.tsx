/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
// tslint:disable-next-line: no-implicit-dependencies
import { StaticToolbarPluginConfig } from '@draft-js-plugins/static-toolbar';

import {
  BoldButtonIcon,
  ItalicButtonIcon,
  OrderedListButtonIcon,
  UnorderedListButtonIcon,
  ImageAttachmentButtonIcon,
  VideoAttachmentButtonIcon,
  FileAttachmentButtonIcon,
} from '../../icons';
import { createInlineStyleButton } from './utils/createInlineStyleButton';
import { createAttachmentButton } from './utils/createAttachmentButton';
import { createBlockStyleButton } from './utils/createBlockStyleButton';

import { EEditorBlock, EEditorStyle } from '../utils/types';

import toolbarStyles from './Toolbar.css';
import buttonStyles from './ButtonStyles.css';

export const toolbarConfig: StaticToolbarPluginConfig = {
  theme: { buttonStyles, toolbarStyles },
};

export const BoldButton = createInlineStyleButton({
  style: EEditorStyle.Bold,
  tooltipText: 'editor.bold',
  children: <BoldButtonIcon />,
});

export const ItalicButton = createInlineStyleButton({
  style: EEditorStyle.Italic,
  tooltipText: 'editor.italic',
  children: <ItalicButtonIcon />,
});

export const OrderedListButton = createBlockStyleButton({
  blockType: EEditorBlock.OrderedListItem,
  tooltipText: 'Ordered List',
  children: <OrderedListButtonIcon />,
});

export const UnorderedListButton = createBlockStyleButton({
  blockType: EEditorBlock.UnorderedListItem,
  tooltipText: 'Unordered List',
  children: <UnorderedListButtonIcon />,
});

export const ImageAttachmentButton = createAttachmentButton({
  attachmentType: 'image',
  tooltipText: 'Attach Image',
  children: <ImageAttachmentButtonIcon />,
});

export const VideoAttachmentButton = createAttachmentButton({
  attachmentType: 'video',
  tooltipText: 'Attach Video',
  children: <VideoAttachmentButtonIcon />,
});

export const FileAttachmentButton = createAttachmentButton({
  attachmentType: 'file',
  tooltipText: 'Attach File',
  children: <FileAttachmentButtonIcon />,
});

export function Separator() {
  return <div className={toolbarStyles['separator']}/>;
}
