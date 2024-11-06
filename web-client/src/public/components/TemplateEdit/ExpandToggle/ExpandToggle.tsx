/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { SmallArrow } from '../../icons';

import styles from './ExpandToggle.css';

interface IExpandToggleProps {
  isExpanded: boolean;
  className?: string;
  ariaLabel?: string;
  onClick(): void;
}

export function ExpandToggle({ onClick, isExpanded, className, ariaLabel }: IExpandToggleProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={classnames(styles['toggle'], isExpanded && styles['toggle_is-expanded'], className)}
      aria-label={ariaLabel || (isExpanded ? 'Collapse' : 'Expand')}
    >
      <SmallArrow className={styles['arrow']} />
    </button>
  );
}
