/* eslint-disable */
/* prettier-ignore */
import { all, fork, put, takeLatest } from 'redux-saga/effects';

import {
  EProfileSettingsActions,
  changeProfileSettingsActiveTab,
  TSetProfileSettingsActiveTab,
} from './actions';

import { ERoutes } from '../../constants/routes';
import { ESettingsTabs } from '../../types/profile';

import { history } from '../../utils/history';

function* setProfileSettingsActiveTabSorting({ payload: processesType }: TSetProfileSettingsActiveTab) {
  yield put(changeProfileSettingsActiveTab(processesType));
  if (processesType === ESettingsTabs.Profile) {
    history.push(ERoutes.Profile);
  }
  if (processesType === ESettingsTabs.AccountSettings) {
    history.push(ERoutes.AccountSettings);
  }
}

export function* watchSetProcessTypeSorting() {
  yield takeLatest(EProfileSettingsActions.SetProfileSettingsActiveTab, setProfileSettingsActiveTabSorting);
}

export function* rootSaga() {
  yield all([
    fork(watchSetProcessTypeSorting),
  ]);
}
