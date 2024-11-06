/* eslint-disable */
/* prettier-ignore */
import { ITypedReduxAction } from '../../types/redux';
import { ESettingsTabs } from '../../types/profile';
import { actionGenerator } from '../../utils/redux';

export const enum EProfileSettingsActions {
  ChangeProfileSettingsActiveTab = 'CHANGE_PROFILE_SETTINGS_ACTIVE_TAB',
  SetProfileSettingsActiveTab = 'SET_PROFILE_SETTINGS_ACTIVE_TAB',
}

export type TChangeProfileSettingsActiveTab =
  ITypedReduxAction<EProfileSettingsActions.ChangeProfileSettingsActiveTab, ESettingsTabs>;
export const changeProfileSettingsActiveTab: (payload: ESettingsTabs) =>
TChangeProfileSettingsActiveTab =
  actionGenerator<EProfileSettingsActions.ChangeProfileSettingsActiveTab, ESettingsTabs>
  (EProfileSettingsActions.ChangeProfileSettingsActiveTab);

export type TSetProfileSettingsActiveTab =
  ITypedReduxAction<EProfileSettingsActions.SetProfileSettingsActiveTab, ESettingsTabs>;
export const setProfileSettingsActiveTab: (payload: ESettingsTabs) =>
TSetProfileSettingsActiveTab =
  actionGenerator<EProfileSettingsActions.SetProfileSettingsActiveTab, ESettingsTabs>
  (EProfileSettingsActions.SetProfileSettingsActiveTab);

export type TProfileSettingsActions =
  TChangeProfileSettingsActiveTab
  | TSetProfileSettingsActiveTab
;
