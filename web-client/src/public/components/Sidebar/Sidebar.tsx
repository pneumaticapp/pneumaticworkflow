/* eslint-disable */
/* prettier-ignore */
import React, { useEffect, useState } from 'react';
import { RouteComponentProps } from 'react-router-dom';
import * as classnames from 'classnames';
import PerfectScrollbar from 'react-perfect-scrollbar';
import { IntlShape } from 'react-intl';

import { ERoutes } from '../../constants/routes';
import { IntlMessages } from '../IntlMessages';
import { RibbonTail } from '../icons';

import { IAuthUser, IMenu } from '../../types/redux';
import { ESubscriptionPlan } from '../../types/account';
import { IMenuItem } from '../../types/menu';

import { setContainerClassnames, openSelectTemplateModal } from '../../redux/actions';
import { LogoContainer } from '../Logo';
import { checkHasTopBar } from '../TopNav/utils/checkHasTopBar';

import { NavLink } from '../NavLink';
import { SubMenuTooltip } from './SubMenuItemTooltip';
import { MobileMenuItem } from './MobileMenuItem';
import { StartProcessButton } from './StartProcessButton';
import { SidebarMenuItemCounter } from './SidebarMenuItemCounter';

import { history } from '../../utils/history';
import { findAncestor } from '../../utils/helpers';
import { EPlanActions } from '../../utils/getPlanPendingActions';

import styles from './Sidebar.css';

export interface ISidebarProps extends IMenu {
  containerClassnames: string;
  menuItems: IMenuItem[];
  authUser: IAuthUser;
  intl: IntlShape;
  pendingActions: EPlanActions[];
  menuHiddenBreakpoint: number;
}

export interface ISidebarDispatchProps {
  setContainerClassnames: typeof setContainerClassnames;
  openSelectTemplateModal: typeof openSelectTemplateModal;
  showPlanExpiredMessage(): void;
}

export type TSidebarProps = ISidebarProps & ISidebarDispatchProps & RouteComponentProps;

export function Sidebar({
  containerClassnames,
  menuItems,
  authUser: {
    account: { isBlocked, billingPlan: plan, leaseLevel, trialIsActive },
    isSupermode,
  },
  intl: { formatMessage },
  pendingActions,
  menuHiddenBreakpoint,
  setContainerClassnames,
  openSelectTemplateModal,
  showPlanExpiredMessage,
}: TSidebarProps) {
  let [active, setActive] = useState<string | null>(null);
  let [isSubMenuActiveState, setIsSubMenuActiveState] = useState(Array(menuItems.length).fill(false));

  let container: HTMLDivElement | null;

  const extraSpace = checkHasTopBar(Boolean(isBlocked), plan, Boolean(isSupermode));
  const statusClassesMap = {
    [ESubscriptionPlan.Unknown]: styles['sidebar_free'],
    [ESubscriptionPlan.Free]: styles['sidebar_free'],
    [ESubscriptionPlan.Trial]: styles['sidebar_trial'],
    [ESubscriptionPlan.Premium]: styles['sidebar_premium'],
    [ESubscriptionPlan.Unlimited]: styles['sidebar_premium'],
    [ESubscriptionPlan.FractionalCOO]: styles['sidebar_premium'],
  };

  const isMobile = () => menuHiddenBreakpoint > window.innerWidth;

  const closeMenu = () => {
    setContainerClassnames(2, containerClassnames, true);
  };

  const openMenu = () => {
    setContainerClassnames(3, containerClassnames, true);
  };

  const isMenuVisible = () => containerClassnames.includes('main-show-temporary');

  const isMenuHidden = () => containerClassnames.includes('main-hidden');

  const getCurrentMenuItem = (menu: IMenuItem[], to: string): IMenuItem | null => {
    let result = null;

    for (let item of menu) {
      if (result) {
        break;
      }
      if (item.subs) {
        result = getCurrentMenuItem(item.subs, to);
      }
      if (!result && (item.to === to || to.startsWith(item.to))) {
        result = item;
      }
    }

    return result;
  };

  const getParent = (menu: IMenuItem[], id: IMenuItem['id'], parentId?: string): string => {
    let result = null;

    for (let item of menu) {
      if (!result && item.subs) {
        result = getParent(item.subs, id, item.id);
      }
      if (parentId && item.id === id) {
        result = parentId || id;
      }
    }

    return result || '';
  };

  const isItemActive = (item: IMenuItem) => item.id === active;

  const renderIcon = (item: IMenuItem) => {
    const { iconComponent: IconComponent, icon } = item;

    if (!IconComponent && !icon) {
      return null;
    }

    const component = (IconComponent && <IconComponent />) || <i className={item.icon} />;

    return <>{component} </>;
  };

  const handleRunWorkflow = () => {
    if (pendingActions.includes(EPlanActions.ChoosePlan)) {
      showPlanExpiredMessage();

      return;
    }
    openSelectTemplateModal();
  };

  const handleDocumentClick = React.useCallback((e: Event) => {
    if (!e.target) {
      return;
    }

    const target = e.target as HTMLElement;
    const isSidebarClicked = Boolean(findAncestor(target, 'sidebar') || findAncestor(target, 'menu-button-mobile'));
    const parent = findAncestor(target, 'nav');
    const isMenuItemClicked = !!parent && !parent.classList.contains('list-unstyled');
    let isMenuClick = false;
    isMenuClick = Boolean(findAncestor(target, 'menu-button') || findAncestor(target, 'menu-button-mobile'));

    if (isMenuItemClicked || !isSidebarClicked) {
      requestAnimationFrame(handleCloseMenu);

      return;
    }

    if ((container && container.contains(target)) || container === target || isMenuClick) {
      return;
    }
  }, []);

  const handleCloseMenu = () => {
    if (!isMenuHidden() || isMenuVisible()) {
      closeMenu();
    }
  };

  const handleOpenMenu = () => {
    if (isMenuHidden() && !isMobile()) {
      openMenu();
    }
  };

  const handleMobileMenuToggle = (e: React.MouseEvent<HTMLElement>) => {
    e.preventDefault();

    if (isMenuHidden()) {
      openMenu();
    }
    if (!isMenuHidden() || isMenuVisible()) {
      closeMenu();
    }
  };

  const handleopenSubMenu = (index: number) => {
    let updateArray = isSubMenuActiveState;
    updateArray.splice(index, 1, true);
    setIsSubMenuActiveState([...updateArray]);
  };

  const handleCloseSubMenu = (index: number) => {
    let updateArray = isSubMenuActiveState;
    updateArray.splice(index, 1, false);
    setIsSubMenuActiveState([...updateArray]);
  };

  useEffect(() => {
    const updateSelectedMenuItem = (menuItems: IMenuItem[]) => {
      const selectedItem = getCurrentMenuItem(menuItems, history.location.pathname);
      setActive(selectedItem?.id || null);
    };

    document.addEventListener('click', handleDocumentClick, true);
    document.addEventListener('popstate', handleDocumentClick, true);

    const unregisterHistoryListener = history.listen(() => {
      updateSelectedMenuItem(menuItems);
    });

    updateSelectedMenuItem(menuItems);

    return () => {
      document.removeEventListener('click', handleDocumentClick, true);
      document.removeEventListener('popstate', handleDocumentClick, true);
      unregisterHistoryListener();
    };
  }, [menuItems]);

  const renderRibbonLabel = () => {
    if (leaseLevel === 'partner') {
      return <span className={styles['sidebar-ribbon__label']}>{formatMessage({ id: 'sidebar.ribbon-partner' })}</span>;
    }

    const statusLabelsMap = {
      [ESubscriptionPlan.Unknown]: formatMessage({ id: 'sidebar.ribbon-free' }),
      [ESubscriptionPlan.Free]: formatMessage({ id: 'sidebar.ribbon-free' }),
      [ESubscriptionPlan.Trial]: formatMessage({ id: 'sidebar.ribbon-trial' }),
      [ESubscriptionPlan.Premium]: formatMessage({ id: 'sidebar.ribbon-premium' }),
      [ESubscriptionPlan.Unlimited]: formatMessage({ id: 'sidebar.ribbon-unlimited' }),
      [ESubscriptionPlan.FractionalCOO]: formatMessage({ id: 'sidebar.ribbon-premium' }),
    };

    if (leaseLevel === 'tenant') {
      return (
        <span className={styles['sidebar-ribbon__label']}>
          {trialIsActive ? formatMessage({ id: 'sidebar.ribbon-trial' }) : statusLabelsMap[plan]}
        </span>
      );
    }

    return (
      <span className={styles['sidebar-ribbon__label']}>
        {trialIsActive ? formatMessage({ id: 'sidebar.ribbon-trial' }) : statusLabelsMap[plan]}
      </span>
    );
  };

  return (
    <div
      ref={(node) => (container = node)}
      className={classnames(
        'sidebar',
        styles['sidebar'],
        trialIsActive ? styles['sidebar_trial'] : statusClassesMap[plan],
        leaseLevel === 'partner' && styles['sidebar_partner'],
      )}
      onMouseOver={handleOpenMenu}
      onMouseLeave={handleCloseMenu}
    >
      <NavLink
        aria-label="Go to Dashboard"
        tabIndex={1}
        to={ERoutes.Main}
        onClick={handleMobileMenuToggle}
        className={classnames(styles['logo-mobile'], extraSpace && styles['logo__extra-space'])}
      >
        <LogoContainer
          className={classnames('active', styles['logo'])}
          size="sm"
          theme={plan === ESubscriptionPlan.Free ? 'dark' : 'light'}
        />
        <RibbonTail className={styles['sidebar-ribbon-tail']} />
      </NavLink>
      <div className={classnames('main-menu', styles['sidebar_menu'], extraSpace && styles['menu__extra-space'])}>
        <NavLink tabIndex={1} to={ERoutes.Main} className={styles['logo-desktop']}>
          <LogoContainer
            size="md"
            className={classnames('active', styles['logo'])}
            theme={plan === ESubscriptionPlan.Free ? 'dark' : 'light'}
          />
        </NavLink>

        <div className={styles['sidebar-ribbon']}>
          {renderRibbonLabel()}
          <RibbonTail className={styles['sidebar-ribbon-tail']} />
        </div>

        <PerfectScrollbar
          options={{ suppressScrollX: true, wheelPropagation: false }}
          className={styles['menu-wrapper']}
        >
          <ul className={classnames(styles['menu-wrapper__list'])}>
            {menuItems &&
              menuItems.map((item, index) => {
                if (item.isHidden) {
                  return null;
                }

                if (isMobile()) {
                  return (
                    <MobileMenuItem
                      key={`MobileMenuItem${index}`}
                      tabIndex={1}
                      item={item}
                      renderIcon={renderIcon}
                      active={isItemActive(item)}
                      handleCloseMenu={closeMenu}
                    />
                  );
                }

                return (
                  <li
                    key={item.id}
                    onMouseOver={
                      item.subs &&
                      (() => {
                        handleopenSubMenu(index);
                      })
                    }
                    onMouseLeave={
                      item.subs &&
                      (() => {
                        handleCloseSubMenu(index);
                      })
                    }
                    id={item.id}
                    className={classnames(styles['nav-item'], isItemActive(item) && 'active')}
                  >
                    {item.subs && (
                      <SubMenuTooltip
                        containerClassName={containerClassnames}
                        onCloseSubmenu={() => handleCloseSubMenu(index)}
                        plan={plan}
                        isOpen={isSubMenuActiveState[index]}
                        target={item.id}
                        menuItems={item.subs}
                      />
                    )}

                    {item.newWindow ? (
                      <a
                        tabIndex={1}
                        href={item.to}
                        rel="noopener noreferrer"
                        target="_blank"
                        className={styles['sidebar__link']}
                      >
                        {renderIcon(item)}
                        <IntlMessages id={item.label} />
                      </a>
                    ) : (
                      <NavLink tabIndex={1} to={item.to} data-flag={item.id} className={styles['sidebar__link']}>
                        {renderIcon(item)}
                        <IntlMessages id={item.label} />
                        {typeof item.counter === 'number' && (
                          <SidebarMenuItemCounter value={item.counter} type={item.counterType} />
                        )}
                      </NavLink>
                    )}
                  </li>
                );
              })}
          </ul>
        </PerfectScrollbar>
        <div className={styles['sidebar__bottom']}>
          <StartProcessButton tabIndex={1} onClick={handleRunWorkflow} />
        </div>
      </div>
    </div>
  );
  // tslint:disable-next-line: max-file-line-count
}
