import React, { useRef } from 'react';
import DatePicker from 'react-datepicker';
import { useIntl } from 'react-intl';

import { useDatePickerSettings } from '../../../../../../hooks/useDatePickerSettings';
import { CustomInput } from '../CustomInput/CustomInput';
import { IRangeDatePickerProps } from '../../types';
import {
  formatDatePickerRangeDisplayValue,
  normalizeDatePickerDate,
  toCalendarDate,
} from '../../utils/normalizeDatePickerDate';

import styles from '../../DatePicker.modules.css';

export const RangeDatePicker = ({
  startDate,
  endDate,
  onChange,
  placeholderText,
  isClearable = true,
  selectsRange: _selectsRange,
  ...props
}: IRangeDatePickerProps) => {
  const { formatMessage } = useIntl();
  const { locale, timezone, dateFdw } = useDatePickerSettings();
  const datePickerRef = useRef<DatePicker>(null);
  const calendarStartDate = toCalendarDate(startDate ?? null, timezone);
  const calendarEndDate = toCalendarDate(endDate ?? null, timezone);
  const clearLabel = formatMessage({ id: 'ui-input.clear' });
  const hasSelectedRange = Boolean(startDate || endDate);

  const handleChangeRange = ([nextStartDate, nextEndDate]: [Date | null, Date | null]) => {
    const adjustedStartDate = normalizeDatePickerDate({
      date: nextStartDate,
      timezone,
      mode: 'start',
      startDay: true,
    });
    const adjustedEndDate = normalizeDatePickerDate({
      date: nextEndDate,
      timezone,
      mode: 'end',
    });

    onChange([adjustedStartDate, adjustedEndDate]);

    if (adjustedStartDate && adjustedEndDate) {
      datePickerRef.current?.setOpen(false);
    }
  };

  return (
    <div className={styles['date-picker']}>
      <DatePicker
        {...props}
        ref={datePickerRef}
        ariaLabelClose={clearLabel}
        clearButtonTitle={clearLabel}
        customInput={<CustomInput />}
        isClearable={Boolean(isClearable && hasSelectedRange)}
        shouldCloseOnSelect={false}
        locale={locale}
        selectsRange
        startDate={calendarStartDate ?? undefined}
        endDate={calendarEndDate ?? undefined}
        selected={calendarStartDate}
        value={formatDatePickerRangeDisplayValue(startDate, endDate, timezone)}
        placeholderText={placeholderText}
        calendarStartDay={dateFdw}
        onChange={handleChangeRange}
      />
    </div>
  );
};
