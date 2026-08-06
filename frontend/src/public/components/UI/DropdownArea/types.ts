import { ReactNode } from 'react';
import { Placement } from '@popperjs/core';

export interface IDropdownAreaProps {
  children: ReactNode;
  title?: string;
  containerClassName?: string;
  toggle?: ReactNode;
  placement?: Placement;
  onOpen?(): void;
  onClose?(): void;
}

export interface IDropdownAreaHandle {
  updateDropdownPosition(): void;
  closeDropdown(): void;
}

export type DropdownAreaHandle = IDropdownAreaHandle;
