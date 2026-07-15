import React from 'react';
import classnames from 'classnames';

import { ESubscriptionPlan } from '../../types/account';
import { IntlMessages } from '../IntlMessages';
import { Tooltip } from '../UI';

import styles from './SubMenuItemTooltip.css';
import type { ISubMenuTooltipProps } from './types';

const planClassNameMap = {
  [ESubscriptionPlan.Unknown]: styles['plan-premium'],
  [ESubscriptionPlan.Free]: styles['plan-premium'],
  [ESubscriptionPlan.Trial]: styles['plan-trial'],
  [ESubscriptionPlan.Premium]: styles['plan-premium'],
  [ESubscriptionPlan.Unlimited]: styles['plan-premium'],
  [ESubscriptionPlan.FractionalCOO]: styles['plan-premium'],
};

export const SubMenuTooltip = ({
  children,
  containerClassName,
  menuItems,
  plan = ESubscriptionPlan.Free,
}: ISubMenuTooltipProps) => {
  const delay = containerClassName.includes('main-hidden') ? 200 : 0;
  const content = (
    <ul>
      {menuItems.map((item) => (
        <li key={item.to}>
          <a
            href={item.to}
            rel="noopener noreferrer"
            target="_blank"
            aria-label={item.label}
            className={styles['sub-menu__link']}
          >
            <IntlMessages id={item.label} />
          </a>
        </li>
      ))}
    </ul>
  );

  return (
    <Tooltip
      className={classnames(styles['sub-menu'], planClassNameMap[plan])}
      content={content}
      contentClassName={styles['sub-menu__inner']}
      appendTo={() => document.body}
      delay={[delay, delay]}
      duration={300}
      placement="right"
      size="auto"
    >
      {children}
    </Tooltip>
  );
};
