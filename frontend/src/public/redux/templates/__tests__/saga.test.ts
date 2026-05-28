// <reference types="jest" />
import { runSaga, stdChannel } from 'redux-saga';
import { call } from 'redux-saga/effects';

import * as getTemplatesApi from '../../../api/getTemplates';
import { IGetTemplatesResponsePaginated } from '../../../api/getTemplates';
import { ETemplatesSorting } from '../../../types/workflow';
import { LIMIT_LOAD_TEMPLATES } from '../../../constants/defaultValues';
import { handleLoadTemplateVariables } from '../saga';
import { getTemplateFields } from '../../../api/getTemplateFields';
import { buildRuntimeMergedOutputParts } from '../../../components/TemplateEdit/TaskOutputFlow/mergeTaskOutputFlow';


jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: {
      urls: {
        templates: '/templates',
        templatesTitlesByOwners: '/templates/titles-by-owners',
      },
    },
  }),
}));

jest.mock('../../../api/getTemplateFields', () => ({
  getTemplateFields: jest.fn(),
}));

jest.mock('../../../components/TemplateEdit/TaskOutputFlow/mergeTaskOutputFlow', () => ({
  buildRuntimeMergedOutputParts: jest.fn(() => []),
}));

jest.mock('../../../components/TemplateEdit/TaskForm/utils/getTaskVariables', () => ({
  getVariables: jest.fn(() => []),
}));

jest.mock('../../../components/Workflows/WorkflowsTablePage/WorkflowsTable/constants', () => ({
  SYSTEM_MERGED_OUTPUTS: [],
}));

jest.mock('../../../utils/isRequestCanceled', () => ({
  isRequestCanceled: jest.fn(() => false),
}));

jest.mock('../../../utils/logger', () => ({
  logger: { info: jest.fn() },
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { notifyApiError: jest.fn() },
}));

jest.mock('../../../utils/getErrorMessage', () => ({
  getErrorMessage: jest.fn(() => 'error'),
}));

describe('templates saga', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchTemplates', () => {
    it('calls getTemplatesByOwners with correct parameters', async () => {
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({
          count: 2,
          next: '',
          previous: '',
          results: [
            { id: 1, name: 'Template 1' },
            { id: 2, name: 'Template 2' },
          ],
        } as IGetTemplatesResponsePaginated);

      await getTemplatesApi.getTemplatesByOwners({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalledWith({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });
    });

    it('calls getTemplatesByOwners instead of getTemplates for My Workflow Templates', async () => {
      const getTemplatesMock = jest.spyOn(getTemplatesApi, 'getTemplates');
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({ count: 0, next: '', previous: '', results: [] });

      await getTemplatesApi.getTemplatesByOwners({
        offset: 0,
        limit: 30,
        sorting: ETemplatesSorting.DateDesc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalled();
      expect(getTemplatesMock).not.toHaveBeenCalled();
    });

    it('handles pagination offset correctly', async () => {
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({ count: 50, next: '', previous: '', results: [] });

      await getTemplatesApi.getTemplatesByOwners({
        offset: 30,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalledWith({
        offset: 30,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });
    });

    it('passes sorting parameter correctly', async () => {
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({ count: 0, next: '', previous: '', results: [] });

      await getTemplatesApi.getTemplatesByOwners({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.NameAsc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalledWith({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.NameAsc,
      });
    });
  });

  describe('fetchIsTemplateOwner', () => {
    it('uses getTemplates (not getTemplatesByOwners) to check ownership', async () => {
      const getTemplatesMock = jest
        .spyOn(getTemplatesApi, 'getTemplates')
        .mockResolvedValue({ count: 1, next: '', previous: '', results: [{ id: 1 }] } as IGetTemplatesResponsePaginated);

      await getTemplatesApi.getTemplates({
        limit: 1,
        isActive: true,
      });

      expect(getTemplatesMock).toHaveBeenCalledWith({
        limit: 1,
        isActive: true,
      });
    });
  });
});

describe('handleLoadTemplateVariables — empty fieldsets filtering', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  interface IDispatchedAction {
    type: string;
    payload?: unknown;
  }

  const makeFieldset = (apiName: string, fieldsCount: number) => ({
    name: `Fieldset ${apiName}`,
    description: '',
    apiName,
    order: 0,
    fields: Array.from({ length: fieldsCount }, (_, i) => ({
      apiName: `${apiName}-field-${i}`,
      name: `Field ${i}`,
      type: 'string',
      order: i,
      isRequired: false,
    })),
  });

  it('filters out fieldsets without fields when building transformedTasks', async () => {
    const fullFieldset = makeFieldset('fs-full', 2);
    const emptyFieldset = makeFieldset('fs-empty', 0);
    const taskFieldset1 = makeFieldset('fs-task-1', 1);
    const taskFieldset2 = makeFieldset('fs-task-2', 3);
    const taskEmptyFieldset = makeFieldset('fs-task-empty', 0);

    const apiResponse = {
      kickoff: {
        fields: [{ apiName: 'kf-1', name: 'KF1', type: 'string', order: 0, isRequired: false }],
        fieldsets: [fullFieldset, emptyFieldset],
      },
      tasks: [{
        id: 1,
        name: 'Task One',
        apiName: 'task-1',
        fields: [{ apiName: 'tf-1', name: 'TF1', type: 'string', order: 0, isRequired: false }],
        fieldsets: [taskFieldset1, taskFieldset2, taskEmptyFieldset],
      }],
    };

    (getTemplateFields as jest.Mock).mockResolvedValue(apiResponse);

    const channel = stdChannel();
    const dispatched: IDispatchedAction[] = [];

    function* wrapper() {
      yield call(handleLoadTemplateVariables, 42);
    }

    const saga = runSaga(
      {
        channel,
        dispatch: (action: IDispatchedAction) => {
          dispatched.push(action);
        },
        getState: () => ({}),
      },
      wrapper,
    );

    await saga.toPromise();

    expect(buildRuntimeMergedOutputParts).toHaveBeenCalledTimes(2);

    expect(buildRuntimeMergedOutputParts).toHaveBeenNthCalledWith(
      1,
      apiResponse.kickoff.fields,
      [fullFieldset],
    );

    expect(buildRuntimeMergedOutputParts).toHaveBeenNthCalledWith(
      2,
      apiResponse.tasks[0].fields,
      [taskFieldset1, taskFieldset2],
    );
  });
});
