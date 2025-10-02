import { IApplicationState } from '../../types/redux';
import { IMenuItem } from '../../types/menu';

export const getMenu = (state: IApplicationState): IMenuItem[] => state.menu.items;
