import React from 'react';
import { useIntl } from 'react-intl';
import { ShortArrowIcon } from '../../icons';
import styles from './ShortArrowBox.css';

interface IShortArrowBoxProps {
  rotated?: boolean;
  toggleBreakdownHandler: () => void;
}

export const ShortArrowBox = ({ rotated, toggleBreakdownHandler }: IShortArrowBoxProps) => {
  const { formatMessage } = useIntl();
  return (
    <button
      className={styles['short-arrow-box']}
      type="button"
      onClick={toggleBreakdownHandler}
      aria-label={formatMessage({ id: rotated ? 'ui.show-tasks' : 'ui.hide-tasks' })}
    >
      <div className={rotated ? styles['short-arrow-rotated'] : styles['short-arrow']}>
        <ShortArrowIcon />
      </div>
    </button>
  );
};
