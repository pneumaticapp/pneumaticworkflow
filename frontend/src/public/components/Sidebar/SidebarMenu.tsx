import React from 'react';
import classnames from 'classnames';
import PerfectScrollbar from 'react-perfect-scrollbar';

import { IntlMessages } from '../IntlMessages';
import { NavLink } from '../NavLink';
import type { IMenuItem } from '../../types/menu';

import { MobileMenuItem } from './MobileMenuItem';
import { SidebarMenuItemCounter } from './SidebarMenuItemCounter';
import { StartProcessButton } from './StartProcessButton';
import { SubMenuTooltip } from './SubMenuItemTooltip';
import styles from './Sidebar.css';
import type { IDesktopMenuItemProps, ISidebarMenuProps } from './types';

const renderIcon = ({ iconComponent: IconComponent, icon }: IMenuItem) => {
  if (!IconComponent && !icon) {
    return null;
  }

  return <>{IconComponent ? <IconComponent /> : <i className={icon} />} </>;
};

const DesktopMenuItem = ({ active, containerClassnames, item, plan }: IDesktopMenuItemProps) => {
  const link = item.newWindow ? (
    <a
      href={item.to}
      rel="noopener noreferrer"
      target="_blank"
      className={styles['sidebar__link']}
    >
      {renderIcon(item)}
      <IntlMessages id={item.label} />
    </a>
  ) : (
    <NavLink
      to={item.to}
      data-flag={item.id}
      className={styles['sidebar__link']}
      onClick={() => {
        if (item.id === 'workflows') {
          sessionStorage.setItem('isInternalNavigation', 'true');
        }
      }}
    >
      {renderIcon(item)}
      <IntlMessages id={item.label} />
      {typeof item.counter === 'number' && (
        <SidebarMenuItemCounter value={item.counter} type={item.counterType} />
      )}
    </NavLink>
  );

  return (
    <li id={item.id} className={classnames(styles['nav-item'], active && 'active')}>
      {item.subs ? (
        <SubMenuTooltip containerClassName={containerClassnames} plan={plan} menuItems={item.subs}>
          {link}
        </SubMenuTooltip>
      ) : (
        link
      )}
    </li>
  );
};

export const SidebarMenu = ({
  activeItemId,
  containerClassnames,
  isMobile,
  menuItems,
  onCloseMenu,
  onRunWorkflow,
  plan,
}: ISidebarMenuProps) => (
  <>
    <PerfectScrollbar
      options={{ suppressScrollX: true, wheelPropagation: false }}
      className={styles['menu-wrapper']}
    >
      <ul className={styles['menu-wrapper__list']}>
        {menuItems.map((item) => {
          if (item.isHidden) {
            return null;
          }

          if (isMobile) {
            return (
              <MobileMenuItem
                key={item.id}
                item={item}
                renderIcon={renderIcon}
                active={item.id === activeItemId}
                handleCloseMenu={onCloseMenu}
              />
            );
          }

          return (
            <DesktopMenuItem
              key={item.id}
              active={item.id === activeItemId}
              containerClassnames={containerClassnames}
              item={item}
              plan={plan}
            />
          );
        })}
      </ul>
    </PerfectScrollbar>
    <div className={styles['sidebar__bottom']}>
      <StartProcessButton onClick={onRunWorkflow} />
    </div>
  </>
);
