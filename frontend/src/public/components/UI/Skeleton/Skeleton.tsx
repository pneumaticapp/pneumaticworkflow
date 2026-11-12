import React from 'react';
import classnames from 'classnames';

import type { TWorkflowLogTheme } from '../../Workflows/WorkflowLog/types';

import styles from './Skeleton.css';

export interface ISkeletonLoaderProps {
  display?: string;
  width?: string | number;
  height?: string | number;
  margin?: string;
  borderRadius?: string | number;
  className?: string;
  theme?: TWorkflowLogTheme;
}

export function Skeleton({ display, theme, width, height, margin, borderRadius, className }: ISkeletonLoaderProps) {
  return (
    <span
      className={classnames(className, theme === 'white' && styles['is-white'], styles['loader'])}
      style={{ display, width, height, margin, borderRadius }}
    >
      &zwnj;
    </span>
  );
}
