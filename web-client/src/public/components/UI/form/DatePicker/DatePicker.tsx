import React from 'react';
import DatePicker, { DatePickerProps } from 'react-datepicker';
import { Locale } from 'date-fns';
import { enUS, ru } from 'date-fns/locale';
import moment from 'moment-timezone';

import { ELocale } from '../../../../types/redux';

import 'react-datepicker/dist/react-datepicker.css';
import '../../../../assets/css/library/react-datepicker.css';
import { DATE_STRING_FNS_TEMPLATE } from '../../../../utils/dateTime';

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
        selected ? (moment(selected).tz(timezone, false).format('YYYY-MM-DDTHH:mm:ss') as unknown as Date) : null
      }
      dateFormat={DATE_STRING_FNS_TEMPLATE}
      calendarStartDay={dateFdw}
      utcOffset={timezone}
      onChange={(value: any) => {
        const mDate = moment(value);
        const endOfDay = mDate.isSame(mDate.clone().startOf('day'));
        const adjustedDate = endOfDay ? mDate.set({ hour: 23, minute: 59, second: 59 }) : mDate;
        onChange(adjustedDate ? adjustedDate.toDate() : null);
      }}
    />
  );
}
