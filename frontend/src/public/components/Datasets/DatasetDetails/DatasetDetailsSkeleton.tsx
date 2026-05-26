import * as React from 'react';
import { Skeleton } from '../../UI/Skeleton';

import rowStyles from '../DatasetRow/DatasetRow.css';
import styles from './DatasetDetails.css';

const SKELETON_ROWS = Array.from({ length: 6 }, (_, index) => `skeleton-row-${index}`);

export const DatasetDetailsSkeleton = () => {
  return (
    <div className={styles['container']}>
      <header className={styles['header']}>
        <Skeleton className={styles['header-skeleton']} width="40%" height="3.2rem" borderRadius="0.8rem" margin="0" />
        <div className={styles['header__config']}>
          <Skeleton width="8rem" height="3.2rem" borderRadius="0.8rem" />
          <Skeleton width="10rem" height="3.2rem" borderRadius="0.8rem" />
        </div>
      </header>
      <div className={styles['list']}>
        <div className={styles['toolbar']}>
          <Skeleton width="16rem" height="2rem" borderRadius="0.4rem" />
          <Skeleton width="10rem" height="2rem" borderRadius="0.4rem" />
        </div>
        {SKELETON_ROWS.map((row) => (
          <div key={row} className={rowStyles['container']}>
            <div className={rowStyles['value']}>
              <Skeleton
                width="65%"
                height="2rem"
                borderRadius="0.4rem"
              />
            </div>
            <div className={rowStyles['actions']}>
              <Skeleton
                width="2.4rem"
                height="2.4rem"
                borderRadius="0.4rem"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
