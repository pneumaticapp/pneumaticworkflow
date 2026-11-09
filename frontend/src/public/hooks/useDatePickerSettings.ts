import { Locale } from 'date-fns';
import { enUS, ru } from 'date-fns/locale';
import { useSelector } from 'react-redux';
import { useIntl } from 'react-intl';

import { ELocale, IApplicationState } from '../types/redux';
import { arSY } from '../lang/dateLocale';
import { resolveLocale } from '../lang/locale';

const localeMap: { [key: string]: Locale } = {
  [ELocale.English]: enUS,
  [ELocale.Russian]: ru,
  [ELocale.Arabic]: arSY,
};

export interface IDatePickerSettings {
  locale: Locale;
  timezone: string;
  dateFdw: string;
}

export const useDatePickerSettings = (): IDatePickerSettings => {
  const { locale } = useIntl();
  const { dateFdw, timezone } = useSelector((state: IApplicationState) => state.authUser);

  return {
    locale: localeMap[resolveLocale(locale)],
    timezone,
    dateFdw,
  };
};
