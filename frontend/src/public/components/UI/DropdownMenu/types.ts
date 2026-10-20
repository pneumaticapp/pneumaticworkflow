import type { ReactElement, ReactNode, SVGAttributes } from 'react';

import type { TDropdownItemState } from './ConfirmableDropdownItem';

export type TDropdownItemColor = 'black' | 'green' | 'red' | 'orange';

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
  /** Passes reactstrap DropdownMenu `positionFixed` so Popper uses fixed positioning (escapes overflow scroll). */
  menuPositionFixed?: boolean;
  /** Passes reactstrap DropdownMenu `container` (portal target), e.g. `document.body`. */
  menuContainer?: string | HTMLElement;
  renderToggle(isOpen: boolean): ReactNode;
  renderMenuContent?(renderedOptions: ReactNode): ReactNode;
  CustomDropdownMenu?(props: IDropdownMenuPanelProps): JSX.Element;
  isFromBreakdownItem?: boolean;
  isDisabled?: boolean;
}

export interface IDropdownMenuPanelProps {
  renderedOptions: ReactNode;
  isWide: boolean;
  level: number;
  direction?: 'right' | 'left';
  className?: string;
  renderMenuContent?(renderedOptions: ReactNode): ReactNode;
  positionFixed?: boolean;
  container?: string | HTMLElement;
}
