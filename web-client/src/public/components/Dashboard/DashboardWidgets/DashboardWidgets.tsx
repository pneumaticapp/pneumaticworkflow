import React from 'react';
import { useSelector } from 'react-redux';
import { getTemplatesStore } from '../../../redux/selectors/templates';

import { AppMobileButtons } from './AppMobileButtons';
import { QuickButtons } from './QuickButtons';
import { getIsAdmin } from '../../../redux/selectors/user';

import styles from './DashboardWidgets.css';

export function DashboardWidgets() {
  const { isTemplateOwner } = useSelector(getTemplatesStore);
  const isAdmin = useSelector(getIsAdmin);

  return (
    <div className={styles['widgets']}>
      {(isAdmin || isTemplateOwner) && (
        <div className={styles['widgets__item']}>
          <QuickButtons isAdmin={isAdmin} isTemplateOwner={isTemplateOwner} />
        </div>
      )}
      <div className={styles['widgets__item']}>
        <AppMobileButtons />
      </div>
    </div>
  );
}
