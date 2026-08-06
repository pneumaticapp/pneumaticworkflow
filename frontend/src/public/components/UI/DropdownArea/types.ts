import { ReactNode } from 'react';
import { Placement } from '@popperjs/core';

import { IDropdownHandle } from '../Dropdown';

export interface IDropdownAreaProps {
  children: ReactNode;
  title?: string;
  containerClassName?: string;
  toggle?: ReactNode;
  placement?: Placement;
  onOpen?(): void;
  onClose?(): void;
}

export type DropdownAreaHandle = IDropdownHandle;
