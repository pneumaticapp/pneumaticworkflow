/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { IMenuItem } from '../../types/menu';
import { IntlMessages } from '../IntlMessages';
import { NavLink } from '../NavLink';

import { SidebarMenuItemCounter } from './SidebarMenuItemCounter';
import styles from './Sidebar.css';

export interface IMobileMenuItemProps {
  item: IMenuItem;
  active: boolean;
  tabIndex?: number;
  renderIcon(item: IMenuItem): JSX.Element | null;
  handleCloseMenu(): void;
}

export const MobileMenuItem = (props: IMobileMenuItemProps) => {
  const { item, active, renderIcon, handleCloseMenu, tabIndex } = props;
  const { id, label, to, newWindow } = item;
  const navItemStyle = classnames(styles['nav-item'], styles['mobile-item'], active && 'active');

  return (
    <li key={`mobileMenuItem${id}`} className={navItemStyle} onClick={handleCloseMenu}>
      {newWindow ? (
        <a href={to} rel="noopener noreferrer" target="_blank" className={styles['sidebar__link']} tabIndex={tabIndex}>
          {renderIcon(item)}
          <IntlMessages id={label} />
        </a>
      ) : (
        <NavLink to={to} data-flag={id} className={styles['sidebar__link']} tabIndex={tabIndex}>
          {renderIcon(item)}
          <IntlMessages id={label} />
          {typeof item.counter === 'number' && <SidebarMenuItemCounter value={item.counter} type={item.counterType} />}
        </NavLink>
      )}
    </li>
  );
};
