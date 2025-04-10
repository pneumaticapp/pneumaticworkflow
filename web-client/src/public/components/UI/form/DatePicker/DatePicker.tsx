import React, { useRef, useState } from 'react';
import DatePicker from 'react-datepicker';
import { Locale } from 'date-fns';
import { enUS, ru } from 'date-fns/locale';
import moment from 'moment-timezone';
import { useSelector } from 'react-redux';

import { CustomInput, CustomCalendarContainer } from './components';
import { ELocale, IApplicationState } from '../../../../types/redux';
import { IDatePickerProps } from './types';

import 'react-datepicker/dist/react-datepicker.css';
import '../../../../assets/css/library/react-datepicker.css';
import styles from './DatePicker.modules.css';



export function DatePickerCustom({
  selected,
  onChange,
  startDay,
  showTimeInput,
  ...props
}: IDatePickerProps) {
  const { dateFdw, language, timezone } = useSelector((state: IApplicationState) => state.authUser);
  const [tempDate, setTempDate] = useState<Date | null>(null);
  const datePickerRef = useRef<any>(null);
  const selectedDate = selected ? moment(selected).tz(timezone, false).format('YYYY-MM-DDTHH:mm:ss') as unknown as Date : null;
  const mapLocale: { [key: string]: Locale } = {
    [ELocale.English]: enUS,
    [ELocale.Russian]: ru,
  };

  const formatDateValue = (date: Date) => {
    return moment(date).tz(timezone, false).format('MMM DD, yyyy');
  };

  const renderCalendarContainer = (rest: any) => {
    return (
      <CustomCalendarContainer
        onChange={(value)=>{
          handleChangeDate(value);
          setTempDate(null);
        }}
        selected={tempDate}
        {...rest}
      />
    );
  };

  const handleChangeDate = (date: Date | null) => {
    datePickerRef.current?.setOpen(false);

    if (date) {
      const mDate = moment(date).tz(timezone, true);
      const endOfDay = mDate.isSame(mDate.clone().startOf('day'));
      const adjustedDate = endOfDay && !startDay ? mDate.set({ hour: 23, minute: 59, second: 59 }) : mDate;
      onChange(adjustedDate ? adjustedDate.toDate() : null);
    } else {
      onChange(null);
    }
  };

  const handleChange = (date: Date | null) => {
    setTempDate(date);
  };

  return (
    <div className={styles['date-picker']}>
      <DatePicker
        ref={datePickerRef}
        customInput={<CustomInput  />}
        startDay={startDay}
        shouldCloseOnSelect={false}
        locale={mapLocale[language]}
        selected={tempDate || selectedDate}
        value={selectedDate ? formatDateValue(selectedDate) : ''}
        calendarStartDay={dateFdw}
        utcOffset={timezone}
        onChange={!showTimeInput ? handleChange : handleChangeDate}
        calendarContainer={!showTimeInput ? renderCalendarContainer : undefined}
        {...props}
      />
    </div>
  );
}
