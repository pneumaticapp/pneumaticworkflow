import type { MouseEvent } from 'react';
import type { TTaskVariable } from '../../../types/template';

export interface IVariableListProps {
  variables: TTaskVariable[];
  className?: string;
  tooltipText: string;
  onVariableClick(apiName: string): (e: MouseEvent) => void;
  focusEditor(): void;
}
