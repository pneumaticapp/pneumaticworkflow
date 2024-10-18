import { all, fork, take, call } from 'redux-saga/effects';

import { EAuthActions } from './auth/actions';
import { stopSaga } from './utils';

import { rootSaga as accountsSagas } from './accounts/saga';
import { rootSaga as genericTemplatesSagas } from './genericTemplates/saga';
import { rootSaga as authSagas } from './auth/saga';
import { rootSaga as dashboardSagas } from './dashboard/saga';
import { rootSaga as processesSagas } from './workflows/saga';
import { rootSaga as taskSagas } from './task/saga';
import { rootSaga as profileSagas } from './profile/saga';
import { rootSaga as highlightsSagas } from './highlights/saga';
import { rootSaga as templatesSagas } from './templates/saga';
import { rootSaga as selectTemplateModal } from './selectTemplateModal/saga';
import { rootSaga as templateSagas } from './template/saga';
import { rootSaga as integrationsSagas } from './integrations/saga';
import { rootSaga as notificationsSagas } from './notifications/saga';
import { rootSaga as runWorkflowModalSagas } from './runWorkflowModal/saga';
import { rootSaga as tasksSagas } from './tasks/saga';
import { rootSaga as teamSagas } from './team/saga';
import { rootSaga as menuSagas } from './menu/saga';
import { rootSaga as webhooksSagas } from './webhooks/saga';
import { rootSaga as tenantsSagas } from './tenants/saga';
import { rootSaga as pagesSagas } from './pages/saga';

export function* rootSaga() {
  while (true) {
    const tasks: unknown = yield all([
      fork(accountsSagas),
      fork(genericTemplatesSagas),
      fork(authSagas),
      fork(dashboardSagas),
      fork(processesSagas),
      fork(taskSagas),
      fork(profileSagas),
      fork(highlightsSagas),
      fork(templatesSagas),
      fork(selectTemplateModal),
      fork(templateSagas),
      fork(integrationsSagas),
      fork(notificationsSagas),
      fork(runWorkflowModalSagas),
      fork(tasksSagas),
      fork(teamSagas),
      fork(menuSagas),
      fork(webhooksSagas),
      fork(tenantsSagas),
      fork(pagesSagas),
    ]);

    yield take(EAuthActions.RedirectToLogin);
    yield call(stopSaga, tasks);
  }
}
