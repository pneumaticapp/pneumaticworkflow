import type { ChangeEvent, MouseEvent, ReactNode } from 'react';

export interface IEditorToolbarProps {
  isModal?: boolean;
  withChecklists?: boolean;
  onUploadAttachments?: (e: ChangeEvent<HTMLInputElement>) => Promise<void>;
}

export type TListType = 'bullet' | 'number' | null;

export interface IToolbarState {
  isBold: boolean;
  isItalic: boolean;
  listType: TListType;
  isLink: boolean;
}

export interface IToolbarButtonProps {
  isActive: boolean;
  tooltipText: string;
  ariaLabel: string;
  isModal?: boolean;
  onMouseDown: (e: MouseEvent<HTMLButtonElement>) => void;
  children: ReactNode;
}

export interface IAttachmentToolbarButtonProps {
  tooltipText: string;
  ariaLabel: string;
  accept?: string;
  multiple?: boolean;
  isModal?: boolean;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  children: ReactNode;
}
