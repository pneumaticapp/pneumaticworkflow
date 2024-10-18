import React from 'react';
import DatePicker, { DatePickerProps } from 'react-datepicker';
import { Locale } from 'date-fns';
import { enUS, ru } from 'date-fns/locale';
import moment from 'moment-timezone';

import { ELocale } from '../../../../types/redux';

import 'react-datepicker/dist/react-datepicker.css';
import '../../../../assets/css/library/react-datepicker.css';

export type IDatePickerProps = DatePickerProps & {
  language: string;
  dateFdw: string;
  timezone: string;
  onChange(date: Date | string | null): void;
};

export function DatePickerComponent({ dateFdw, language, timezone, selected, onChange, ...props }: IDatePickerProps) {
  const mapLocale: { [key: string]: Locale } = {
    [ELocale.English]: enUS,
    [ELocale.Russian]: ru,
  };

  return (
    <DatePicker
      {...props}
      locale={mapLocale[language]}
      selected={
        // Removing the timezone so that the library does not format the date in the time zone set by the browser
        selected ? (moment(selected).tz(timezone, false).format('YYYY-MM-DDTHH:mm:ss') as unknown as Date) : null
      }
      calendarStartDay={dateFdw}
      utcOffset={timezone}
      // Setting the selected date as the time zone date set by the user
      onChange={(value: any) => onChange(value ? moment(value).tz(timezone, true).format() : null)}
    />
  );
}
