import type { IMenuItem } from '../../types/menu';

export interface IMenu {
  items: IMenuItem[];
  containerClassnames: string;
  subHiddenBreakpoint: number;
  menuHiddenBreakpoint: number;
  menuClickCount: number;
  selectedMenuHasSubItems: boolean;
}
