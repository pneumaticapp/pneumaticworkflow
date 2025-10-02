/* eslint-disable */
/* prettier-ignore */
import { EMenuActions, TMenuActions } from './actions';
import { defaultMenuType } from '../../constants/defaultValues';
import { IMenu } from '../../types/redux';
import merge from 'lodash.merge';

const { DESKTOP_MIN_WIDTH_BREAKPOINT, SUB_HIDDEN_BREAKPOINT } = require('../../constants/breakpoints');

const INIT_STATE: IMenu = {
  items: [],
  containerClassnames: 'menu-default main-hidden sub-hidden',
  subHiddenBreakpoint: SUB_HIDDEN_BREAKPOINT,
  menuHiddenBreakpoint: DESKTOP_MIN_WIDTH_BREAKPOINT,
  menuClickCount: 0,
  /* if you use menu-sub-hidden as default menu type, set value of this variable to false */
  selectedMenuHasSubItems: defaultMenuType === 'menu-default',
};

export const reducer = (state: IMenu = INIT_STATE, action: TMenuActions) => {
  switch (action.type) {
    case EMenuActions.SetMenuItems: {
      return { ...state, items: action.payload };
    }
    case EMenuActions.MergeMenuItems: {
      const newItems = merge(state.items, action.payload);

      return { ...state, items: newItems };
    }
    case EMenuActions.SetMenuItemCounter: {
      const newItems = state.items.map((item) => {
        return item.id === action.payload.id
          ? { ...item, counter: action.payload.value, counterType: action.payload.type }
          : item;
      });

      return { ...state, items: newItems };
    }
    case EMenuActions.ChangeHasSubItemStatus:
      return {
        ...state,
        selectedMenuHasSubItems: action.payload,
      };

    case EMenuActions.SetClassnames:
      return {
        ...state,
        containerClassnames: action.payload.containerClassnames,
        menuClickCount: action.payload.menuClickCount,
      };

    case EMenuActions.ContainerAddClassname:
      return {
        ...state,
        containerClassnames: action.payload,
      };

    case EMenuActions.ChangeDefaultClasses:
      return {
        ...state,
        containerClassnames: action.payload,
      };

    default:
      return { ...state };
  }
};
