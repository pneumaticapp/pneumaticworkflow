import React from 'react';
import classnames from 'classnames';

import { TDropdownSurfaceProps } from './types';

import styles from './DropdownSurface.css';

export const getDropdownSurfaceClassName = (className?: string) => classnames(styles['dropdown-surface'], className);

export const DropdownSurface = React.forwardRef<HTMLDivElement, TDropdownSurfaceProps>(({ className, ...props }, ref) => (
  <div ref={ref} className={getDropdownSurfaceClassName(className)} {...props} />
));
