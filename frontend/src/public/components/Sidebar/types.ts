import type { MouseEvent, ReactElement } from 'react';
import type { IntlShape } from 'react-intl';

import type { ESubscriptionPlan } from '../../types/account';
import type { IMenuItem, IMenuItemSub } from '../../types/menu';
import type { IAuthUser } from '../../types/redux';

export interface ISidebarRibbonProps {
  formatMessage: IntlShape['formatMessage'];
  leaseLevel: IAuthUser['account']['leaseLevel'];
  plan: ESubscriptionPlan;
  trialIsActive: boolean;
}

export interface ISidebarMenuProps {
  activeItemId: IMenuItem['id'] | null;
  containerClassnames: string;
  isMobile: boolean;
  menuItems: IMenuItem[];
  plan: ESubscriptionPlan;
  onCloseMenu(): void;
  onRunWorkflow(): void;
}

export interface IDesktopMenuItemProps {
  active: boolean;
  containerClassnames: string;
  item: IMenuItem;
  plan: ESubscriptionPlan;
}

export interface ISubMenuTooltipProps {
  children: ReactElement;
  containerClassName: string;
  menuItems: IMenuItemSub[];
  plan?: ESubscriptionPlan;
}

export interface IUseSidebarNavigationProps {
  containerClassnames: string;
  menuHiddenBreakpoint: number;
  menuItems: IMenuItem[];
}

export interface IUseSidebarNavigationResult {
  activeItemId: IMenuItem['id'] | null;
  closeMenu(): void;
  containerRef: { current: HTMLDivElement | null };
  handleCloseMenu(): void;
  handleMobileMenuToggle(event: MouseEvent<HTMLElement>): void;
  handleOpenMenu(): void;
  isMobile: boolean;
}
