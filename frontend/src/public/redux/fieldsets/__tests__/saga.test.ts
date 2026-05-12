// <reference types="jest" />
import { runSaga } from 'redux-saga';
import { call } from 'redux-saga/effects';

import { loadFieldsetsSaga, loadCurrentFieldsetSaga } from '../saga';
import { getFieldsets } from '../../../api/fieldsets/getFieldsets';
import { getFieldset } from '../../../api/fieldsets/getFieldset';
import { loadFieldsets, loadFieldsetsFailed, loadCurrentFieldset, loadCurrentFieldsetSuccess } from '../slice';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: {
      urls: {
        templateFieldsets: '/templates/:id/fieldsets',
        fieldset: '/fieldsets/:id',
      },
    },
  }),
}));

jest.mock('../../../api/fieldsets/getFieldsets', () => ({
  getFieldsets: jest.fn(),
}));

jest.mock('../../../api/fieldsets/getFieldset', () => ({
  getFieldset: jest.fn(),
}));

jest.mock('../../../utils/history', () => ({
  history: { replace: jest.fn(), push: jest.fn() },
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn() },
}));

jest.mock('../../../utils/logger', () => ({
  logger: { error: jest.fn() },
}));

interface IDispatchedAction {
  type: string;
  payload?: unknown;
}

describe('loadFieldsetsSaga', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const makeMockState = () => ({
    fieldsets: {
      fieldsetsList: { items: [], count: 0, offset: 0 },
      fieldsetsListSorting: '-date',
      templateId: null,
      catalogLoadedForTemplateId: null,
    },
  });

  const runLoadFieldsets = async (
    templateId: number,
    offset: number = 0,
  ) => {
    const dispatched: IDispatchedAction[] = [];
    const mockState = makeMockState();
    const action = loadFieldsets({ templateId, offset });

    function* wrapper() {
      yield call(loadFieldsetsSaga, action);
    }

    const saga = runSaga(
      {
        dispatch: (dispatchedAction: IDispatchedAction) => {
          dispatched.push(dispatchedAction);
        },
        getState: () => mockState,
      },
      wrapper,
    );

    await saga.toPromise();

    return dispatched;
  };

  describe('Redirect on non-existent template', () => {
    it('redirects to templates list on 404 API response', async () => {
      const error404 = { status: 404, message: 'Not found' };
      (getFieldsets as jest.Mock).mockRejectedValue(error404);

      const dispatched = await runLoadFieldsets(9999);

      expect(getFieldsets).toHaveBeenCalledTimes(1);

      const failedAction = dispatched.find(
        (a) => a.type === loadFieldsetsFailed.type,
      );
      expect(failedAction).toBeDefined();

      expect(history.replace).toHaveBeenCalledTimes(1);
      expect(history.replace).toHaveBeenCalledWith(ERoutes.Templates);
    });

    it('does not redirect on non-404 errors', async () => {
      const error500 = { status: 500, message: 'Internal server error' };
      (getFieldsets as jest.Mock).mockRejectedValue(error500);

      const dispatched = await runLoadFieldsets(42);

      const failedAction = dispatched.find(
        (a) => a.type === loadFieldsetsFailed.type,
      );
      expect(failedAction).toBeDefined();

      expect(history.replace).not.toHaveBeenCalled();
    });
  });
});

describe('loadCurrentFieldsetSaga', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const URL_TEMPLATE_ID = 20;
  const FIELDSET_TEMPLATE_ID = 15;
  const FIELDSET_ID = 5;

  const makeFieldset = (overrides = {}) => ({
    id: FIELDSET_ID,
    templateId: FIELDSET_TEMPLATE_ID,
    name: 'Test Fieldset',
    description: '',
    labelPosition: 'top',
    layout: 'one_column',
    order: 0,
    kickoffId: null,
    taskId: null,
    rules: [],
    fields: [],
    ...overrides,
  });

  const makeMockState = (templateId: number | null) => ({
    fieldsets: {
      fieldsetsList: { items: [], count: 0, offset: 0 },
      fieldsetsListSorting: '-date',
      templateId,
      catalogLoadedForTemplateId: null,
      currentFieldset: null,
      isCurrentFieldsetLoading: false,
    },
  });

  const runLoadCurrentFieldset = async (
    fieldsetId: number,
    urlTemplateId: number | null,
  ) => {
    const dispatched: IDispatchedAction[] = [];
    const mockState = makeMockState(urlTemplateId);
    const action = loadCurrentFieldset({ id: fieldsetId });

    function* wrapper() {
      yield call(loadCurrentFieldsetSaga, action);
    }

    const saga = runSaga(
      {
        dispatch: (dispatchedAction: IDispatchedAction) => {
          dispatched.push(dispatchedAction);
        },
        getState: () => mockState,
      },
      wrapper,
    );

    await saga.toPromise();

    return dispatched;
  };

  describe('Redirect on template ownership mismatch', () => {
    it('redirects to fieldsets list when fieldset belongs to a different template', async () => {
      (getFieldset as jest.Mock).mockResolvedValue(makeFieldset());

      const dispatched = await runLoadCurrentFieldset(FIELDSET_ID, URL_TEMPLATE_ID);

      expect(getFieldset).toHaveBeenCalledTimes(1);

      const expectedRoute = ERoutes.TemplateFieldsets.replace(':templateId', String(URL_TEMPLATE_ID));
      expect(history.replace).toHaveBeenCalledTimes(1);
      expect(history.replace).toHaveBeenCalledWith(expectedRoute);

      const successAction = dispatched.find(
        (a) => a.type === loadCurrentFieldsetSuccess.type,
      );
      expect(successAction).toBeUndefined();
    });

    it('does not redirect when fieldset belongs to the URL template', async () => {
      const matchingFieldset = makeFieldset({ templateId: URL_TEMPLATE_ID });
      (getFieldset as jest.Mock).mockResolvedValue(matchingFieldset);

      const dispatched = await runLoadCurrentFieldset(FIELDSET_ID, URL_TEMPLATE_ID);

      expect(getFieldset).toHaveBeenCalledTimes(1);
      expect(history.replace).not.toHaveBeenCalled();

      const successAction = dispatched.find(
        (a) => a.type === loadCurrentFieldsetSuccess.type,
      );
      expect(successAction).toBeDefined();
    });
  });
});
