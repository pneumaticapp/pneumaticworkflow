import type { ComponentProps, ReactNode, SVGAttributes } from 'react';
import type ReactSelect from 'react-select';

export type TControlSize = 'lg' | 'sm';
export type TControlVariant = 'muted' | 'accent';
export type TPlacement = 'left' | 'right';

export type TSelectOption = {
  label: string | ReactNode;
  sourceId?: string | null;
  value?: string;
  count?: number;
  searchByText?: string;
  onClick?: () => void;
};

export type TSelectOptionGroup<TOption> = {
  label: string;
  options: TOption[];
};

export interface IControlSMParams {
  title: ReactNode;
  isOpen: boolean;
  isDisabled: boolean;
  variant: TControlVariant;
  className?: string;
  Icon?(props: SVGAttributes<SVGElement>): JSX.Element;
  content?: ReactNode;
  onToggle(isOpen: boolean): void;
  onClear?(): void;
}

export interface ISelectProps<TOption extends TSelectOption> extends Omit<
  ComponentProps<typeof ReactSelect>,
  'options' | 'onChange'
> {
  label?: string;
  options: TOption[] | TSelectOptionGroup<TOption>[];
  title?: ReactNode;
  controlSize?: TControlSize;
  className?: string;
  staticMenu?: boolean;
  placement?: TPlacement;
  onChange?: (value: any, action: any) => void;
  errorMessage?: string;
  isRequired?: boolean;
  controlVariant?: TControlVariant;
  controlClassName?: string;
  controlContent?: ReactNode;
  Icon?(props: SVGAttributes<SVGElement>): JSX.Element;
  onClear?(): void;
}
