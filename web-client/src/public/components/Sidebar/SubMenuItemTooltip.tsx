/* eslint-disable */
/* prettier-ignore */
import React, { useState } from 'react';
import * as classnames from 'classnames';
import { Tooltip, TooltipProps } from 'reactstrap';
import { IntlMessages } from '../IntlMessages';

import { IMenuItemSub } from '../../types/menu';
import { ESubscriptionPlan } from '../../types/account';

import { NavLink } from '../NavLink/NavLink';

import s from './SubMenuItemTooltip.css';

export interface ISubMenuTooltipProps extends Omit<TooltipProps, 'target' | 'isOpen'> {
  menuItems: IMenuItemSub[];
  containerClassName: string;
  classNameBase?: string;
  plan?: ESubscriptionPlan;
  onCloseSubmenu(): void;
}

export const SubMenuTooltip = ({
  isOpen,
  target,
  menuItems,
  onCloseSubmenu,
  containerClassName,
  plan = ESubscriptionPlan.Free,
}: ISubMenuTooltipProps) => {
  if (!target) {
    return null;
  }

  let [activeSubmenu, setActiveSubmenu] = useState(false);

  let timeDelayHideShowSubMenu = containerClassName.includes('main-hidden') ? 200 : 0;
  let styleHideSubMenu = '';
  let targetCurrent = document.querySelector(`#${target}`)!;
  const planClassNameMap = {
    [ESubscriptionPlan.Unknown]: s['plan-free'],
    [ESubscriptionPlan.Free]: s['plan-free'],
    [ESubscriptionPlan.Trial]: s['plan-trial'],
    [ESubscriptionPlan.Premium]: s['plan-premium'],
    [ESubscriptionPlan.Unlimited]: s['plan-premium'],
    [ESubscriptionPlan.FractionalCOO]: s['plan-premium'],
  };

  const renderSubMenuItems = () => {
    return (
      <ul>
        {menuItems.map((item) => (
          <li key={item.to}>
            {item.to ? (
              <a
                onClick={() => {
                  onCloseSubmenu();
                  handleMouseOver();
                }}
                href={item.to}
                rel="noopener noreferrer"
                target="_blank"
              >
                <IntlMessages id={item.label} />
              </a>
            ) : (
              <NavLink to={item.to} data-flag={item.label}>
                <IntlMessages id={item.label} />
              </NavLink>
            )}
          </li>
        ))}
      </ul>
    );
  };

  const handleMouseLeave = () => targetCurrent.classList.add('active');
  const handleMouseOver = () => targetCurrent.classList.remove('active');

  if (isOpen) {
    styleHideSubMenu = '';
    window.setTimeout(() => setActiveSubmenu(true), timeDelayHideShowSubMenu);
  } else {
    styleHideSubMenu = s['hide'];
    window.setTimeout(() => setActiveSubmenu(false), timeDelayHideShowSubMenu);
  }

  return (
    <div onMouseOver={handleMouseLeave} onMouseLeave={handleMouseOver}>
      <Tooltip
        arrowClassName={s['sub-menu__arrow']}
        className={classnames(s['sub-menu'], planClassNameMap[plan], styleHideSubMenu)}
        innerClassName={s['sub-menu__inner']}
        isOpen={activeSubmenu}
        placement={'right'}
        target={target}
      >
        {renderSubMenuItems()}
      </Tooltip>
    </div>
  );
};
