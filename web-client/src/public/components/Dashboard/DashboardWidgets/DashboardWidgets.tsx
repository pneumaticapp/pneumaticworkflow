import React from 'react';

import { AppMobileButtons } from './AppMobileButtons';
import { QuickButtons } from './QuickButtons';

import styles from './DashboardWidgets.css';

export function DashboardWidgets() {
  return (
    <div className={styles['widgets']}>
      <div className={styles['widgets__item']}>
        <QuickButtons />
      </div>
      <div className={styles['widgets__item']}>
        <AppMobileButtons />
      </div>
    </div>
  );
}
