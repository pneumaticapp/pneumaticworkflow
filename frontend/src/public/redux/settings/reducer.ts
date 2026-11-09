import { envLanguageCode } from '../../constants/enviroment';
import { getBrowserConfig } from '../../utils/getConfig';
import { resolveLocale } from '../../lang/locale';

import { ESettingsActions, TSettingsActions } from './actions';

const INIT_STATE = {
  locale: getLocale(),
};

export const reducer = (state = INIT_STATE, action: TSettingsActions) => {
  switch (action.type) {
    case ESettingsActions.ChangeLocale:
      return { ...state, locale: resolveLocale(action.payload) };

    default:
      return { ...state };
  }
};

function getLocale() {
  const { user } = getBrowserConfig();
  let localStorageLang: string | null = null;
  try {
    localStorageLang = localStorage.getItem('currentLanguage');
  } catch {
    // Storage may be unavailable in an embedded or private browsing context.
  }
  return resolveLocale(user?.language, envLanguageCode, localStorageLang);
}
