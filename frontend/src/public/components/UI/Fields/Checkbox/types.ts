import { HTMLProps, ReactNode } from 'react';

export type TCheckboxTriState = 'checked' | 'empty' | 'indeterminate';

export interface ICheckboxProps {
  title?: ReactNode;
  titlePosition?: 'external';
  isRequired?: boolean;
  containerClassName?: string;
  labelClassName?: string;
  titleClassName?: string;
  triState?: TCheckboxTriState;
  checkboxId?: string;
}

export type TCheckboxProps = ICheckboxProps &
  Pick<HTMLProps<HTMLInputElement>, 'checked' | 'disabled' | 'onChange' | 'id' | 'onClick' | 'readOnly'>;
