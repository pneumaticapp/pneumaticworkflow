import type { ReactNode } from 'react';

export interface ITokenListItemAction {
  label: string;
  onClick(): void;
  isDisabled?: boolean;
  tooltip?: string;
  'data-testid'?: string;
}

export interface ITokenListItemProps {
  name: string;
  tokenPrefix: string;
  details?: ReactNode;
  meta?: ReactNode;
  action: ITokenListItemAction;
  'data-testid'?: string;
}

export interface ITokenListItemSkeletonProps {
  'data-testid'?: string;
}
