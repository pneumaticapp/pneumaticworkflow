import React from 'react';

import { Skeleton } from '../../UI/Skeleton';

import styles from './TenantsSkeleton.css';
import stylesTenant from '../Tenant/Tenant.css';

export function TenantsSkeleton() {
  return (
    <div className={stylesTenant['tenant']}>
      <div className={styles['skeleton']}>
        <div className={styles['skeleton__names']}>
          <Skeleton height="24px" />
        </div>
        <div className={styles['skeleton__counters']}>
          <Skeleton className={styles['skeleton__counters-item']} />
        </div>
      </div>
    </div>
  );
}
