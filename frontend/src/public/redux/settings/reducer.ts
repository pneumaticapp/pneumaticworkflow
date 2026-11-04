import { defaultLocale, localeOptions } from '../../constants/defaultValues';
import { envLanguageCode } from '../../constants/enviroment';
import type { ISettings } from '../../types/redux';
import type { ELocale } from '../../types/locale';
import { getBrowserConfig } from '../../utils/getConfig';

import { ESettingsActions, TSettingsActions } from './actions';

const INIT_STATE: ISettings = {
  locale: getLocale(),
};

export const reducer = (state = INIT_STATE, action: TSettingsActions): ISettings => {
  switch (action.type) {
    case ESettingsActions.ChangeLocale:
      return { ...state, locale: action.payload };

    default:
      return { ...state };
  }
};

function getLocale(): ELocale {
  const { user } = getBrowserConfig();
  const localStorageLang: string | null = localStorage.getItem('currentLanguage');

  const matchedOption =
    localeOptions.find((item) => item.id === user?.language) ||
    localeOptions.find((item) => item.id === envLanguageCode) ||
    localeOptions.find((item) => item.id === localStorageLang);

  return matchedOption?.id || defaultLocale;
}
