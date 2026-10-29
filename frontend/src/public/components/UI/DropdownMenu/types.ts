import type { MouseEvent, ReactElement, ReactNode, SVGAttributes } from 'react';

export type TDropdownItemColor = 'black' | 'green' | 'red' | 'orange';

export type TDropdownItemState = 'option' | 'confirmation';

export type TDropdownMenuOption = {
  mapKey?: string;
  label: ReactNode;
  withConfirmation?: boolean;
  initialConfirmationState?: TDropdownItemState;
  withUpperline?: boolean;
  subOptions?: TDropdownMenuOption[] | TDropdownMenuOption;
  customSubOption?: ReactElement;
  color?: TDropdownItemColor;
  isHidden?: boolean;
  isDisabled?: boolean;
  disabledTooltip?: string;
  size?: 'lg' | 'sm';
  className?: string;
  Icon?(props: SVGAttributes<SVGElement>): JSX.Element;
  onClick?(closeDropdown: () => void): void;
};

export interface IDropdownMenuProps {
  options: TDropdownMenuOption[] | TDropdownMenuOption | [];
  direction?: 'right' | 'left';
  className?: string;
  toggleProps?: { [key in string]: string };
  menuClassName?: string;
  renderToggle(isOpen: boolean): ReactNode;
  renderMenuContent?(renderedOptions: ReactNode): ReactNode;
  isFromBreakdownItem?: boolean;
  isDisabled?: boolean;
}

export interface IDropdownMenuPanelProps {
  renderedOptions: ReactNode;
  isOpen: boolean;
  isWide: boolean;
  level: number;
  direction?: 'right' | 'left';
  className?: string;
  renderMenuContent?(renderedOptions: ReactNode): ReactNode;
}

export interface IDropdownSubmenuProps {
  label: ReactNode;
  className?: string;
  toggleClassName?: string;
  renderPanel(isOpen: boolean): ReactNode;
}

export interface IDropdownMenuItemProps {
  option: TDropdownMenuOption;
  isSpaced: boolean;
  closeDropdown(): void;
}

export interface IConfirmableDropdownItemProps {
  children: ReactNode;
  className?: string;
  withConfirmation?: boolean;
  initialConfirmationState?: TDropdownItemState;
  closeDropdown(): void;
  onClick?(event?: MouseEvent<HTMLButtonElement>): void;
}

export type TSubmenuPlacement = { side: 'right' } | { side: 'left' } | { side: 'shifted'; left: number };
