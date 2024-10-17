/* eslint-disable */
/* prettier-ignore */
import { cancel } from 'redux-saga/effects';

import { ERoutes } from '../../constants/routes';
import { history } from '../../utils/history';

// tslint:disable-next-line:no-any
export function* stopSaga(tasks: any) {
  yield cancel(tasks);
  history.push(ERoutes.Login);
}
