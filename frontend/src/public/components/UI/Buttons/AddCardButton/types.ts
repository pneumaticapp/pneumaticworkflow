import { ReactNode, MouseEvent } from 'react';

export interface IAddCardButtonProps {
  title: ReactNode;
  caption: ReactNode;
  icon: ReactNode;
  onClick?: (e?: MouseEvent) => void;
  to?: string;
  className?: string;
  testId?: string;
}
