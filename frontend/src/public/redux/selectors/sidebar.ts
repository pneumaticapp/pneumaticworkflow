import { createSelector } from 'reselect';

import type { IApplicationState } from '../../types/redux';
import { getUserPendingActions } from './user';

const getMenu = ({ menu }: IApplicationState) => menu;
const getAuthUser = ({ authUser }: IApplicationState) => authUser;

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
