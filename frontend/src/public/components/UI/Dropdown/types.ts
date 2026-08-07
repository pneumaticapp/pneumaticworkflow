import { ButtonHTMLAttributes, ReactElement, ReactNode, Ref, SVGAttributes } from 'react';
import { Placement } from '@popperjs/core';

export type TDropdownItemState = 'option' | 'confirmation';
export type TDropdownItemColor = 'black' | 'green' | 'red' | 'orange';

export type TDropdownOption = {
  mapKey?: string;
  label: ReactNode;
  withConfirmation?: boolean;
  initialConfirmationState?: TDropdownItemState;
  withUpperline?: boolean;
  subOptions?: TDropdownOption[] | TDropdownOption;
  customSubOption?: ReactElement;
  color?: TDropdownItemColor;
  isHidden?: boolean;
  size?: 'lg' | 'sm';
  className?: string;
  Icon?(props: SVGAttributes<SVGElement>): JSX.Element;
  onClick?(closeDropdown: () => void): void;
};

export interface IDropdownRenderProps {
  closeDropdown(): void;
}

export interface IDropdownOptionsProps {
  options: TDropdownOption[] | TDropdownOption;
  closeDropdown(): void;
  isFromBreakdownItem?: boolean;
}

export interface IDropdownProps {
  options?: TDropdownOption[] | TDropdownOption;
  children?: ReactNode | ((props: IDropdownRenderProps) => ReactNode);
  direction?: 'right' | 'left';
  placement?: Placement;
  className?: string;
  toggleProps?: Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children' | 'onClick' | 'disabled'> & {
    'data-test-id'?: string;
  };
  menuClassName?: string;
  menuPositionFixed?: boolean;
  menuContainer?: string | HTMLElement;
  renderToggle(isOpen: boolean): ReactNode;
  renderMenuContent?(renderedOptions: ReactNode): ReactNode;
  isFromBreakdownItem?: boolean;
  isDisabled?: boolean;
  onOpen?(): void;
  onClose?(): void;
  dropdownRef?: Ref<IDropdownHandle>;
}

export interface IDropdownHandle {
  updateDropdownPosition(): void;
  closeDropdown(): void;
}

export interface IConfirmableDropdownItemProps {
  children: ReactNode;
  className?: string;
  withConfirmation?: boolean;
  initialConfirmationState?: TDropdownItemState;
  closeDropdown(): void;
  onClick?(): void;
  cssModule?: { 'dropdown-item'?: string };
  toggle?: boolean;
  tag?: string;
}
