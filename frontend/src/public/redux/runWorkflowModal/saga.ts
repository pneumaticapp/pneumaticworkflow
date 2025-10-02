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
import { EWorkflowTaskStatus } from '../../types/workflow';
import { RawPerformer } from '../../types/template';

function* runWorkflow({ payload: workflow }: TRunWorkflow) {
  yield deleteRemovedFilesFromFields(workflow.kickoff.fields);

  try {
    const isAdmin: ReturnType<typeof getIsAdmin> = yield select(getIsAdmin);
    const mappedWorkflow = mapWorkflowToRunProcess(workflow);

    const { tasks, name }: TRunProcessResponse = yield runProcess(mappedWorkflow);

    const activeTasksPerformers: RawPerformer[] = tasks.reduce((allPerformers, task) => {
      if (task.status === EWorkflowTaskStatus.Active) {
        return [...allPerformers, ...task.performers];
      }
      return allPerformers;
    }, [] as RawPerformer[]);

    const {
      authUser: { id },
    }: ReturnType<typeof getAuthUser> = yield select(getAuthUser);

    const isCurrentPerformer = activeTasksPerformers.find((item) => item.sourceId === id);
    const shouldRedirectTasks = (activeTasksPerformers && id && isCurrentPerformer) || !isAdmin;
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
