import React from 'react';

import { ESubscriptionPlan } from '../../types/account';

import styles from './Sidebar.css';
import type { ISidebarRibbonProps } from './types';

export const SidebarRibbon = ({ formatMessage, leaseLevel, plan, trialIsActive }: ISidebarRibbonProps) => {
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
  const label = trialIsActive ? formatMessage({ id: 'sidebar.ribbon-trial' }) : statusLabelsMap[plan];

  return <span className={styles['sidebar-ribbon__label']}>{label}</span>;
};
