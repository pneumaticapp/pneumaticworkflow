import React from 'react';
import classnames from 'classnames';

import styles from './Sidebar.css';
import { TMenuCounterType } from '../../types/menu';

export interface ISidebarMenuItemCounter {
  value: number;
  type?: TMenuCounterType;
}

export const SidebarMenuItemCounter = ({ value, type = 'alert' }: ISidebarMenuItemCounter) => {
  if (!value) {
    return null;
  }

  const count = value > 999 ? '999+' : String(value);

  return (
    <div className={styles['counter_container']}>
      <div
        className={classnames(
          styles['counter'],
          { [styles['counter_alert']]: type === 'alert' },
          { [styles['counter_info']]: type === 'info' },
        )}
      >
        <span>{count}</span>
      </div>
    </div>
  );
};
