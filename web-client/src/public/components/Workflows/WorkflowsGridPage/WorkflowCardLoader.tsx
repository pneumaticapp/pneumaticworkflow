/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { Skeleton } from '../../UI/Skeleton';

import styles from './WorkflowsGridPage.css';

export interface IWorkflowCardLoaderProps {
  className?: string;
}

export function WorkflowCardLoader({ className }: IWorkflowCardLoaderProps) {

  return (
    <>
      <div className={styles['card-wrapper']}>
        <div className={classnames(styles['card'], styles['card-loading'])}>
          <Skeleton width="160px" height="16px" borderRadius="4px" margin="0 16px 8px" />
          <Skeleton width="80px" height="16px" borderRadius="4px" margin="0 16px 8px" />
          <Skeleton width="192px" height="24px" borderRadius="4px" margin="0 16px 20px" />
          <Skeleton width="100%" height="90px" borderRadius="16px" />
        </div>
      </div>
    </>
  );
}
