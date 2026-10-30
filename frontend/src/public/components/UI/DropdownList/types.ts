import * as React from 'react';
import Select from 'react-select';

export type TControlSize = 'lg' | 'sm';
export type TPlacement = 'left' | 'right';

export type TDropdownOptionBase = {
  label: string | React.ReactNode;
  sourceId?: string | null;
  value?: string;
  onClick?: () => void;
};

export interface IDropdownListProps<TOption extends TDropdownOptionBase> extends Omit<
  React.ComponentProps<typeof Select>,
  'options' | 'onChange'
> {
  label?: string;
  options: TOption[];
  title?: string;
  controlSize?: TControlSize;
  className?: string;
  staticMenu?: boolean;
  placement?: TPlacement;
  onChange?: (value: any, action: any) => void;
  errorMessage?: string;
  isRequired?: boolean;
}
