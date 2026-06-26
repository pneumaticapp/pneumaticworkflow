import { runSaga, stdChannel } from 'redux-saga';
import { call } from 'redux-saga/effects';
import { fetchTemplate, watchPatchTemplate, watchSaveTemplate } from '../saga';
import { getTemplate } from '../../../api/getTemplate';
import { updateTemplate } from '../../../api/updateTemplate';
import { ETemplateActions, TLoadTemplate } from '../actions';
import { loadFieldsetsCatalog, loadFieldsetsCatalogSuccess, loadFieldsetsCatalogFailed } from '../../fieldsets/slice';
import { ETemplateStatus } from '../../../types/redux';
import { ESubscriptionPlan } from '../../../types/account';
import { cleanTemplateReferences, mapTemplateRequest } from '../../../utils/template';
import { checkSomeRouteIsActive } from '../../../utils/history';
import { ITemplate } from '../../../types/template';

jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: {
      urls: {
        templates: '/templates',
      },
    },
  }),
}));

jest.mock('../../../api/getTemplate', () => ({
  getTemplate: jest.fn(),
}));

jest.mock('../../../utils/history', () => ({
  history: { replace: jest.fn() },
  checkSomeRouteIsActive: jest.fn(),
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn() },
}));

jest.mock('../../../utils/logger', () => ({
  logger: { info: jest.fn(), error: jest.fn() },
}));

jest.mock('../../../utils/template', () => ({
  cleanTemplateReferences: jest.fn((template: ITemplate) => template),
  getNormalizedTemplate: jest.fn((template: ITemplate) => template),
  mapTemplateRequest: jest.fn((template: ITemplate) => template),
}));

jest.mock('../../../api/updateTemplate', () => ({
  updateTemplate: jest.fn(),
}));

jest.mock('../../../api/createTemplate', () => ({
  createTemplate: jest.fn(),
}));

jest.mock('../../../utils/getErrorMessage', () => ({
  getErrorMessage: jest.fn(() => 'error'),
  isPaidFeatureError: jest.fn(() => false),
}));

jest.mock('../../../utils/templates/insertId', () => ({
  insertId: jest.fn((lastState: ITemplate, saved: ITemplate) => ({ ...lastState, id: saved.id })),
}));

describe('fetchTemplate saga', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const makeTemplate = (overrides = {}) => ({
    id: 42,
    name: 'Test Template',
    description: '',
    isActive: false,
    finalizable: false,
    dateUpdated: null,
    updatedBy: null,
    tasks: [],
    kickoff: { fields: [], fieldsets: [], description: '' },
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: 0,
    performersCount: 0,
    owners: [],
    viewers: [],
    starters: [],
    completionNotification: false,
    reminderNotification: false,
    ...overrides,
  });

  interface IMockFieldsetsOverrides {
    fieldsets?: { catalogLoadedForTemplateId: number | null };
  }

  const makeMockState = (overrides: IMockFieldsetsOverrides = {}) => ({
    authUser: {
      account: {
        isSubscribed: false,
        billingPlan: ESubscriptionPlan.Free,
      },
    },
    accounts: {
      users: [],
    },
    fieldsets: {
      catalogLoadedForTemplateId: null,
      ...overrides.fieldsets,
    },
  });

  interface IDispatchedAction {
    type: string;
    payload?: unknown;
  }

  const runFetchTemplate = async (
    templateId: number,
    mockState: ReturnType<typeof makeMockState>,
    catalogResponse: 'success' | 'failed' = 'success',
  ) => {
    const channel = stdChannel();
    const dispatched: IDispatchedAction[] = [];
    const action: TLoadTemplate = { payload: templateId, type: ETemplateActions.Load };

    function* wrapper() {
      yield call(fetchTemplate, action);
    }

    const saga = runSaga(
      {
        channel,
        dispatch: (dispathedAction: IDispatchedAction) => {
          dispatched.push(dispathedAction);

          if (dispathedAction.type === loadFieldsetsCatalog.type) {
            setTimeout(() => {
              if (catalogResponse === 'success') {
                channel.put(loadFieldsetsCatalogSuccess([]));
              } else {
                channel.put(loadFieldsetsCatalogFailed());
              }
            }, 0);
          }
        },
        getState: () => mockState,
      },
      wrapper,
    );

    await saga.toPromise();

    return dispatched;
  };

  describe('Catalog loading and status synchronization', () => {
    it('dispatches loadFieldsetsCatalog BEFORE setTemplateStatus(Saved)', async () => {
      const template = makeTemplate({ id: 42 });
      (getTemplate as jest.Mock).mockResolvedValue(template);

      const dispatched = await runFetchTemplate(42, makeMockState());

      const catalogIndex = dispatched.findIndex(
        (a) => a.type === loadFieldsetsCatalog.type,
      );
      const savedIndex = dispatched.findIndex(
        (a) => a.type === ETemplateActions.SetTemplateStatus && a.payload === ETemplateStatus.Saved,
      );

      expect(catalogIndex).toBeGreaterThan(-1);
      expect(savedIndex).toBeGreaterThan(-1);
      expect(catalogIndex).toBeLessThan(savedIndex);
    });

    it('does not dispatch any setTemplateStatus between catalog load and Saved', async () => {
      const template = makeTemplate({ id: 42 });
      (getTemplate as jest.Mock).mockResolvedValue(template);

      const dispatched = await runFetchTemplate(42, makeMockState());

      const catalogIndex = dispatched.findIndex(
        (a) => a.type === loadFieldsetsCatalog.type,
      );
      const savedIndex = dispatched.findIndex(
        (a) => a.type === ETemplateActions.SetTemplateStatus && a.payload === ETemplateStatus.Saved,
      );

      const statusActionsBetween = dispatched
        .slice(catalogIndex + 1, savedIndex)
        .filter((a) => a.type === ETemplateActions.SetTemplateStatus);

      expect(statusActionsBetween).toHaveLength(0);
    });

    it('skips catalog loading when already loaded for the same template', async () => {
      const template = makeTemplate({ id: 42 });
      (getTemplate as jest.Mock).mockResolvedValue(template);

      const mockState = makeMockState({
        fieldsets: { catalogLoadedForTemplateId: 42 },
      });

      const dispatched = await runFetchTemplate(42, mockState);

      const catalogAction = dispatched.find(
        (a) => a.type === loadFieldsetsCatalog.type,
      );
      expect(catalogAction).toBeUndefined();

      const savedAction = dispatched.find(
        (a) => a.type === ETemplateActions.SetTemplateStatus && a.payload === ETemplateStatus.Saved,
      );
      expect(savedAction).toBeDefined();
    });

    it('dispatches setTemplateStatus(Saved) even when catalog loading fails', async () => {
      const template = makeTemplate({ id: 42 });
      (getTemplate as jest.Mock).mockResolvedValue(template);

      const dispatched = await runFetchTemplate(42, makeMockState(), 'failed');

      const savedAction = dispatched.find(
        (a) => a.type === ETemplateActions.SetTemplateStatus && a.payload === ETemplateStatus.Saved,
      );
      expect(savedAction).toBeDefined();
    });

    it('blocks on take — Saved does not appear until catalog responds', async () => {
      const template = makeTemplate({ id: 42 });
      (getTemplate as jest.Mock).mockResolvedValue(template);

      const channel = stdChannel();
      const dispatched: IDispatchedAction[] = [];
      const mockState = makeMockState();
      const action: TLoadTemplate = { payload: 42, type: ETemplateActions.Load };

      function* wrapper() {
        yield call(fetchTemplate, action);
      }

      const saga = runSaga(
        {
          channel,
          dispatch: (dispathedAction: IDispatchedAction) => {
            dispatched.push(dispathedAction);
          },
          getState: () => mockState,
        },
        wrapper,
      );

      await new Promise((resolve) => setTimeout(resolve, 50));

      const savedBefore = dispatched.find(
        (a) => a.type === ETemplateActions.SetTemplateStatus && a.payload === ETemplateStatus.Saved,
      );
      expect(savedBefore).toBeUndefined();

      channel.put(loadFieldsetsCatalogSuccess([]));
      await saga.toPromise();

      const savedAfter = dispatched.find(
        (a) => a.type === ETemplateActions.SetTemplateStatus && a.payload === ETemplateStatus.Saved,
      );
      expect(savedAfter).toBeDefined();
    });
  });
});

describe('patchTemplateSaga — fieldsets reference cleanup', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const makeTemplate = (overrides = {}) => ({
    id: 42,
    name: 'Test Template',
    description: '',
    isActive: false,
    finalizable: false,
    dateUpdated: null,
    updatedBy: null,
    tasks: [],
    kickoff: { fields: [], fieldsets: [], description: '' },
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: 0,
    performersCount: 0,
    owners: [],
    viewers: [],
    starters: [],
    completionNotification: false,
    reminderNotification: false,
    ...overrides,
  });

  interface IDispatchedAction {
    type: string;
    payload?: unknown;
  }

  const makePatchMockState = (templateOverrides = {}) => ({
    authUser: {
      account: { isSubscribed: false, billingPlan: ESubscriptionPlan.Free },
    },
    accounts: { users: [] },
    template: {
      data: makeTemplate(templateOverrides),
    },
    fieldsets: {
      catalogLoadedForTemplateId: 42,
      catalogAllFieldsets: [],
    },
  });

  const runPatchTemplate = async (
    changedFields: Partial<ITemplate>,
    stateOverrides = {},
  ) => {
    const channel = stdChannel();
    const dispatched: IDispatchedAction[] = [];
    const mockState = makePatchMockState(stateOverrides);

    const saga = runSaga(
      {
        channel,
        dispatch: (action: IDispatchedAction) => {
          dispatched.push(action);
        },
        getState: () => mockState,
      },
      watchPatchTemplate,
    );

    channel.put({
      type: ETemplateActions.PatchTemplate,
      payload: { changedFields },
    });

    await new Promise((resolve) => setTimeout(resolve, 500));
    saga.cancel();

    return dispatched;
  };

  it('calls cleanTemplateReferences when tasks change', async () => {
    const newTasks = [{ uuid: 't1', name: 'Task 1', apiName: 'task-1' }];

    await runPatchTemplate({ tasks: newTasks } as Partial<ITemplate>);

    expect(cleanTemplateReferences).toHaveBeenCalledTimes(1);
    expect(cleanTemplateReferences).toHaveBeenCalledWith(
      expect.objectContaining({ tasks: newTasks }),
    );
  });

  it('calls cleanTemplateReferences when kickoff changes', async () => {
    const newKickoff = { fields: [], fieldsets: [], description: 'new kickoff desc' };

    await runPatchTemplate({ kickoff: newKickoff } as Partial<ITemplate>);

    expect(cleanTemplateReferences).toHaveBeenCalledTimes(1);
    expect(cleanTemplateReferences).toHaveBeenCalledWith(
      expect.objectContaining({ kickoff: newKickoff }),
    );
  });

  it('does not call cleanTemplateReferences when only name changes', async () => {
    await runPatchTemplate({ name: 'New Name' });

    expect(cleanTemplateReferences).not.toHaveBeenCalled();
  });
});

describe('fetchSaveTemplate — fieldsets in mapTemplateRequest', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const makeTemplate = (overrides = {}) => ({
    id: 99,
    name: 'Test Template',
    description: '',
    isActive: false,
    finalizable: false,
    dateUpdated: null,
    updatedBy: null,
    tasks: [],
    kickoff: { fields: [], fieldsets: [], description: '' },
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: 0,
    performersCount: 0,
    owners: [],
    viewers: [],
    starters: [],
    completionNotification: false,
    reminderNotification: false,
    ...overrides,
  });

  interface IDispatchedAction {
    type: string;
    payload?: unknown;
  }

  const makeSaveMockState = () => ({
    authUser: {
      account: { isSubscribed: false, billingPlan: ESubscriptionPlan.Free },
    },
    accounts: { users: [] },
    template: {
      data: makeTemplate({ id: 99 }),
    },
    fieldsets: {
      catalogLoadedForTemplateId: 99,
      catalogAllFieldsets: [],
    },
  });

  it('passes template data to mapTemplateRequest', async () => {
    const mockState = makeSaveMockState();
    (checkSomeRouteIsActive as jest.Mock).mockReturnValue(true);
    (mapTemplateRequest as jest.Mock).mockReturnValue({ id: 99, name: 'Test' });
    (updateTemplate as jest.Mock).mockResolvedValue(makeTemplate({ id: 99 }));

    const channel = stdChannel();
    const dispatched: IDispatchedAction[] = [];

    function* wrapper() {
      yield call(watchSaveTemplate);
    }

    const saga = runSaga(
      {
        channel,
        dispatch: (action: IDispatchedAction) => {
          dispatched.push(action);
        },
        getState: () => mockState,
      },
      wrapper,
    );

    channel.put({
      type: ETemplateActions.Save,
      payload: {},
    });

    await new Promise((resolve) => setTimeout(resolve, 100));
    saga.cancel();

    expect(mapTemplateRequest).toHaveBeenCalledTimes(1);
    expect(mapTemplateRequest).toHaveBeenCalledWith(
      mockState.template.data,
    );
  });
});
