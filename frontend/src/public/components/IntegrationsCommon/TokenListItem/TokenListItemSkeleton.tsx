import React from 'react';

import { Skeleton } from '../../UI/Skeleton';
import type { ITokenListItemSkeletonProps } from './types';

import styles from './TokenListItem.css';

export function TokenListItemSkeleton({ 'data-testid': testId }: ITokenListItemSkeletonProps) {
  return (
    <div className={styles['token-list']} data-testid={testId}>
      {[0, 1, 2].map((row) => (
        <div key={row} className={styles['token-list__item']}>
          <div className={styles['token-list__info']}>
            <Skeleton className={styles['token-list__skeleton-name']} />
            <Skeleton className={styles['token-list__skeleton-details']} />
            <Skeleton className={styles['token-list__skeleton-token']} />
          </div>
          <div className={styles['token-list__actions']}>
            <Skeleton className={styles['token-list__skeleton-action']} />
          </div>
        </div>
      ))}
    </div>
  );
}
