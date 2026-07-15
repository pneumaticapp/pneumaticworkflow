import { useCallback, useEffect, useRef, useState } from 'react';
import type { MouseEvent } from 'react';
import { useDispatch } from 'react-redux';

import { setContainerClassnames } from '../../redux/actions';
import type { IMenuItem, IMenuItemSub } from '../../types/menu';
import { history } from '../../utils/history';
import { findAncestor } from '../../utils/helpers';

import type { IUseSidebarNavigationProps, IUseSidebarNavigationResult } from './types';

const getCurrentMenuItem = (menuItems: IMenuItem[], pathname: string): IMenuItemSub | null => {
  return menuItems.reduce<IMenuItemSub | null>((selectedItem, item) => {
    if (selectedItem) {
      return selectedItem;
    }

    const selectedSubItem = item.subs?.find(
      (subItem) => subItem.to === pathname || pathname.startsWith(subItem.to),
    );

    if (selectedSubItem) {
      return selectedSubItem;
    }

    return item.to === pathname || pathname.startsWith(item.to) ? item : null;
  }, null);
};

export const useSidebarNavigation = ({
  containerClassnames,
  menuHiddenBreakpoint,
  menuItems,
}: IUseSidebarNavigationProps): IUseSidebarNavigationResult => {
  const dispatch = useDispatch();
  const [activeItemId, setActiveItemId] = useState<IMenuItemSub['id'] | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const isMobile = menuHiddenBreakpoint > window.innerWidth;
  const isMenuVisible = containerClassnames.includes('main-show-temporary');
  const isMenuHidden = containerClassnames.includes('main-hidden');

  const closeMenu = useCallback(() => {
    dispatch(setContainerClassnames(2, containerClassnames, true));
  }, [containerClassnames, dispatch]);

  const handleCloseMenu = useCallback(() => {
    if (!isMenuHidden || isMenuVisible) {
      closeMenu();
    }
  }, [closeMenu, isMenuHidden, isMenuVisible]);

  const handleOpenMenu = () => {
    if (isMenuHidden && !isMobile) {
      dispatch(setContainerClassnames(3, containerClassnames, true));
    }
  };

  const handleMobileMenuToggle = (event: MouseEvent<HTMLElement>) => {
    event.preventDefault();

    if (isMenuHidden) {
      dispatch(setContainerClassnames(3, containerClassnames, true));
    }

    if (!isMenuHidden || isMenuVisible) {
      closeMenu();
    }
  };

  const handleDocumentClick = useCallback(
    (event: Event) => {
      if (!event.target) {
        return;
      }

      const target = event.target as HTMLElement;
      const isSidebarClicked = Boolean(findAncestor(target, 'sidebar') || findAncestor(target, 'menu-button-mobile'));
      const parent = findAncestor(target, 'nav');
      const isMenuItemClicked = Boolean(parent && !parent.classList.contains('list-unstyled'));

      if (isMenuItemClicked || !isSidebarClicked) {
        requestAnimationFrame(handleCloseMenu);
      }
    },
    [handleCloseMenu],
  );

  useEffect(() => {
    const updateSelectedMenuItem = () => {
      setActiveItemId(getCurrentMenuItem(menuItems, history.location.pathname)?.id || null);
    };

    document.addEventListener('click', handleDocumentClick, true);
    document.addEventListener('popstate', handleDocumentClick, true);
    const unregisterHistoryListener = history.listen(updateSelectedMenuItem);
    updateSelectedMenuItem();

    return () => {
      document.removeEventListener('click', handleDocumentClick, true);
      document.removeEventListener('popstate', handleDocumentClick, true);
      unregisterHistoryListener();
    };
  }, [handleDocumentClick, menuItems]);

  return {
    activeItemId,
    closeMenu,
    containerRef,
    handleCloseMenu,
    handleMobileMenuToggle,
    handleOpenMenu,
    isMobile,
  };
};
