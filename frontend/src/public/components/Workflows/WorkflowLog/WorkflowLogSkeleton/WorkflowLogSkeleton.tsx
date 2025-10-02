import React from 'react';
import classnames from 'classnames';

import { Skeleton } from '../../../UI/Skeleton';
import { TWorkflowLogTheme } from '../WorkflowLog';

import styles from './WorkflowLogSkeleton.css';

export interface IWorkflowLogSkeletonProps {
  className?: string;
  theme?: TWorkflowLogTheme;
}

export function WorkflowLogSkeleton({ className, theme }: IWorkflowLogSkeletonProps) {
  return (
    <div className={classnames(styles['skeleton'], theme === 'white' && styles['is-white'], className)}>
      <div className={styles['skeleton__data']}>
        <Skeleton theme={theme} width="45%" height="16px" />
        <Skeleton theme={theme} width="65%" height="24px" margin="8px 0" />
        <Skeleton theme={theme} width="35%" height="20px" />
      </div>
    </div>
  );
}
