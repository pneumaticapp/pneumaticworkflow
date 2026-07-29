import { expectSaga } from 'redux-saga-test-plan';
import * as matchers from 'redux-saga-test-plan/matchers';
import { call } from 'redux-saga/effects';

import { loadBreakdownTasks } from '../actions';
import { fetchBreakdownTasks, openRunWorflowByTemplateDataSaga } from '../saga';
import { getDashboardStore } from '../../selectors/dashboard';
import { getCanAccessWorkflows } from '../../selectors/user';
import { EDashboardModes, IDashboardStore, IDashboardTask } from '../../../types/redux';
import { EDashboardTimeRange } from '../../../types/dashboard';
import { reducer } from '../reducer';
import { getDashboardWorkflowsTasks } from '../../../api/dashboard/getDashboardWorkflowsTasks';
import * as templatesSaga from '../../templates/saga';
import { openRunWorkflowModalSideMenu } from '../actions';
import { loadDatasetsMap } from '../../../components/TemplateEdit/utils/getRunnableWorkflow';
import { openRunWorkflowModal } from '../../runWorkflowModal/actions';

describe('fetchBreakdownTasks', () => {
  it('load breakdown tasks', () => {
    const mockDashboardStore: IDashboardStore = {
      counters: {
        completed: 1,
        inProgress: 1,
        overdue: 1,
        started: 1,
      },
      timeRange: EDashboardTimeRange.Today,
      breakdownItems: [],
      mode: EDashboardModes.Workflows,
      isLoading: false,
      settingsChanged: false,
      checklist: {
        isLoading: false,
        isCompleted: false,
        checks: {
          templateCreated: false,
          inviteTeam: false,
          workflowStarted: false,
          templateOwnerChanged: false,
          conditionCreated: false,
          templatePublicated: false,
        },
      },
    };

    const fetchBreakdownTasksAction = loadBreakdownTasks({ templateId: 1 });
    const mockTasks: IDashboardTask[] = [
      {
        id: 1,
        apiName: 'task-1',
        number: 1,
        name: 'Task 1',
        started: 1,
        inProgress: 1,
        overdue: 1,
        completed: 1,
      },
    ];
    jest.spyOn(templatesSaga, 'handleLoadTemplateVariables').mockImplementation(function* () {});

    function* wrapper() {
      yield call(fetchBreakdownTasks, fetchBreakdownTasksAction);
    }

    return (
      expectSaga(wrapper)
        .provide([
          [matchers.select.selector(getCanAccessWorkflows), true],
          [matchers.select.selector(getDashboardStore), mockDashboardStore],
          [matchers.call.fn(getDashboardWorkflowsTasks), mockTasks],
        ])
        .withReducer(reducer, mockDashboardStore)

        .put({
          type: 'PATCH_DASHBOARD_BREAKDOWN_ITEM',
          payload: { templateId: 1, changedFields: { tasks: mockTasks } },
        })
        .run()
    );
  });
});

describe('openRunWorflowByTemplateDataSaga — fieldset selections enrichment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('enriches fieldset field selections from datasetsMap', async () => {
    const DATASET_ID = 5;
    const DATASET_OPTIONS = ['opt-a', 'opt-b'];

    const templateData = {
      id: 10,
      name: 'Template From Side Menu',
      kickoff: {
        fields: [],
        fieldsets: [
          {
            apiName: 'fs-1',
            name: 'Fieldset 1',
            order: 0,
            fields: [
              {
                apiName: 'field-ds',
                name: 'Field With Dataset',
                type: 'string',
                isRequired: false,
                isHidden: false,
                order: 0,
                selections: [],
                dataset: DATASET_ID,
              },
              {
                apiName: 'field-no-ds',
                name: 'Field Without Dataset',
                type: 'string',
                isRequired: false,
                isHidden: false,
                order: 1,
                selections: ['original'],
                dataset: null,
              },
            ],
          },
        ],
      },
    };

    const action = openRunWorkflowModalSideMenu({
      templateData,
      ancestorTaskId: 99,
    });

    const openModalActionType = openRunWorkflowModal({} as never).type;

    function* wrapper() {
      yield call(openRunWorflowByTemplateDataSaga, action);
    }

    const { effects } = await expectSaga(wrapper)
      .provide([
        [matchers.call.fn(loadDatasetsMap), { [DATASET_ID]: DATASET_OPTIONS }],
      ])
      .run();

    const putEffects = effects.put || [];
    const openModalPut = putEffects.find(
      (effect) => effect.payload.action.type === openModalActionType,
    );

    if (!openModalPut) {
      throw new Error('Expected openRunWorkflowModal PUT not found');
    }

    const { loadedFieldsets } = openModalPut.payload.action.payload;

    expect(loadedFieldsets).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          fields: expect.arrayContaining([
            expect.objectContaining({
              apiName: 'field-ds',
              selections: DATASET_OPTIONS,
            }),
            expect.objectContaining({
              apiName: 'field-no-ds',
              selections: ['original'],
            }),
          ]),
        }),
      ]),
    );
  });
});
