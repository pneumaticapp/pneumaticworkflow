import type { RootState } from '../store';
import type { IMenuItem } from '../../types/menu';

export const getMenu = (state: RootState): IMenuItem[] => state.menu.items;
