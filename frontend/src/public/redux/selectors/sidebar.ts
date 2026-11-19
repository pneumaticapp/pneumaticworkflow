import { createSelector } from 'reselect';

import type { RootState } from '../store';
import { getUserPendingActions } from './user';

const getMenu = ({ menu }: RootState) => menu;
const getAuthUser = ({ authUser }: RootState) => authUser;

export const getSidebarState = createSelector(
  getMenu,
  getAuthUser,
  getUserPendingActions,
  ({ containerClassnames, items: menuItems, menuHiddenBreakpoint }, authUser, pendingActions) => ({
    authUser,
    containerClassnames,
    menuHiddenBreakpoint,
    menuItems,
    pendingActions,
  }),
);
