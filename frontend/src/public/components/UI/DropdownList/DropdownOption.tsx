import React, { ReactNode } from 'react';
import classnames from 'classnames';

import { Tooltip } from '../Tooltip';

import styles from './DropdownOption.css';

export interface IDropdownOptionProps {
  label: ReactNode;
  isSelected?: boolean;
  withTooltip?: boolean;
}

export function DropdownOption({ label, isSelected, withTooltip }: IDropdownOptionProps) {
  const option = (
    <div className={classnames(styles['dropdown-option'], isSelected && styles['dropdown-option_selected'])}>
      {label}
    </div>
  );

  if (!withTooltip) {
    return option;
  }

  return (
    <Tooltip content={<div className={styles['dropdown-option__tooltip']}>{label}</div>} interactive={false}>
      {option}
    </Tooltip>
  );
}
