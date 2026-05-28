
import { runSaga } from 'redux-saga';
import { call } from 'redux-saga/effects';

import { loadFieldsetsSaga, loadCurrentFieldsetSaga, deleteFieldsetSaga } from '../saga';
import { getFieldsets } from '../../../api/fieldsets/getFieldsets';
import { getFieldset } from '../../../api/fieldsets/getFieldset';
import { deleteFieldset } from '../../../api/fieldsets/deleteFieldset';
import {
  loadFieldsets, loadFieldsetsSuccess, loadFieldsetsFailed,
  loadCurrentFieldset, loadCurrentFieldsetSuccess,
  removeFieldsetFromList,
  loadFieldsetsCatalog,
} from '../slice';
import { initialState } from '../slice';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';
import { EFieldsetsSorting } from '../../../types/fieldset';
import { isRequestCanceled } from '../../../utils/isRequestCanceled';

jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: { urls: { templateFieldsets: '/templates/:id/fieldsets', fieldset: '/fieldsets/:id' } },
  }),
}));

jest.mock('../../../api/fieldsets/getFieldsets', () => ({ getFieldsets: jest.fn() }));
jest.mock('../../../api/fieldsets/getFieldset', () => ({ getFieldset: jest.fn() }));
jest.mock('../../../api/fieldsets/createFieldset', () => ({ createFieldset: jest.fn() }));
jest.mock('../../../api/fieldsets/updateFieldset', () => ({ updateFieldset: jest.fn() }));
jest.mock('../../../api/fieldsets/deleteFieldset', () => ({ deleteFieldset: jest.fn() }));

jest.mock('../../../utils/history', () => ({
  history: { replace: jest.fn(), push: jest.fn() },
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn() },
}));

jest.mock('../../../utils/logger', () => ({
  logger: { error: jest.fn() },
}));

jest.mock('../../../utils/isRequestCanceled', () => ({
  isRequestCanceled: jest.fn(() => false),
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

  describe('redirect on non-existent template', () => {
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

  describe('redirect on template ownership mismatch', () => {
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

  it('dispatches success without template check when URL templateId is null', async () => {
    const fieldset = makeFieldset({ templateId: 99 });
    (getFieldset as jest.Mock).mockResolvedValue(fieldset);

    const dispatched = await runLoadCurrentFieldset(FIELDSET_ID, null);

    const successAction = dispatched.find((a) => a.type === loadCurrentFieldsetSuccess.type);
    expect(successAction).toBeDefined();
    expect(history.replace).not.toHaveBeenCalled();
  });
});

describe('loadFieldsetsSaga — additional cases', () => {
  beforeEach(() => { jest.clearAllMocks(); });

  const runSagaHelper = async (
    saga: (...args: unknown[]) => Generator,
    action: { type: string; payload?: unknown },
    stateOverrides: Record<string, unknown> = {},
  ) => {
    const dispatched: { type: string; payload?: unknown }[] = [];
    const fieldsets = { ...initialState };
    Object.keys(stateOverrides).forEach((key) => {
      (fieldsets as Record<string, unknown>)[key] = stateOverrides[key];
    });
    const state = { fieldsets };

    function* wrapper() {
      yield call(saga, action);
    }

    await runSaga(
      {
        dispatch: (a: { type: string; payload?: unknown }) => dispatched.push(a),
        getState: () => state,
      },
      wrapper,
    ).toPromise();

    return dispatched;
  };

  it('offset=0: passes offset*30, sorting from store, dispatches success', async () => {
    const apiResponse = { count: 2, results: [{ id: 1 }, { id: 2 }] };
    (getFieldsets as jest.Mock).mockResolvedValue(apiResponse);

    const dispatched = await runSagaHelper(
      loadFieldsetsSaga,
      loadFieldsets({ offset: 0, templateId: 10 }),
      { fieldsetsListSorting: EFieldsetsSorting.NameAsc },
    );

    expect(getFieldsets).toHaveBeenCalledTimes(1);
    expect(getFieldsets).toHaveBeenCalledWith(
      expect.objectContaining({
        templateId: 10,
        offset: 0,
        limit: 30,
        ordering: EFieldsetsSorting.NameAsc,
      }),
    );

    expect(dispatched).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          type: loadFieldsetsSuccess.type,
          payload: { count: 2, offset: 0, items: [{ id: 1 }, { id: 2 }] },
        }),
      ]),
    );
  });

  it('isRequestCanceled — does not dispatch failed', async () => {
    (getFieldsets as jest.Mock).mockRejectedValue(new Error('canceled'));
    (isRequestCanceled as jest.Mock).mockReturnValueOnce(true);

    const dispatched = await runSagaHelper(
      loadFieldsetsSaga,
      loadFieldsets({ offset: 0, templateId: 10 }),
    );

    expect(dispatched).toEqual([]);
  });
});

describe('deleteFieldsetSaga', () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it('happy: removes from list, reloads catalog, calls onSuccess', async () => {
    (deleteFieldset as jest.Mock).mockResolvedValue(undefined);
    const onSuccess = jest.fn();

    const dispatched: { type: string; payload?: unknown }[] = [];
    const state = { fieldsets: { ...initialState, templateId: 10 } };

    await runSaga(
      {
        dispatch: (a: { type: string; payload?: unknown }) => dispatched.push(a),
        getState: () => state,
      },
      function* wrapper() {
        yield call(deleteFieldsetSaga, {
          type: 'fieldsets/deleteFieldsetAction',
          payload: { id: 5, onSuccess },
        });
      },
    ).toPromise();

    expect(deleteFieldset).toHaveBeenCalledTimes(1);
    expect(deleteFieldset).toHaveBeenCalledWith({ id: 5 });
    expect(dispatched).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ type: removeFieldsetFromList.type, payload: 5 }),
        expect.objectContaining({ type: loadFieldsetsCatalog.type }),
      ]),
    );
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it('error: onSuccess is NOT called', async () => {
    (deleteFieldset as jest.Mock).mockRejectedValue(new Error('fail'));
    const onSuccess = jest.fn();

    const dispatched: { type: string; payload?: unknown }[] = [];
    const state = { fieldsets: { ...initialState, templateId: 10 } };

    await runSaga(
      {
        dispatch: (a: { type: string; payload?: unknown }) => dispatched.push(a),
        getState: () => state,
      },
      function* wrapper() {
        yield call(deleteFieldsetSaga, {
          type: 'fieldsets/deleteFieldsetAction',
          payload: { id: 5, onSuccess },
        });
      },
    ).toPromise();

    expect(onSuccess).not.toHaveBeenCalled();
    expect(dispatched).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ type: loadFieldsetsFailed.type }),
      ]),
    );
  });
});
