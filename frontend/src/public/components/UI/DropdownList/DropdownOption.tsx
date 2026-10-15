import React from 'react';
import classnames from 'classnames';

import { Tooltip } from '../Tooltip';
import { IDropdownOptionProps } from './types';

import styles from './DropdownOption.css';

export function DropdownOption({ label, isSelected, withTooltip, className }: IDropdownOptionProps) {
  const option = (
    <div
      className={classnames(
        styles['dropdown-option'],
        isSelected && styles['dropdown-option_selected'],
        className,
      )}
    >
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
