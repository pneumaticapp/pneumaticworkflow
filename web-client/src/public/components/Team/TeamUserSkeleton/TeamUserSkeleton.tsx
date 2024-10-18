/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { Skeleton } from '../../UI/Skeleton';

import styles from './TeamUserSkeleton.css';

export function TeamUserSkeleton() {
  return (
    <div className={styles['skeleton']}>
      <Skeleton className={styles['skeleton-avatar']} />
      <div className={styles['skeleton-data']}>
        <Skeleton width="45%" height="20px" margin="0 0 4px" />
        <Skeleton width="65%" height="16px" />
      </div>
    </div>
  );
}
