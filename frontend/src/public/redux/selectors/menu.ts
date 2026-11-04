import type { IApplicationState } from '../store';
import { IMenuItem } from '../../types/menu';

export const getMenu = (state: IApplicationState): IMenuItem[] => state.menu.items;
