/* eslint-disable */
/* prettier-ignore */
import { expectSaga } from 'redux-saga-test-plan';
import * as matchers from 'redux-saga-test-plan/matchers';

import { loadBreakdownTasks } from '../actions';
import { fetchBreakdownTasks } from '../saga';
import { getDashboardStore } from '../../selectors/dashboard';
import { getIsAdmin } from '../../selectors/user';
import { EDashboardModes, IDashboardStore, IDashboardTask } from '../../../types/redux';
import { EDashboardTimeRange } from '../../../types/dashboard';
import { reducer } from '../reducer';
import { getDashboardWorkflowsTasks } from '../../../api/dashboard/getDashboardWorkflowsTasks';
import * as templatesSaga from '../../templates/saga';

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
    const mockTasks: IDashboardTask[] = [{
      id: 1,
      number: 1,
      name: 'Task 1',
      started: 1,
      inProgress: 1,
      overdue: 1,
      completed: 1,
    }];
    jest.spyOn(templatesSaga, 'handleLoadTemplateVariables').mockImplementation(function* () { });

    // tslint:disable-next-line: no-any
    return expectSaga(fetchBreakdownTasks as any, fetchBreakdownTasksAction)
      .provide([
        [matchers.select.selector(getIsAdmin), true],
        [matchers.select.selector(getDashboardStore), mockDashboardStore],
        [matchers.call.fn(getDashboardWorkflowsTasks), mockTasks],
      ])
      .withReducer(reducer, mockDashboardStore)

      // assert dispatch the following action
      .put({ type: 'PATCH_DASHBOARD_BREAKDOWN_ITEM', payload: { templateId: 1, changedFields: { tasks: mockTasks } } })
      .run();
  });
});
