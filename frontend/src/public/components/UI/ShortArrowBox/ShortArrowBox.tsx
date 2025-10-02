/* eslint-disable max-len */
import React from 'react';
import { ShortArrowIcon } from '../../icons';
import styles from './ShortArrowBox.css';

interface IShortArrowBoxProps {
  rotated?: boolean;
  toggleBreakdownHandler: () => void;
}

export const ShortArrowBox = ({ rotated, toggleBreakdownHandler }: IShortArrowBoxProps) => {
  return (
    <button
      className={styles['short-arrow-box']}
      type="button"
      onClick={toggleBreakdownHandler}
      aria-label={rotated ? 'show tasks' : 'hidden tasks'}
    >
      <div className={rotated ? styles['short-arrow-rotated'] : styles['short-arrow']}>
        <ShortArrowIcon />
      </div>
    </button>
  );
};
