import { useCallback, useEffect, useState } from 'react';
import type { MouseEvent } from 'react';
import { useDispatch } from 'react-redux';

import { setContainerClassnames } from '../../redux/actions';
import type { IMenuItem } from '../../types/menu';
import { history } from '../../utils/history';
import { findAncestor } from '../../utils/helpers';

import type { IUseSidebarNavigationProps, IUseSidebarNavigationResult } from './types';

const isViewportMobile = (menuHiddenBreakpoint: number) => menuHiddenBreakpoint > window.innerWidth;

export const getCurrentMenuItem = (menuItems: IMenuItem[], pathname: string): IMenuItem | null => {
  const parentWithActiveSubItem = menuItems.find((item) =>
    item.subs?.some((subItem) => subItem.to === pathname || pathname.startsWith(subItem.to)),
  );

  if (parentWithActiveSubItem) {
    return parentWithActiveSubItem;
  }

  const matchingItems = menuItems.filter((item) => item.to === pathname || pathname.startsWith(item.to));

  return matchingItems.sort((firstItem, secondItem) => secondItem.to.length - firstItem.to.length)[0] ?? null;
};

export const useSidebarNavigation = ({
  containerClassnames,
  menuHiddenBreakpoint,
  menuItems,
}: IUseSidebarNavigationProps): IUseSidebarNavigationResult => {
  const dispatch = useDispatch();
  const [activeItemId, setActiveItemId] = useState<IMenuItem['id'] | null>(null);
  const [isMobile, setIsMobile] = useState(() => isViewportMobile(menuHiddenBreakpoint));
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
    if (isMenuHidden && !isViewportMobile(menuHiddenBreakpoint)) {
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
    const updateViewportMode = () => {
      setIsMobile(isViewportMobile(menuHiddenBreakpoint));
    };

    updateViewportMode();
    window.addEventListener('resize', updateViewportMode);

    return () => {
      window.removeEventListener('resize', updateViewportMode);
    };
  }, [menuHiddenBreakpoint]);

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
    handleCloseMenu,
    handleMobileMenuToggle,
    handleOpenMenu,
    isMobile,
  };
};
