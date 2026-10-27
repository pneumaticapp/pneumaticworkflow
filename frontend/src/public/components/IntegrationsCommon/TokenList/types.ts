import type { ReactNode } from 'react';

export interface ITokenListItemProps {
  name: string;
  tokenPrefix: string;
  details?: ReactNode;
  meta?: ReactNode;
  action: ReactNode;
  'data-testid'?: string;
}

export interface ITokenListSkeletonProps {
  'data-testid'?: string;
}
