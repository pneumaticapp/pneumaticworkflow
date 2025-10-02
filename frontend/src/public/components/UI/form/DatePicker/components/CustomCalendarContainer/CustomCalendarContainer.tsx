import React, { forwardRef } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { Button } from '../../../../Buttons/Button/Button';

import styles from './CustomCalendarContainer.css';
import { CustomCalendarContainerProps } from './types';



export const CustomCalendarContainer = 
forwardRef<HTMLDivElement, CustomCalendarContainerProps>(({ onChange, selected, children, value, ...props }, ref) => {
  const renderCalendarFooter = () => {
    const { formatMessage } = useIntl();

    return (
      <div className={styles['calendar-footer']}>
        <Button
          buttonStyle="yellow"
          disabled={!selected}
          label={formatMessage({ id: 'due-date.save' })}
          onClick={() => onChange(selected)}
        />
        <Button
          className={classnames('cancel-button', styles['calendar-footer__cancel'])}
          label={formatMessage({ id: 'due-date.remove' })}
          onClick={() => onChange(null)}
        />
      </div>
    );
  };

  return (
    <div {...props} ref={ref}>
      {children}
      {renderCalendarFooter()}
    </div>
  )
});
