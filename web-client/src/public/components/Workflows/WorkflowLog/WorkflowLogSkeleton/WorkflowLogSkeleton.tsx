import React from 'react';
import classnames from 'classnames';

import { Skeleton } from '../../../UI/Skeleton';

import styles from './WorkflowLogSkeleton.css';

export interface IWorkflowLogSkeletonProps {
  className?: string;
}

export function WorkflowLogSkeleton({ className }: IWorkflowLogSkeletonProps) {
  return (
    <div className={classnames(styles['skeleton'], className)}>
      <div className={styles['skeleton__data']}>
        <Skeleton width="45%" height="16px" />
        <Skeleton width="65%" height="24px" margin="8px 0" />
        <Skeleton width="35%" height="20px" />
      </div>
    </div>
  );
}
