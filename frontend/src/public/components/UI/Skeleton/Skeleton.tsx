import React from 'react';
import classnames from 'classnames';

import type { ISkeletonLoaderProps } from './types';

import styles from './Skeleton.css';

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
