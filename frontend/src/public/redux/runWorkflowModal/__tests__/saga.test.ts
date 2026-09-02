import { expectSaga } from 'redux-saga-test-plan';
import * as matchers from 'redux-saga-test-plan/matchers';
import { StaticProvider } from 'redux-saga-test-plan/providers';

import * as runProcessApi from '../../../api/runProcess';
import { history } from '../../../utils/history';
import { getAuthUser, getIsAdmin, getUsers } from '../../selectors/user';
import { runWorkflow } from '../actions';
import { rootSaga } from '../saga';
import { ERoutes } from '../../../constants/routes';
import { EWorkflowTaskStatus } from '../../../types/workflow';
import { loadCurrentTask } from '../../actions';
import { IRunWorkflow } from '../../../components/WorkflowEditPopup/types';

jest.mock('../../../utils/history', () => ({
  history: { push: jest.fn(), replace: jest.fn() },
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { success: jest.fn(), warning: jest.fn() },
}));

const ANCESTOR_TASK_ID = 77;
const CURRENT_USER_ID = 5;

const buildWorkflow = (overrides: Partial<IRunWorkflow> = {}): IRunWorkflow =>
  ({
    id: 1,
    name: 'Workflow',
    tasksCount: 1,
    performersCount: 1,
    kickoff: { description: '', fields: [], fieldsets: [] },
    ...overrides,
  } as IRunWorkflow);

/** One active task assigned to somebody else, so the redirect target is the workflows list. */
const runProcessResponse = {
  name: 'Workflow',
  status: 0,
  tasks: [{ status: EWorkflowTaskStatus.Active, performers: [{ sourceId: 999 }] }],
};

const provideCommon = (): StaticProvider[] => [
  [matchers.select.selector(getUsers), []],
  [matchers.select.selector(getIsAdmin), true],
  [matchers.select.selector(getAuthUser), { authUser: { id: CURRENT_USER_ID } }],
];

describe('runWorkflow saga', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(runProcessApi, 'runProcess').mockResolvedValue(runProcessResponse as any);
  });

  it('does not navigate away when the workflow is started as a sub-workflow', () => {
    const workflow = buildWorkflow({ ancestorTaskId: ANCESTOR_TASK_ID });

    return expectSaga(rootSaga)
      .provide(provideCommon())
      .put(loadCurrentTask({ taskId: ANCESTOR_TASK_ID }))
      .dispatch(runWorkflow(workflow))
      .silentRun()
      .then(() => {
        expect(history.push).not.toHaveBeenCalled();
      });
  });

  it('navigates to the workflows list when a standalone workflow is started', () => {
    const workflow = buildWorkflow();

    return expectSaga(rootSaga)
      .provide(provideCommon())
      .dispatch(runWorkflow(workflow))
      .silentRun()
      .then(() => {
        expect(history.push).toHaveBeenCalledWith(ERoutes.WorkflowsInProgress);
      });
  });
});
