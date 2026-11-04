import type { RootState } from '../store';
import { IMenuItem } from '../../types/menu';

export const getMenu = (state: RootState): IMenuItem[] => state.menu.items;
