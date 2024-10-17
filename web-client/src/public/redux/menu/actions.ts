/* eslint-disable */
/* prettier-ignore */
import * as classNames from 'classnames';
import { IMenu, ITypedReduxAction } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { IMenuItem } from '../../types/menu';
import { TMenuCounter } from '../../constants/menu';

export const enum EMenuActions {
  GenerateMenu = 'GENERATE_MENU',
  SetMenuItems = 'SET_MENU_ITEMS',
  MergeMenuItems = 'MERGE_MENU_ITEMS',
  SetMenuItemCounter = 'SET_MENU_ITEM_COUNTER',
  UpdateMenu = 'UPDATE_MENU',
  SetClassnames = 'MENU_SET_CLASSNAMES',
  ContainerAddClassname = 'MENU_CONTAINER_ADD_CLASSNAME',
  ChangeDefaultClasses = 'MENU_CHANGE_DEFAULT_CLASSES',
  ChangeHasSubItemStatus = 'MENU_CHANGE_HAS_SUB_ITEM_STATUS',
}

export type TGenerateMenu = ITypedReduxAction<EMenuActions.GenerateMenu, void>;
export const generateMenu: (payload?: void) => TGenerateMenu = actionGenerator<EMenuActions.GenerateMenu, void>(
  EMenuActions.GenerateMenu,
);

export type TSetMenuItems = ITypedReduxAction<EMenuActions.SetMenuItems, IMenuItem[]>;
export const setMenuItems: (payload: IMenuItem[]) => TSetMenuItems = actionGenerator<
  EMenuActions.SetMenuItems,
  IMenuItem[]
>(EMenuActions.SetMenuItems);

export type TMergeMenuItems = ITypedReduxAction<EMenuActions.MergeMenuItems, IMenuItem[]>;
export const mergeMenuItems: (payload: IMenuItem[]) => TMergeMenuItems = actionGenerator<
  EMenuActions.MergeMenuItems,
  IMenuItem[]
>(EMenuActions.MergeMenuItems);

export type TSetMenuItemCounter = ITypedReduxAction<EMenuActions.SetMenuItemCounter, TMenuCounter>;
export const setMenuItemCounter: (payload: TMenuCounter) => TSetMenuItemCounter = actionGenerator<
  EMenuActions.SetMenuItemCounter,
  TMenuCounter
>(EMenuActions.SetMenuItemCounter);

export type TChangeSubItemStatus = ITypedReduxAction<EMenuActions.ChangeHasSubItemStatus, boolean>;
export const changeSelectedMenuHasSubItems: (payload: boolean) => TChangeSubItemStatus = actionGenerator<
  EMenuActions.ChangeHasSubItemStatus,
  boolean
>(EMenuActions.ChangeHasSubItemStatus);

export type TChangeDefaultClasses = ITypedReduxAction<EMenuActions.ChangeDefaultClasses, string>;
export const changeDefaultClassnames: (payload: string) => TChangeDefaultClasses = actionGenerator<
  EMenuActions.ChangeDefaultClasses,
  string
>(EMenuActions.ChangeDefaultClasses);

export type TContainerAddClassname = ITypedReduxAction<EMenuActions.ContainerAddClassname, string>;
export const addContainerClass: (payload: string) => TContainerAddClassname = actionGenerator<
  EMenuActions.ContainerAddClassname,
  string
>(EMenuActions.ContainerAddClassname);

export type TClassnamesPayload = Pick<IMenu, 'containerClassnames' | 'menuClickCount'>;

export type TSetClassnames = ITypedReduxAction<EMenuActions.SetClassnames, TClassnamesPayload>;
export const setClassnames: (payload: TClassnamesPayload) => TSetClassnames = actionGenerator<
  EMenuActions.SetClassnames,
  TClassnamesPayload
>(EMenuActions.SetClassnames);

export const addContainerClassname = (classname: string, currentClassname: string) =>
  addContainerClass(classNames(currentClassname, classname));

export const clickOnMobileMenu = (strCurrentClasses: string) => {
  const currentClasses = strCurrentClasses
    ? strCurrentClasses.split(' ').filter((x) => x !== '' && x !== 'sub-show-temporary')
    : [''];
  let nextClasses = '';
  if (currentClasses.includes('main-show-temporary')) {
    nextClasses = currentClasses.filter((x) => x !== 'main-show-temporary').join(' ');
  } else {
    nextClasses = currentClasses.join(' ') + ' main-show-temporary';
  }

  return setClassnames({ containerClassnames: nextClasses, menuClickCount: 0 });
};

export const setContainerClassnames = (index: number, strCurrentClasses: string, hasSubItems: boolean) => {
  let clickIndex = index;
  const currentClasses = strCurrentClasses ? strCurrentClasses.split(' ').filter(Boolean) : '';
  let nextClasses = '';
  if (!hasSubItems) {
    if (currentClasses.includes('menu-default') && (clickIndex % 4 === 0 || clickIndex % 4 === 3)) {
      clickIndex = 1;
    }
    if (currentClasses.includes('menu-sub-hidden') && clickIndex % 4 === 2) {
      clickIndex = 0;
    }
    if (currentClasses.includes('menu-hidden') && (clickIndex % 4 === 2 || clickIndex % 4 === 3)) {
      clickIndex = 0;
    }
  }

  if (clickIndex === 1 && !currentClasses.includes('menu-mobile')) {
    nextClasses = 'menu-default sub-hidden';

    return setClassnames({ containerClassnames: nextClasses, menuClickCount: clickIndex });
  }

  if (clickIndex % 4 === 0) {
    if (currentClasses.includes('menu-default') && currentClasses.includes('menu-sub-hidden')) {
      nextClasses = 'menu-default menu-sub-hidden';
    } else if (currentClasses.includes('menu-default')) {
      nextClasses = 'menu-default';
    } else if (currentClasses.includes('menu-sub-hidden')) {
      nextClasses = 'menu-sub-hidden';
    } else if (currentClasses.includes('menu-hidden')) {
      nextClasses = 'menu-hidden';
    }
    clickIndex = 0;
  } else if (clickIndex % 4 === 1) {
    if (currentClasses.includes('menu-default') && currentClasses.includes('menu-sub-hidden')) {
      nextClasses = 'menu-default menu-sub-hidden main-hidden sub-hidden';
    } else if (currentClasses.includes('menu-default')) {
      nextClasses = 'menu-default sub-hidden main-hidden';
    } else if (currentClasses.includes('menu-sub-hidden')) {
      nextClasses = 'menu-sub-hidden main-hidden sub-hidden';
    } else if (currentClasses.includes('menu-hidden')) {
      nextClasses = 'menu-hidden main-show-temporary';
    }
  } else if (clickIndex % 4 === 2) {
    if (currentClasses.includes('menu-default') && currentClasses.includes('menu-sub-hidden')) {
      nextClasses = 'menu-default menu-sub-hidden sub-hidden';
    } else if (currentClasses.includes('menu-default')) {
      nextClasses = 'menu-default main-hidden sub-hidden';
    } else if (currentClasses.includes('menu-sub-hidden')) {
      nextClasses = 'menu-sub-hidden sub-hidden';
    } else if (currentClasses.includes('menu-hidden')) {
      nextClasses = 'menu-hidden main-show-temporary sub-show-temporary';
    }
  } else if (clickIndex % 4 === 3) {
    if (currentClasses.includes('menu-default') && currentClasses.includes('menu-sub-hidden')) {
      nextClasses = 'menu-default menu-sub-hidden sub-show-temporary';
    } else if (currentClasses.includes('menu-default')) {
      nextClasses = 'menu-default sub-hidden';
    } else if (currentClasses.includes('menu-sub-hidden')) {
      nextClasses = 'menu-sub-hidden sub-show-temporary';
    } else if (currentClasses.includes('menu-hidden')) {
      nextClasses = 'menu-hidden main-show-temporary';
    }
  }
  if (currentClasses.includes('menu-mobile')) {
    nextClasses += ' menu-mobile';
  }

  return setClassnames({ containerClassnames: nextClasses, menuClickCount: clickIndex });
};

export type TMenuActions =
  | TGenerateMenu
  | TSetMenuItems
  | TMergeMenuItems
  | TSetMenuItemCounter
  | TChangeSubItemStatus
  | TChangeDefaultClasses
  | TContainerAddClassname
  | TSetClassnames;
