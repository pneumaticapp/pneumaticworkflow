import { ComponentProps, ReactNode } from 'react';
import Select from 'react-select';

export type TControlSize = 'lg' | 'sm';
export type TPlacement = 'left' | 'right';

export type TDropdownOptionBase = {
  label: string | ReactNode;
  sourceId?: string | null;
  value?: string;
  onClick?: () => void;
};

export interface IDropdownListProps<TOption extends TDropdownOptionBase>
  extends Omit<ComponentProps<typeof Select>, 'options' | 'onChange'> {
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

export interface IDropdownOptionProps {
  label: ReactNode;
  isSelected?: boolean;
  withTooltip?: boolean;
  className?: string;
}
