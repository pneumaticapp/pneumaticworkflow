import * as React from 'react';
import classnames from 'classnames';

import styles from './Skeleton.css';

export interface ISkeletonLoaderProps {
  display?: string;
  width?: string | number;
  height?: string | number;
  margin?: string;
  borderRadius?: string | number;
  className?: string;
}

export function Skeleton({ display, width, height, margin, borderRadius, className }: ISkeletonLoaderProps) {
  return (
    <span className={classnames(className, styles['loader'])} style={{ display, width, height, margin, borderRadius }}>
      &zwnj;
    </span>
  );
}
