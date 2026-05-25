import * as React from 'react';
import { ReactElement, ReactNode } from 'react';
import { IExtraField } from '../../../../../types/template';

export interface IOutputFieldContentProps {
  field: IExtraField;
  editField: (changedProps: Partial<IExtraField>) => void;
  isDisabled?: boolean;
  datasetName?: string;
  children?: React.ReactNode;
}

export interface ITruncatedTooltipProps {
  label?: string | ReactNode;
  containerClassName: string;
  children: ReactElement;
  trigger?: string;
  delay?: number | [number, number];
}
