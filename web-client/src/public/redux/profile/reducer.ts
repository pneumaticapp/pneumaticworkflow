/* eslint-disable */
/* prettier-ignore */
import {
  IStoreProfile,
} from '../../types/redux';
import { EProfileSettingsActions, TProfileSettingsActions } from './actions';
import { ESettingsTabs } from '../../types/profile';
import { checkSomeRouteIsActive } from '../../utils/history';
import { ERoutes } from '../../constants/routes';

const initialTab = checkSomeRouteIsActive(ERoutes.AccountSettings)
  ? ESettingsTabs.AccountSettings
  : ESettingsTabs.Profile;

export const INIT_STATE: IStoreProfile = {
  settingsTab: initialTab,
};

export const reducer = (state = INIT_STATE, action: TProfileSettingsActions): IStoreProfile => {
  switch (action.type) {
  case EProfileSettingsActions.ChangeProfileSettingsActiveTab:

    return { ...state, settingsTab: action.payload };

  default: return { ...state };
  }
};
