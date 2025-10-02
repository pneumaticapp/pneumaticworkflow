import React from 'react';
import { isSameYear, Locale } from 'date-fns';
import { formatInTimeZone } from 'date-fns-tz';
import { enUS, ru } from 'date-fns/locale';

import { ELocale } from '../../../types/redux';

import styles from './DateFormat.css';

export interface IDateFormatProps {
  date?: string | number;
  language: string;
  timezone: string;
  dateFmt: string;
}

export const DateFormatComponent = ({ date, timezone, dateFmt, language }: IDateFormatProps) => {
  const currentDate = date ? new Date(date) : new Date();
  const mapLocale: { [key: string]: Locale } = {
    [ELocale.English]: enUS,
    [ELocale.Russian]: ru,
  };
  // We delete the year if it is the current one
  if (isSameYear(currentDate, new Date())) dateFmt = dateFmt.replace('yyy, ', '');

  return (
    <span className={styles['date']}>
      {formatInTimeZone(currentDate, timezone, dateFmt, { locale: mapLocale[language] })}
    </span>
  );
};
