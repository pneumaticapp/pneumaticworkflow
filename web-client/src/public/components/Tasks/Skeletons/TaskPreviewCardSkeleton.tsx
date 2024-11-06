/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { Skeleton } from '../../UI/Skeleton';

import styles from './TaskPreviewCardSkeleton.css';

export interface ITaskCardLoaderProps {
  className?: string;
}

export function TaskPreviewCardSkeleton({ className }: ITaskCardLoaderProps) {

  return (
    <div className={classnames(styles['card-skeleton'], className)}>
      <div className={styles['card-skeleton__inner']}>
        <Skeleton width="45%" height="16px" />
        <Skeleton width="65%" height="24px" margin="8px 0" />
      </div>
    </div>
  );
}
