import type { Location } from 'history';
import type { ReactNode } from 'react';

export interface IRouteLeavingGuardProps {
  when?: boolean;
  title: string;
  message: string;
  onConfirm: (path: string) => void;
  onReject: (path: string) => void;
  shouldBlockNavigation: (location: Location) => boolean;
  renderControlls(confirm: () => void, reject: () => void): ReactNode;
}

export type TGuardState = 'confirmed' | 'rejected' | 'none';
