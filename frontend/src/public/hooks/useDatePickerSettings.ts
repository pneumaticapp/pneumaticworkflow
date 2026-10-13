import { Locale } from 'date-fns';
import { enUS, ru } from 'date-fns/locale';
import { useSelector } from 'react-redux';

import { ELocale, IApplicationState } from '../types/redux';

const localeMap: { [key: string]: Locale } = {
  [ELocale.English]: enUS,
  [ELocale.Russian]: ru,
};

export interface IDatePickerSettings {
  locale: Locale;
  timezone: string;
  dateFdw: string;
}

export const useDatePickerSettings = (): IDatePickerSettings => {
  const { dateFdw, language, timezone } = useSelector((state: IApplicationState) => state.authUser);

  return {
    locale: localeMap[language],
    timezone,
    dateFdw,
  };
};
