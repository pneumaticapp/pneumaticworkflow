import * as React from 'react';
import { ReactElement, ReactNode } from 'react';
import { IExtraField } from '../../../../../types/template';

export enum ESourceMode {
  Custom = 'custom',
  Dataset = 'dataset',
}

export interface IDatasetOption {
  label: string;
  value: string;
}

export interface IDatasetSourceToggleProps {
  field: IExtraField;
  editField: (changedProps: Partial<IExtraField>) => void;
  isDisabled?: boolean;
  children?: React.ReactNode;
}

export interface ITruncatedTooltipProps {
  label?: string | ReactNode;
  containerClassName: string;
  children: ReactElement;
  trigger?: string;
  delay?: number | [number, number];
}
