/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';

import { Field } from '../../Field';
import {
  formatDelayRequest,
  getSeconds,
  parseDuration,
  SEC_IN_DAY,
} from '../../../utils/dateTime';
import { EMPTY_DURATION } from '../../TemplateEdit/constants';

import styles from './Duration.css';

export interface IDurationProps {
  duration: string | null;
  durationMonths?: number | null;
  onEditDuration(duration: string): void;
  onEditDurationMonths?(months: number): void;
}

export enum EDurationFieldType {
  Hour = 'hours',
  Day = 'days',
  Minute = 'minutes',
}

export function Duration({
  duration,
  durationMonths,
  onEditDuration,
  onEditDurationMonths,
}: IDurationProps) {
  const { useState } = React;
  const { formatMessage } = useIntl();

  const normalizedDuration = duration || EMPTY_DURATION;
  const { days, hours, minutes } = parseDuration(normalizedDuration);
  const [daysDuration, setDaysDuration] = useState(days);
  const [hoursDuration, setHoursDuration] = useState(hours);
  const [minutesDuration, setMinutesDuration] = useState(minutes);

  const SET_DURATION_MAP = {
    [EDurationFieldType.Day]: setDaysDuration,
    [EDurationFieldType.Hour]: setHoursDuration,
    [EDurationFieldType.Minute]: setMinutesDuration,
  };

  const handleChangeDuration = (type: EDurationFieldType) => (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    const isValid = e.target.validity.valid;

    if (!isValid) {
      return;
    }

    const value = Number(e.target.value);
    const duration = {
      days: daysDuration,
      hours: hoursDuration,
      minutes: minutesDuration,
      [type]: value,
    };

    const totalDays = Math.floor(getSeconds(duration) / SEC_IN_DAY);
    const isDurationExceeds = totalDays > 999;

    if (isDurationExceeds) {
      return;
    }

    const setDuration = SET_DURATION_MAP[type];
    setDuration(value);

    const formattedDuration = formatDelayRequest(duration);
    onEditDuration(formattedDuration);
  };

  const classNameForField = (duration: number) => classnames(styles['field'], duration === 0 && styles['field_default-value']);

  return (
    <div className={styles['container']}>
      {(typeof durationMonths !== 'undefined' &&
        typeof onEditDurationMonths !== 'undefined') && (
          <Field
            value={durationMonths || ''}
            className={classNameForField(durationMonths || 0)}
            onChange={e => onEditDurationMonths(Number(e.target.value))}
            intlId="duration-month"
            labelClassName={styles['field-label']}
            placeholder={formatMessage({ id: 'duration-month-placeholder' })}
            pattern="[0-9]*"
          />
        )}
      <Field
        value={daysDuration}
        className={classNameForField(daysDuration)}
        onChange={handleChangeDuration(EDurationFieldType.Day)}
        intlId="duration-day"
        labelClassName={styles['field-label']}
        placeholder={formatMessage({ id: 'duration-day-placeholder' })}
        pattern="[0-9]*"
      />
      <Field
        value={hoursDuration}
        className={classNameForField(hoursDuration)}
        onChange={handleChangeDuration(EDurationFieldType.Hour)}
        intlId="duration-hour"
        labelClassName={styles['field-label']}
        placeholder={formatMessage({ id: 'duration-hour-placeholder' })}
        pattern="[0-9]*"
      />
      <Field
        value={minutesDuration}
        className={classNameForField(minutesDuration)}
        onChange={handleChangeDuration(EDurationFieldType.Minute)}
        intlId="duration-minute"
        labelClassName={styles['field-label']}
        placeholder={formatMessage({ id: 'duration-minute-placeholder' })}
        pattern="[0-9]*"
      />
    </div>
  );
}
