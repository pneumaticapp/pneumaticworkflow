import { runSaga, stdChannel } from 'redux-saga';
import { call } from 'redux-saga/effects';

import { watchSaveTemplate } from '../saga';
import { ETemplateActions } from '../actions';
import { initialTemplate } from '../reducer';
import { updateTemplate } from '../../../api/updateTemplate';
import { checkSomeRouteIsActive } from '../../../utils/history';
import { NotificationManager } from '../../../components/UI/Notifications';
import { ESubscriptionPlan } from '../../../types/account';
import { EExtraFieldType, ITemplate, ITemplateClient } from '../../../types/template';
import { makeExtraField } from '../../../__stubs__/fields.factory';
import { makeKickoffClient } from '../../../__stubs__/templates.factory';
import {
  clearTemplateValidationErrors,
  removeTemplateValidationErrors,
  setTemplateValidationErrors,
} from '../../templateValidation/slice';
import { getValidationErrorEntitySnapshot } from '../../templateValidation/getValidationErrorTarget';
import type { ITemplateValidationError } from '../../templateValidation/types';

jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({ api: { urls: { templates: '/templates' } } }),
}));

jest.mock('../../../utils/history', () => ({
  history: { replace: jest.fn() },
  checkSomeRouteIsActive: jest.fn(),
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn(), notifyApiError: jest.fn() },
}));

jest.mock('../../../utils/logger', () => ({
  logger: { info: jest.fn(), error: jest.fn() },
}));

jest.mock('../../../utils/template', () => ({
  ...jest.requireActual('../../../utils/template'),
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

jest.mock('../../../utils/templates/insertId', () => ({
  insertId: jest.fn((lastState: ITemplate) => lastState),
}));

interface IDispatchedAction {
  type: string;
  payload?: unknown;
}

const kickoffField = makeExtraField({ apiName: 'field-user', type: EExtraFieldType.User, isRequired: false });

const makeTemplate = (overrides: Partial<ITemplateClient> = {}): ITemplateClient => ({
  ...initialTemplate.data,
  id: 7,
  kickoff: makeKickoffClient({ fields: [kickoffField] }),
  ...overrides,
});

const makeValidationError = (snapshotSource: unknown): ITemplateValidationError => ({
  apiName: 'field-user',
  message: 'User field must be required',
  target: { taskUuid: null, section: null, elementApiName: 'field-user' },
  entitySnapshot: getValidationErrorEntitySnapshot(snapshotSource),
});

const runSave = async (
  template: ITemplateClient,
  validationErrors: ITemplateValidationError[] = [],
  failWhileEditing?: { editedTemplate: ITemplateClient; error: unknown },
) => {
  const dispatched: IDispatchedAction[] = [];
  const channel = stdChannel();
  const state = {
    authUser: { account: { isSubscribed: false, billingPlan: ESubscriptionPlan.Free } },
    accounts: { users: [] },
    template: { data: template },
    templateValidation: { errors: validationErrors, batchId: 1, focusElementApiName: null },
  };

  if (failWhileEditing) {
    (updateTemplate as jest.Mock).mockImplementation(() => {
      state.template.data = failWhileEditing.editedTemplate;

      return Promise.reject(failWhileEditing.error);
    });
  }

  function* wrapper() {
    yield call(watchSaveTemplate);
  }

  const saga = runSaga(
    { channel, dispatch: (action: IDispatchedAction) => dispatched.push(action), getState: () => state },
    wrapper,
  );
  channel.put({ type: ETemplateActions.Save, payload: {} });
  await new Promise((resolve) => setTimeout(resolve, 50));
  saga.cancel();

  return dispatched;
};

const apiError = (apiName: string) => ({
  status: 400,
  data: {
    code: 'validation_error',
    message: 'User field must be required',
    details: { api_name: apiName, reason: 'User field must be required' },
  },
});

describe('fetchSaveTemplate validation errors', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (checkSomeRouteIsActive as jest.Mock).mockReturnValue(true);
  });

  it('stores a located validation error instead of showing the toast', async () => {
    (updateTemplate as jest.Mock).mockRejectedValue(apiError('field-user'));

    const dispatched = await runSave(makeTemplate({ isActive: true }));

    const stored = dispatched.find((action) => action.type === setTemplateValidationErrors.type);
    expect(stored?.payload).toEqual([
      expect.objectContaining({
        apiName: 'field-user',
        message: 'User field must be required',
        target: { taskUuid: null, section: null, elementApiName: 'field-user' },
        entitySnapshot: getValidationErrorEntitySnapshot(kickoffField),
      }),
    ]);
    expect(NotificationManager.notifyApiError).not.toHaveBeenCalled();
  });

  it('shows the toast instead of an inline error when the element was corrected during the request', async () => {
    const correctedTemplate = makeTemplate({
      kickoff: makeKickoffClient({ fields: [{ ...kickoffField, isRequired: true }] }),
    });

    const dispatched = await runSave(makeTemplate({ isActive: true }), [], {
      editedTemplate: correctedTemplate,
      error: apiError('field-user'),
    });

    expect(dispatched.map((action) => action.type)).not.toContain(setTemplateValidationErrors.type);
    expect(NotificationManager.notifyApiError).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ title: 'template.save-failed' }),
    );
  });

  it('shows the toast and keeps inline errors when the api_name is not in the template', async () => {
    (updateTemplate as jest.Mock).mockRejectedValue(apiError('owner-1'));

    const dispatched = await runSave(makeTemplate({ isActive: true }), [makeValidationError(kickoffField)]);

    expect(dispatched.map((action) => action.type)).not.toContain(clearTemplateValidationErrors.type);
    expect(dispatched.map((action) => action.type)).not.toContain(setTemplateValidationErrors.type);
    expect(NotificationManager.notifyApiError).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ title: 'template.save-failed', message: 'User field must be required' }),
    );
  });

  it('keeps the error after a draft save when the element did not change', async () => {
    const template = makeTemplate();
    (updateTemplate as jest.Mock).mockResolvedValue(template);

    const dispatched = await runSave(template, [makeValidationError(kickoffField)]);

    expect(dispatched.map((action) => action.type)).not.toContain(removeTemplateValidationErrors.type);
    expect(dispatched).not.toContainEqual(clearTemplateValidationErrors());
  });

  it('clears the error after a draft save when the element changed', async () => {
    const template = makeTemplate();
    (updateTemplate as jest.Mock).mockResolvedValue(template);

    const dispatched = await runSave(template, [makeValidationError({ ...kickoffField, name: 'Old name' })]);

    expect(dispatched).toContainEqual(removeTemplateValidationErrors(['field-user']));
  });

  it('clears the error after the template is saved as active', async () => {
    const template = makeTemplate({ isActive: true });
    (updateTemplate as jest.Mock).mockResolvedValue(template);

    const dispatched = await runSave(template, [makeValidationError(kickoffField)]);

    expect(dispatched).toContainEqual(clearTemplateValidationErrors());
  });

  it('keeps the errors when the client marks the template active but the server saved a draft', async () => {
    (updateTemplate as jest.Mock).mockResolvedValue(makeTemplate({ isActive: false }));

    const dispatched = await runSave(makeTemplate({ isActive: true }), [makeValidationError(kickoffField)]);

    expect(dispatched).not.toContainEqual(clearTemplateValidationErrors());
  });
});
