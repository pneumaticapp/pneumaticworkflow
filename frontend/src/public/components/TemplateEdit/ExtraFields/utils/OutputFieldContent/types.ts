import type { ReactElement, ReactNode } from 'react';
import type { IExtraField } from '../../../../../types/template';

export interface IOutputFieldContentProps {
  field: IExtraField;
  editField: (changedProps: Partial<IExtraField>) => void;
  isDisabled?: boolean;
  datasetName?: string;
  className?: string;
  children?: ReactNode;
}

export interface ITruncatedTooltipProps {
  label?: string | ReactNode;
  containerClassName: string;
  children: ReactElement;
  trigger?: string;
  delay?: number | [number, number];
}
