import { runSaga } from 'redux-saga';

import {
  createAIAgent as createAIAgentApi,
  createAIProvider as createAIProviderApi,
  createAIProviderByVendor as createAIProviderByVendorApi,
  getAIAgents as getAIAgentsApi,
  getAIProviders as getAIProvidersApi,
} from '../../../api/ai';
import { createAIAgentSaga, createAIProviderByVendorSaga, createAIProviderSaga } from '../saga';
import {
  createAIAgent,
  createAIAgentFailed,
  createAIAgentSuccess,
  createAIProvider,
  createAIProviderByVendor,
  createAIProviderFailed,
  createAIProviderSuccess,
} from '../slice';
import { closeCreateUserModal } from '../../accounts/slice';

jest.mock('../../../api/ai', () => ({
  createAIAgent: jest.fn(),
  createAIProvider: jest.fn(),
  createAIProviderByVendor: jest.fn(),
  getAIAgents: jest.fn(),
  getAIProviders: jest.fn(),
}));
jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { success: jest.fn(), warning: jest.fn() },
}));
jest.mock('../../../utils/logger', () => ({ logger: { error: jest.fn() } }));

describe('AI creation sagas', () => {
  const agentData = {
    name: 'Agent',
    providerId: 1,
    model: 'model',
    systemPrompt: 'Prompt',
    photo: null,
    isActive: true,
  };
  const actions: unknown[] = [];

  const run = async (saga: (...args: any[]) => Generator, action: object) => {
    await runSaga(
      {
        dispatch: (dispatched) => {
          actions.push(dispatched);
        },
        getState: () => ({}),
      },
      saga,
      action,
    ).toPromise();
  };

  beforeEach(() => {
    actions.length = 0;
    jest.clearAllMocks();
    (createAIAgentApi as jest.Mock).mockResolvedValue({});
    (createAIProviderApi as jest.Mock).mockResolvedValue({});
    (createAIProviderByVendorApi as jest.Mock).mockResolvedValue({});
    (getAIAgentsApi as jest.Mock).mockResolvedValue([]);
    (getAIProvidersApi as jest.Mock).mockResolvedValue([]);
  });

  it('marks agent creation successful when POST succeeds even if the list refresh fails', async () => {
    (getAIAgentsApi as jest.Mock).mockRejectedValue(new Error('Refresh failed'));
    const request = createAIAgent(agentData);
    await run(createAIAgentSaga, request);

    expect(actions).toContainEqual(createAIAgentSuccess());
    expect(actions).toContainEqual(closeCreateUserModal());
    expect(actions).not.toContainEqual(createAIAgentFailed());
    expect(createAIAgentApi).toHaveBeenCalledTimes(1);
  });

  it('marks agent creation failed when POST rejects', async () => {
    (createAIAgentApi as jest.Mock).mockRejectedValue(new Error('Invalid agent'));
    const request = createAIAgent(agentData);
    await run(createAIAgentSaga, request);

    expect(actions).toContainEqual(createAIAgentFailed());
    expect(actions).not.toContainEqual(createAIAgentSuccess());
    expect(actions).not.toContainEqual(closeCreateUserModal());
  });

  it('marks vendor provider creation successful even when refreshing providers fails', async () => {
    (getAIProvidersApi as jest.Mock).mockRejectedValue(new Error('Refresh failed'));
    const request = createAIProviderByVendor({ vendor: 'openrouter', apiKey: 'secret' });
    await run(createAIProviderByVendorSaga, request);

    expect(actions).toContainEqual(createAIProviderSuccess());
    expect(actions).not.toContainEqual(createAIProviderFailed());
    expect(createAIProviderByVendorApi).toHaveBeenCalledTimes(1);
  });

  it('marks custom provider creation failed when POST rejects', async () => {
    (createAIProviderApi as jest.Mock).mockRejectedValue(new Error('Invalid provider'));
    const request = createAIProvider({ name: 'Custom', baseUrl: 'https://example.com', apiKey: 'secret' });
    await run(createAIProviderSaga, request);

    expect(actions).toContainEqual(createAIProviderFailed());
    expect(actions).not.toContainEqual(createAIProviderSuccess());
  });
});
