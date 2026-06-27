import {
  watchCloneWorkflow,
  cloneWorkflowSaga,
  deleteWorkflowSaga,
  watchDeleteWorfklow,
  watchReturnWorkflowToTask,
  returnWorkflowToTaskSaga,
  setWorkflowFinishedSaga,
  fetchFilterSteps,
} from '../saga';
import * as deleteApi from '../../../api/deleteWorkflow';
import * as finishWorkflowApi from '../../../api/finishWorkflow';
import { NotificationManager } from '../../../components/UI/Notifications';
import { cloneWorkflowAction, deleteWorkflowAction, returnWorkflowToTaskAction, setWorkflowFinished } from '../slice';
import { runSaga } from 'redux-saga';
import { call } from 'redux-saga/effects';
import { getWorkflow } from '../../../api/getWorkflow';
import { getTemplate } from '../../../api/getTemplate';
import {
  loadDatasetsMap,
  getRunnableWorkflow,
} from '../../../components/TemplateEdit/utils/getRunnableWorkflow';
import { mapTemplateFieldsetsToRuntime } from '../../../utils/mapTemplateFieldsetsToRuntime';
import { getClonedKickoff } from '../../../components/Workflows/WorkflowsGridPage/WorkflowCard/utils/getClonedKickoff';
import { getTemplateSteps } from '../../../api/getTemplateSteps';
import { handleLoadTemplateVariables } from '../../templates/saga';
import { IFieldsetData, IKickoff } from '../../../types/template';
import { loadFilterSteps } from '../slice';

jest.mock('../../../api/getWorkflow', () => ({
  getWorkflow: jest.fn(),
}));

jest.mock('../../../api/getTemplate', () => ({
  getTemplate: jest.fn(),
}));

jest.mock('../../../components/TemplateEdit/utils/getRunnableWorkflow', () => ({
  loadDatasetsMap: jest.fn(),
  getRunnableWorkflow: jest.fn(),
}));

jest.mock('../../../utils/mapTemplateFieldsetsToRuntime', () => ({
  mapTemplateFieldsetsToRuntime: jest.fn(),
}));

jest.mock('../../../components/Workflows/WorkflowsGridPage/WorkflowCard/utils/getClonedKickoff', () => ({
  getClonedKickoff: jest.fn(),
}));

jest.mock('../../../api/getTemplateSteps', () => ({
  getTemplateSteps: jest.fn(),
}));

jest.mock('../../templates/saga', () => ({
  handleLoadTemplateVariables: jest.fn(function* () {}),
}));

jest.mock('../../../utils/dateTime', () => ({
  formatDateToISOInWorkflow: jest.fn((x) => x),
  toTspDate: jest.fn(),
}));

jest.mock('../../../utils/logger', () => ({
  logger: { info: jest.fn(), error: jest.fn() },
}));

jest.mock('../../../utils/getErrorMessage', () => ({
  getErrorMessage: jest.fn(() => 'error'),
}));

jest.mock('../../../utils/isRequestCanceled', () => ({
  isRequestCanceled: jest.fn(() => false),
}));

describe('workflows saga', () => {
  it('deleteWorkflowSaga work', () => {
    const saga = deleteWorkflowSaga({ type: deleteWorkflowAction.type, payload: { workflowId: 1 } });
    const deleteApiMock = jest.spyOn(deleteApi, 'deleteWorkflow').mockImplementation(() => Promise.resolve());
    const notificationManagerSuccessMock = jest.spyOn(NotificationManager, 'success');
    saga.next();
    saga.next();
    saga.next();
    expect(notificationManagerSuccessMock).toHaveBeenCalled();
    expect(deleteApiMock).toHaveBeenCalled();
  });
  it('setWorkflowFinishedSaga work', () => {
    const saga = setWorkflowFinishedSaga({
      type: setWorkflowFinished.type,
      payload: {
        workflowId: 1,
        onWorkflowEnded: () => {},
      },
    });
    const finishWorkflowApiMock = jest
      .spyOn(finishWorkflowApi, 'finishWorkflow')
      .mockImplementation(() => Promise.resolve());
    const notificationManagerSuccessMock = jest.spyOn(NotificationManager, 'success');
    saga.next();
    saga.next();
    expect(finishWorkflowApiMock).toHaveBeenCalled();
    expect(notificationManagerSuccessMock).toHaveBeenCalled();
  });
  describe('generator', () => {
    it.each([
      [watchCloneWorkflow, cloneWorkflowAction.type, cloneWorkflowSaga],
      [watchDeleteWorfklow, deleteWorkflowAction.type, deleteWorkflowSaga],
      [watchReturnWorkflowToTask, returnWorkflowToTaskAction.type, returnWorkflowToTaskSaga],
    ])(
      'for the function %s, calls takeEvery with parameters %s and %s',
      (testingFn, _action, _expectedFn) => {
        const result = (testingFn as () => Generator)();
        result.next();
      },
    );
  });
});

describe('cloneWorkflowSaga — fieldsets loading on clone', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  interface IDispatchedAction {
    type: string;
    payload?: unknown;
  }

  const mockKickoff: IKickoff = { fields: [], fieldsets: [], description: '' };

  const mockTemplate = {
    id: 10,
    name: 'Test Template',
    kickoff: mockKickoff,
    tasks: [],
    description: '',
    isActive: true,
    finalizable: false,
    dateUpdated: null,
    updatedBy: null,
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: 0,
    performersCount: 0,
    owners: [],
    completionNotification: false,
    reminderNotification: false,
  };

  const mockWorkflow = {
    id: 1,
    name: 'Test WF',
    kickoff: mockKickoff,
    tasks: [],
    status: 'running',
  };

  const mockLoadedFieldsets: Pick<IFieldsetData, 'apiName' | 'apiNameBinding' | 'name' | 'fields' | 'order'>[] = [
    { apiName: 'fs-1', apiNameBinding: 'fs-1', name: 'Fieldset 1', fields: [], order: 0 },
  ];

  const mockDatasetsMap: Record<number, string[]> = {};

  it('loads fieldsets, enriches datasets and passes to getRunnableWorkflow', async () => {
    (getWorkflow as jest.Mock).mockResolvedValue(mockWorkflow);
    (getTemplate as jest.Mock).mockResolvedValue(mockTemplate);
    (mapTemplateFieldsetsToRuntime as jest.Mock).mockReturnValue({
      normalizedTemplate: mockTemplate,
      loadedFieldsets: mockLoadedFieldsets,
    });
    (loadDatasetsMap as jest.Mock).mockResolvedValue(mockDatasetsMap);
    (getRunnableWorkflow as jest.Mock).mockReturnValue({
      templateId: 10,
      kickoff: mockKickoff,
    });
    (getClonedKickoff as jest.Mock).mockReturnValue(mockKickoff);

    const dispatched: IDispatchedAction[] = [];

    const action = cloneWorkflowAction({
      workflowId: 1,
      workflowName: 'Test WF',
      templateId: 10,
    });

    function* wrapper() {
      yield call(cloneWorkflowSaga, action);
    }

    await runSaga(
      {
        dispatch: (a: IDispatchedAction) => { dispatched.push(a); },
        getState: () => ({}),
      },
      wrapper,
    ).toPromise();

    expect(mapTemplateFieldsetsToRuntime).toHaveBeenCalledTimes(1);
    expect(mapTemplateFieldsetsToRuntime).toHaveBeenCalledWith(mockTemplate);

    expect(loadDatasetsMap).toHaveBeenCalledTimes(1);
    expect(loadDatasetsMap).toHaveBeenCalledWith(mockTemplate.kickoff, mockLoadedFieldsets);

    expect(getRunnableWorkflow).toHaveBeenCalledTimes(1);
    expect(getRunnableWorkflow).toHaveBeenCalledWith(mockTemplate, mockDatasetsMap, mockLoadedFieldsets);
  });
});

describe('fetchFilterSteps — fieldsets variables loading for filters', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  interface IDispatchedAction {
    type: string;
    payload?: unknown;
  }

  it('calls handleLoadTemplateVariables with templateId', async () => {
    const TEMPLATE_ID = 42;

    (getTemplateSteps as jest.Mock).mockResolvedValue([
      { apiName: 'step-1', name: 'Step 1' },
    ]);

    const dispatched: IDispatchedAction[] = [];

    const action = loadFilterSteps({
      templateId: TEMPLATE_ID,
    });

    function* wrapper() {
      yield call(fetchFilterSteps, action);
    }

    await runSaga(
      {
        dispatch: (a: IDispatchedAction) => { dispatched.push(a); },
        getState: () => ({}),
      },
      wrapper,
    ).toPromise();

    expect(handleLoadTemplateVariables).toHaveBeenCalledTimes(1);
    expect(handleLoadTemplateVariables).toHaveBeenCalledWith(TEMPLATE_ID);
  });
});
