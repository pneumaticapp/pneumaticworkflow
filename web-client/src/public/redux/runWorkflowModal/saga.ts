import { all, fork, put, select, takeEvery } from 'redux-saga/effects';
import { mapWorkflowToRunProcess } from '../../utils/mappers';
import { runProcess, TRunProcessResponse } from '../../api/runProcess';
import { getAuthUser, getIsAdmin } from '../selectors/user';
import { ERoutes } from '../../constants/routes';
import { closeSelectTemplateModal, loadCurrentTask } from '../actions';
import { ERunWorkflowModalActions, runWorkflowFailed, runWorkflowSuccess, TRunWorkflow } from './actions';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { history } from '../../utils/history';
import { NotificationManager } from '../../components/UI/Notifications';
import { logger } from '../../utils/logger';
import { deleteRemovedFilesFromFields } from '../../api/deleteRemovedFilesFromFields';

function* runWorkflow({ payload: workflow }: TRunWorkflow) {
  yield deleteRemovedFilesFromFields(workflow.kickoff.fields);

  try {
    const isAdmin: ReturnType<typeof getIsAdmin> = yield select(getIsAdmin);
    const mappedWorkflow = mapWorkflowToRunProcess(workflow);
    const {
      currentTask: { performers: currenttaskPerformers },
      name,
    }: TRunProcessResponse = yield runProcess(mappedWorkflow);
    const {
      authUser: { id },
    }: ReturnType<typeof getAuthUser> = yield select(getAuthUser);
    const shouldRedirectTasks = (currenttaskPerformers && id && currenttaskPerformers.includes(id)) || !isAdmin;
    const nextRoute = shouldRedirectTasks ? ERoutes.Tasks : ERoutes.WorkflowsInProgress;

    yield put(runWorkflowSuccess());

    if (workflow.ancestorTaskId) {
      yield put(loadCurrentTask({ taskId: workflow.ancestorTaskId }));
    } else {
      history.push(nextRoute);
    }
    yield put(closeSelectTemplateModal());
    NotificationManager.success({ title: name, message: 'workflows.run-success' });
  } catch (error) {
    logger.info('start process error : ', error);
    yield put(runWorkflowFailed());

    NotificationManager.warning({
      message: getErrorMessage(error),
    });
  }
}

export function* watchStartProcess() {
  yield takeEvery(ERunWorkflowModalActions.RunWorkflow, runWorkflow);
}

export function* rootSaga() {
  yield all([fork(watchStartProcess)]);
}
