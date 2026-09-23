import { runSaga } from 'redux-saga';
import { call, takeEvery } from 'redux-saga/effects';

import { makeExtraField } from '../../../__stubs__/fields.factory';
import { makeFieldsetRuntime, makeFieldsetTaskAPI } from '../../../__stubs__/fieldsets.factory';
import { makeTemplateResponse } from '../../../__stubs__/templates.factory';
import { makeWorkflowResponse } from '../../../__stubs__/workflows.factory';
import * as deleteApi from '../../../api/deleteWorkflow';
import * as finishWorkflowApi from '../../../api/finishWorkflow';
import { getTemplate } from '../../../api/getTemplate';
import { getTemplateSteps } from '../../../api/getTemplateSteps';
import { getWorkflow } from '../../../api/getWorkflow';
import { NotificationManager } from '../../../components/UI/Notifications';
import { getClonedKickoff } from '../../../components/Workflows/WorkflowsGridPage/WorkflowCard/utils/getClonedKickoff';
import { getRunnableWorkflow, loadDatasetsMap } from '../../../components/TemplateEdit/utils/getRunnableWorkflow';
import { ERoutes } from '../../../constants/routes';
import { EExtraFieldType, IKickoff } from '../../../types/template';
import { history } from '../../../utils/history';
import { mapTemplateFieldsetsToRuntime } from '../../../utils/mapTemplateFieldsetsToRuntime';
import { handleLoadTemplateVariables } from '../../templates/saga';
import {
  watchCloneWorkflow,
  cloneWorkflowSaga,
  deleteWorkflowSaga,
  watchDeleteWorfklow,
  watchReturnWorkflowToTask,
  returnWorkflowToTaskSaga,
  setWorkflowFinishedSaga,
  fetchFilterSteps,
  handleOpenWorkflowLogPopup,
} from '../saga';
import {
  cloneWorkflowAction,
  deleteWorkflowAction,
  loadFilterSteps,
  openWorkflowLogPopup,
  returnWorkflowToTaskAction,
  setWorkflowFinished,
} from '../slice';

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
  handleLoadTemplateVariables: jest.fn(function* handleLoadTemplateVariablesMock() {
    yield undefined;
  }),
}));

jest.mock('../../../utils/dateTime', () => ({
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
  it('updates the workflow detail URL through router history', () => {
    const replaceHistory = jest.spyOn(history, 'replace').mockImplementation(() => undefined);
    const expectedUrl = ERoutes.WorkflowDetail.replace(':id', '42') + history.location.search;
    const saga = handleOpenWorkflowLogPopup(
      openWorkflowLogPopup({
        workflowId: 42,
        shouldSetWorkflowDetailUrl: true,
      }),
    );

    saga.next();

    expect(replaceHistory).toHaveBeenCalledWith(expectedUrl);
    replaceHistory.mockRestore();
  });

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
    ])('for the function %s, calls takeEvery with parameters %s and %s', (testingFn, action, expectedFn) => {
      const result = (testingFn as () => Generator)();

      expect(result.next().value).toEqual(takeEvery(action, expectedFn));
    });
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

  const mockTemplate = makeTemplateResponse({
    id: 10,
    name: 'Test Template',
    kickoff: mockKickoff,
  });

  const mockWorkflowKickoff = { id: 1, description: '', output: [], fieldsets: [] };

  const mockWorkflow = makeWorkflowResponse({
    id: 1,
    name: 'Test WF',
    kickoff: mockWorkflowKickoff,
  });

  const mockLoadedFieldsets = [makeFieldsetRuntime({ apiNameBinding: 'fs-1', name: 'Fieldset 1' })];

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
        dispatch: (a: IDispatchedAction) => {
          dispatched.push(a);
        },
        getState: () => ({ authUser: { timezone: 'UTC' } }),
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

  it('passes kickoff with mapped runtime fieldsets to getClonedKickoff', async () => {
    const backendKickoff = {
      id: 1,
      description: '',
      output: [makeExtraField({ apiName: 'date-f1', type: EExtraFieldType.Date, value: 1725134400 })],
      fieldsets: [
        makeFieldsetTaskAPI({
          id: 99,
          apiName: 'backend-fieldset-1',
          fields: [makeExtraField({ apiName: 'date-f2', type: EExtraFieldType.Date, value: 1725134400 })],
        }),
      ],
    };

    const workflowWithBackendFieldsets = makeWorkflowResponse({
      id: 1,
      name: 'Test WF',
      kickoff: backendKickoff,
    });

    (getWorkflow as jest.Mock).mockResolvedValue(workflowWithBackendFieldsets);
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
        dispatch: (dispatcedAction: IDispatchedAction) => {
          dispatched.push(dispatcedAction);
        },
        getState: () => ({ authUser: { timezone: 'UTC' } }),
      },
      wrapper,
    ).toPromise();

    const clonedKickoffCall = (getClonedKickoff as jest.Mock).mock.calls[0];
    const mappedKickoff = clonedKickoffCall[0];

    expect(mappedKickoff.fieldsets).toHaveLength(1);
    expect(mappedKickoff.fieldsets[0].apiNameBinding).toBe('backend-fieldset-1');
    expect('id' in mappedKickoff.fieldsets[0]).toBe(false);

    expect(mappedKickoff.output[0].value).toBe(1725134400);
    expect(mappedKickoff.fieldsets[0].fields[0].value).toBe(1725134400);
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

    (getTemplateSteps as jest.Mock).mockResolvedValue([{ apiName: 'step-1', name: 'Step 1' }]);

    const dispatched: IDispatchedAction[] = [];

    const action = loadFilterSteps({
      templateId: TEMPLATE_ID,
    });

    function* wrapper() {
      yield call(fetchFilterSteps, action);
    }

    await runSaga(
      {
        dispatch: (a: IDispatchedAction) => {
          dispatched.push(a);
        },
        getState: () => ({}),
      },
      wrapper,
    ).toPromise();

    expect(handleLoadTemplateVariables).toHaveBeenCalledTimes(1);
    expect(handleLoadTemplateVariables).toHaveBeenCalledWith(TEMPLATE_ID);
  });
});
