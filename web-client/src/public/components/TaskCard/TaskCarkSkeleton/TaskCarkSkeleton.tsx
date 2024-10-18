/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { Skeleton } from '../../UI/Skeleton';

import styles from './TaskCarkSkeleton.css';

export interface ITaskCardLoaderProps {
  className?: string;
}

export function TaskCarkSkeleton({ className }: ITaskCardLoaderProps) {
  return (
    <div className={classnames(styles['task-skeleton'], className)}>
      <div className={styles['task-skeleton__data']}>
        <Skeleton width="45%" height="16px" />
        <Skeleton width="65%" height="24px" margin="8px 0" />
        <Skeleton width="35%" height="20px" />
        <Skeleton width="20px" height="20px" borderRadius="50%" margin="8px 0 0" />
      </div>
      <div className={styles['task_skeleton__links']} >
        <Skeleton width="20px" height="20px" display="inline-block"/>
        <Skeleton width="25%" height="16px" display="inline-block" margin="auto 8px"/>
        <div className={styles['task_skeleton__button']}>
          <Skeleton width="86px" height="32px" display="inline-block" borderRadius="16px" margin="0 0 8px" />
        </div>
      </div>
    </div>
  );
}
