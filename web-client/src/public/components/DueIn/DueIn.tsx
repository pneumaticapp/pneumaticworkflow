import React, { useEffect, useRef, useState } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import moment from 'moment-timezone';

import { useSelector } from 'react-redux';
import { getLanguage } from '../../redux/selectors/user';
import { getDueInData } from './utils/getDueInData';
import { ClockIcon } from '../icons';
import { DropdownArea } from '../UI/DropdownArea';
import { getDate, getTime } from '../../utils/strings';
import { Button, InputField, Tooltip } from '../UI';
import { DatePicker } from '../UI/form/DatePicker';

import styles from './DueIn.css';

export interface IDueInProps {
  dueDate: string | null;
  timezone: string;
  dateFmt: string;
  showIcon?: boolean;
  containerClassName?: string;
  view?: 'timeLeft' | 'dueDate';
  withTime?: boolean;
  onSave(date: string): void;
  onRemove(): void;
}

export function DueIn({
  dueDate,
  containerClassName,
  showIcon = true,
  view = 'timeLeft',
  withTime,
  timezone,
  dateFmt,
  onSave,
  onRemove,
}: IDueInProps) {
  const { formatMessage } = useIntl();
  const locale = useSelector(getLanguage);
  const dueInData = getDueInData([dueDate], null, timezone, locale);
  const dropdownRef = useRef<React.ElementRef<typeof DropdownArea> | null>(null);
  const [selectedDate, setSelectedDate] = useState(null);
  const [timeString, setTimeString] = useState('');
  const [timeError, setTimeError] = useState('');

  useEffect(() => {
    setTimeString(dueDate ? getTime(dueDate, timezone, dateFmt) : '');
  }, [dueDate]);

  const handleChangeTime: React.DOMAttributes<HTMLInputElement>['onChange'] = (event) => {
    const newTimeString = event.currentTarget.value;
    setTimeString(newTimeString);
    setTimeError('');
  };

  const handleSave = () => {
    if (!selectedDate) return;

    if (!timeString) {
      onSave(selectedDate);
      dropdownRef.current?.closeDropdown();
      return;
    }

    try {
      const dateWithTime = setTimeForDate(selectedDate, timeString, timezone, dateFmt);
      onSave(dateWithTime);
      dropdownRef.current?.closeDropdown();
    } catch (error) {
      setTimeError(formatMessage({ id: 'due-date.time-invalid' }));
    }
  };

  const handleRemove = () => {
    if (dueInData) {
      onRemove();
      setTimeString('');
    }

    dropdownRef.current?.closeDropdown();
  };

  const renderLabel = () => {
    if (!dueInData || !dueDate) {
      return (
        <Tooltip content={formatMessage({ id: 'due-date.tooltip-set-up' })} contentClassName={styles['tooltip-label']}>
          <p className={classnames(styles['due-date__inner'], styles['not-set'])}>
            <span className={styles['due-date__status']}>{formatMessage({ id: 'due-date.edit' })}</span>

            {showIcon && <ClockIcon className={styles['icon']} />}
          </p>
        </Tooltip>
      );
    }

    const { statusTitle, timeLeft, isOverdue } = dueInData;
    return (
      <Tooltip content={formatMessage({ id: 'due-date.tooltip-due-date' })} contentClassName={styles['tooltip-label']}>
        <p className={classnames(styles['due-date__inner'], isOverdue && styles['overdue'])}>
          <span className={styles['due-date__status']}>
            {view === 'timeLeft'
              ? formatMessage({ id: statusTitle }, { duration: timeLeft })
              : getDate(dueDate, { view: 'day' })}
          </span>
          {showIcon && <ClockIcon className={styles['icon']} />}
        </p>
      </Tooltip>
    );
  };

  return (
    <div className={containerClassName}>
      <DropdownArea
        ref={dropdownRef}
        toggle={<div className={classnames(styles['due-date'])}>{renderLabel()}</div>}
        placement="bottom-end"
      >
        <div className={styles['datepicker']}>
          <DatePicker
            selected={selectedDate}
            onChange={setSelectedDate}
            inline
            minDate={moment.tz(timezone).add(1, 'days').format('YYYY-MM-DD')}
          />
        </div>

        {withTime && (
          <InputField
            fieldSize="md"
            containerClassName={styles['time-block']}
            className={styles['time-block__input']}
            placeholder={
              dateFmt.split(', ')[2] === 'p'
                ? formatMessage({ id: 'due-date.time.12' })
                : formatMessage({ id: 'due-date.time.24' })
            }
            value={timeString}
            onChange={handleChangeTime}
            errorMessage={timeError}
          >
            <div className={styles['time-block__hint']}>{formatMessage({ id: 'due-date.time' })}</div>
          </InputField>
        )}

        <div className={styles['datepicker-controls']}>
          <Button
            label={formatMessage({ id: 'due-date.save' })}
            onClick={handleSave}
            buttonStyle="yellow"
            size="md"
            disabled={!selectedDate}
          />

          {dueInData && (
            <button
              type="button"
              className={classnames('cancel-button', styles['datepicker-controls__remove'])}
              onClick={handleRemove}
            >
              {formatMessage({ id: 'due-date.remove' })}
            </button>
          )}
        </div>
      </DropdownArea>
    </div>
  );
}

const setTimeForDate = (initialDate: Date, timeString: string, timezone: string, dateFmt: string): string => {
  const timeRegex12 = /(\d{1,2})(?::(\d{2}))?\s*?(am|pm)/;
  const timeRegex24 = /^([01][0-9]|2[0-3]):([0-5][0-9])$/;
  const match = dateFmt.split(', ')[2] === 'p' ? timeRegex12.exec(timeString) : timeRegex24.exec(timeString);
  if (!match) throw new Error('Invalid time');

  const [, hours, minutes = '00', period] = match;

  return moment(initialDate)
    .tz(timezone)
    .set({ h: period && period === 'pm' ? +hours + 12 : +hours, m: +minutes })
    .format();
};
