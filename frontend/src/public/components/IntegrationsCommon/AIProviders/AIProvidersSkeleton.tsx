import * as React from 'react';

import { Skeleton } from '../../UI/Skeleton';

import styles from './AIProviders.css';

export function AIProvidersSkeleton() {
  return (
    <div className={styles['providers__list']} data-testid="ai-providers-skeleton">
      {[0, 1, 2].map((row) => (
        <div key={row} className={styles['providers__item']}>
          <div className={styles['providers__item-info']}>
            <Skeleton className={styles['providers__skeleton-name']} />
            <Skeleton className={styles['providers__skeleton-url']} />
            <Skeleton className={styles['providers__skeleton-key']} />
          </div>
          <div className={styles['providers__item-actions']}>
            <Skeleton className={styles['providers__skeleton-btn']} />
          </div>
        </div>
      ))}
    </div>
  );
}
