import { ReactNode } from 'react';

export type OutsideClickHandlerDisplay = 'block' | 'flex' | 'inline' | 'inline-block' | 'contents';

export interface IOutsideClickHandlerProperties {
  children: ReactNode;
  onOutsideClick: (event: MouseEvent) => void;
  disabled?: boolean;
  useCapture?: boolean;
  display?: OutsideClickHandlerDisplay;
}
