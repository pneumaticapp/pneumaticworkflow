import { ELocale, ITypedReduxAction } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';

export const enum ESettingsActions {
  ChangeLocale = 'CHANGE_LOCALE',
}

export type TChangeLocale = ITypedReduxAction<ESettingsActions.ChangeLocale, ELocale>;
export const changeLocale: (payload: ELocale) => TChangeLocale =
  actionGenerator<ESettingsActions.ChangeLocale, ELocale>(ESettingsActions.ChangeLocale);

export const changeLocaleSettings = (locale: ELocale) => {
  localStorage.setItem('currentLanguage', locale);

  return changeLocale(locale);
};

export type TSettingsActions =
  TChangeLocale
;
