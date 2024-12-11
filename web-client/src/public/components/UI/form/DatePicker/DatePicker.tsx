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
  startDay?: true;
};

export function DatePickerComponent({
  dateFdw,
  language,
  timezone,
  selected,
  onChange,
  startDay,
  ...props
}: IDatePickerProps) {
  const mapLocale: { [key: string]: Locale } = {
    [ELocale.English]: enUS,
    [ELocale.Russian]: ru,
  };

  return (
    <DatePicker
      {...props}
      startDay={startDay}
      locale={mapLocale[language]}
      selected={
        // Removing the timezone so that the library does not format the date in the time zone set by the format
        selected ? (moment(selected).tz(timezone, false).format('YYYY-MM-DDTHH:mm:ss') as unknown as Date) : null
      }
      dateFormat={DATE_STRING_FNS_TEMPLATE}
      calendarStartDay={dateFdw}
      utcOffset={timezone}
      onChange={(value: any) => {
        const mDate = moment(value).tz(timezone, true);
        const endOfDay = mDate.isSame(mDate.clone().startOf('day'));
        const adjustedDate = endOfDay && !startDay ? mDate.set({ hour: 23, minute: 59, second: 59 }) : mDate;
        onChange(adjustedDate ? adjustedDate.toDate() : null);
      }}
    />
  );
}
