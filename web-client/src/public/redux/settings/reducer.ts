/* eslint-disable @typescript-eslint/default-param-last */
import { defaultLocale, localeOptions } from '../../constants/defaultValues';
import { envLanguageCode } from '../../constants/enviroment';
import { getBrowserConfig } from '../../utils/getConfig';

import { ESettingsActions, TSettingsActions } from './actions';


const INIT_STATE = {
  locale: getLocale(),
};

export const reducer = (state = INIT_STATE, action: TSettingsActions) => {
  switch (action.type) {
    case ESettingsActions.ChangeLocale:
      return { ...state, locale: action.payload};

    default: return { ...state };
  }
};

function getLocale() {
  const { user } = getBrowserConfig();
  const localStorageLang: string | null = localStorage.getItem('currentLanguage');

  if (user?.language && localeOptions.find((item) => item.id === user.language)) return user.language;
  if (envLanguageCode && localeOptions.find((item) => item.id === envLanguageCode)) return envLanguageCode;
  if (localStorageLang && localeOptions.find((item) => item.id === localStorageLang)) return localStorageLang;

  return defaultLocale;
}
