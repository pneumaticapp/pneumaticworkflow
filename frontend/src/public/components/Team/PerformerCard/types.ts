import type { ReactNode } from 'react';

import type { TDropdownOption } from '../../UI';

export interface IPerformerCardToggle {
  label: string;
  isChecked: boolean;
  isDisabled?: boolean;
  onChange(isChecked: boolean): void;
}

export interface IPerformerCardProps {
  avatar: ReactNode;
  name: ReactNode;
  nameBadge?: string;
  description?: ReactNode;
  badge?: string;
  toggle?: IPerformerCardToggle;
  options?: TDropdownOption[];
  'data-testid'?: string;
}
