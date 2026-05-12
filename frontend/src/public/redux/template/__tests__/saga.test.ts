// <reference types="jest" />
import { runSaga, stdChannel } from 'redux-saga';
import { call } from 'redux-saga/effects';
import { fetchTemplate } from '../saga';
import { getTemplate } from '../../../api/getTemplate';
import { ETemplateActions, TLoadTemplate } from '../actions';
import { loadFieldsetsCatalog, loadFieldsetsCatalogSuccess, loadFieldsetsCatalogFailed } from '../../fieldsets/slice';
import { ETemplateStatus } from '../../../types/redux';
import { ESubscriptionPlan } from '../../../types/account';

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
  logger: { info: jest.fn() },
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
