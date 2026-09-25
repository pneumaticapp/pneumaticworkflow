import React from 'react';
import classnames from 'classnames';

import { ExpandIcon } from '../../icons';
import { IDropdownControlProps } from './types';

import styles from './DropdownControl.css';

export function DropdownControl({ title, isOpen, className }: IDropdownControlProps) {
  return (
    <span className={classnames(styles['dropdown-control'], isOpen && styles['is-open'], className)}>
      <span className={styles['dropdown-control__value']}>{title}</span>
      <ExpandIcon className={styles['dropdown-control__arrow']} />
    </span>
  );
}
