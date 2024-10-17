/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { Skeleton } from '../../UI/Skeleton';

import styles from './Breakdowns.css';

export function BreakdownsSkeleton() {
  return (
    <div className={styles['breakdown']}>
      <div className={styles['breakdown__skeleton']}>
        <div className={styles['breakdown__skeleton-names']}>
          <Skeleton height="24px" />
        </div>
        <div className={styles['breakdown__skeleton-counters']}>
          <Skeleton className={styles['breakdown__skeleton-counters-item']} />
          <Skeleton className={styles['breakdown__skeleton-counters-item']} />
          <Skeleton className={styles['breakdown__skeleton-counters-item']} />
          <Skeleton className={styles['breakdown__skeleton-counters-item']} />
        </div>
      </div>
    </div>
  );
}
