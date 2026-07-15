import React, { useRef } from 'react';
import DatePicker from 'react-datepicker';

import { useDatePickerSettings } from '../../../../../../hooks/useDatePickerSettings';
import { CustomInput } from '../CustomInput/CustomInput';
import { ISingleDatePickerProps } from '../../types';
import { formatDatePickerDisplayValue, normalizeDatePickerDate, toCalendarDate } from '../../utils/normalizeDatePickerDate';

import styles from '../../DatePicker.modules.css';

export const SingleDatePicker = ({
  selected,
  onChange,
  startDay,
  selectsRange: _selectsRange,
  ...props
}: ISingleDatePickerProps) => {
  const { locale, timezone, dateFdw } = useDatePickerSettings();
  const datePickerRef = useRef<DatePicker>(null);
  const selectedDate = toCalendarDate(selected ?? null, timezone);

  const handleChangeDate = (date: Date | null) => {
    datePickerRef.current?.setOpen(false);

    onChange(
      normalizeDatePickerDate({
        date,
        timezone,
        mode: 'start',
        startDay: Boolean(startDay),
      }),
    );
  };

  return (
    <div className={styles['date-picker']}>
      <DatePicker
        ref={datePickerRef}
        customInput={<CustomInput />}
        shouldCloseOnSelect
        locale={locale}
        selected={selectedDate}
        value={selected ? formatDatePickerDisplayValue(selected, timezone) : ''}
        calendarStartDay={dateFdw}
        onChange={handleChangeDate}
        {...props}
      />
    </div>
  );
};
