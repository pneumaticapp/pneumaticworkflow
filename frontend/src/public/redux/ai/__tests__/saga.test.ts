import { runSaga, stdChannel } from 'redux-saga';
import { takeLatest } from 'redux-saga/effects';

import {
  createAIAgent as createAIAgentApi,
  createAIProvider as createAIProviderApi,
  createAIProviderByVendor as createAIProviderByVendorApi,
  getAIAgents as getAIAgentsApi,
  getAIProviders as getAIProvidersApi,
  updateAIAgent as updateAIAgentApi,
} from '../../../api/ai';
import {
  createAIAgentSaga,
  createAIProviderByVendorSaga,
  createAIProviderSaga,
  updateAIAgentSaga,
  uploadAIAgentAvatarSaga,
} from '../saga';
import {
  createAIAgent,
  createAIProvider,
  createAIProviderByVendor,
  createAIProviderFailed,
  createAIProviderSuccess,
  cancelAIAgentAvatarUpload,
  closeCreateAIProviderModal,
  updateAIAgent,
  uploadAIAgentAvatar,
} from '../slice';
import { uploadUserAvatar } from '../../../utils/uploadFiles';
import { NotificationManager } from '../../../components/UI/Notifications';
import { closeCreatePerformerModal, createPerformerFailed, createPerformerStarted } from '../../team/slice';

jest.mock('../../../api/ai', () => ({
  createAIAgent: jest.fn(),
  createAIProvider: jest.fn(),
  createAIProviderByVendor: jest.fn(),
  getAIAgents: jest.fn(),
  getAIProviders: jest.fn(),
  updateAIAgent: jest.fn(),
}));
jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { success: jest.fn(), warning: jest.fn() },
}));
jest.mock('../../../utils/logger', () => ({ logger: { error: jest.fn() } }));
jest.mock('../../../utils/uploadFiles', () => ({ uploadUserAvatar: jest.fn() }));

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

    expect(actions).toContainEqual(createPerformerStarted());
    expect(actions).toContainEqual(closeCreatePerformerModal());
    expect(actions).not.toContainEqual(createPerformerFailed());
    expect(createAIAgentApi).toHaveBeenCalledTimes(1);
  });

  it('marks agent creation failed when POST rejects', async () => {
    (createAIAgentApi as jest.Mock).mockRejectedValue(new Error('Invalid agent'));
    const request = createAIAgent(agentData);
    await run(createAIAgentSaga, request);

    expect(actions).toContainEqual(createPerformerFailed());
    expect(actions).not.toContainEqual(closeCreatePerformerModal());
  });

  it('reports a successful agent update without sending the callbacks to the API', async () => {
    (updateAIAgentApi as jest.Mock).mockResolvedValue({});
    const onSuccess = jest.fn();
    const onError = jest.fn();
    await run(updateAIAgentSaga, updateAIAgent({ id: 7, ...agentData, onSuccess, onError }));

    expect(updateAIAgentApi).toHaveBeenCalledWith(7, agentData);
    expect(onSuccess).toHaveBeenCalledTimes(1);
    expect(onError).not.toHaveBeenCalled();
  });

  it('reports a failed agent update', async () => {
    (updateAIAgentApi as jest.Mock).mockRejectedValue(new Error('Invalid model'));
    const onSuccess = jest.fn();
    const onError = jest.fn();
    await run(updateAIAgentSaga, updateAIAgent({ id: 7, ...agentData, onSuccess, onError }));

    expect(onError).toHaveBeenCalledTimes(1);
    expect(onSuccess).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalled();
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

describe('AI agent avatar upload saga', () => {
  const dispatched: unknown[] = [];
  const pendingUploads: ((value: unknown) => void)[] = [];
  const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

  const startWatcher = () => {
    const channel = stdChannel();
    runSaga(
      {
        channel,
        dispatch: (action) => {
          dispatched.push(action);
        },
        getState: () => ({}),
      },
      function* watcher() {
        yield takeLatest([uploadAIAgentAvatar, cancelAIAgentAvatarUpload], uploadAIAgentAvatarSaga);
      },
    );

    return channel;
  };

  const buildFile = (name: string) => new File([name], name, { type: 'image/png' });

  beforeEach(() => {
    dispatched.length = 0;
    pendingUploads.length = 0;
    jest.clearAllMocks();
    (uploadUserAvatar as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) => {
          pendingUploads.push(resolve);
        }),
    );
  });

  it('applies only the latest avatar upload', async () => {
    const channel = startWatcher();
    const onOld = jest.fn();
    const onNew = jest.fn();

    channel.put(uploadAIAgentAvatar({ file: buildFile('old.png'), onSuccess: onOld }));
    channel.put(uploadAIAgentAvatar({ file: buildFile('new.png'), onSuccess: onNew }));
    pendingUploads[0]([{ id: 'old', url: 'https://files.example.com/old.png', size: 1 }]);
    pendingUploads[1]([{ id: 'new', url: 'https://files.example.com/new.png', size: 1 }]);
    await flush();

    expect(onOld).not.toHaveBeenCalled();
    expect(onNew).toHaveBeenCalledWith('https://files.example.com/new.png');
  });

  it('drops a pending upload after cancellation', async () => {
    const channel = startWatcher();
    const onSuccess = jest.fn();

    channel.put(uploadAIAgentAvatar({ file: buildFile('old.png'), onSuccess }));
    channel.put(cancelAIAgentAvatarUpload());
    pendingUploads[0]([{ id: 'old', url: 'https://files.example.com/old.png', size: 1 }]);
    await flush();

    expect(onSuccess).not.toHaveBeenCalled();
  });

  it('warns and finishes when the upload fails', async () => {
    (uploadUserAvatar as jest.Mock).mockRejectedValue(new Error('Compression failed'));
    const channel = startWatcher();
    const onSuccess = jest.fn();

    channel.put(uploadAIAgentAvatar({ file: buildFile('avatar.png'), onSuccess }));
    await flush();

    expect(onSuccess).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledWith({ message: 'file-service.upload-failed' });
  });

  it('ignores an upload result marked with an error', async () => {
    const channel = startWatcher();
    const onSuccess = jest.fn();

    channel.put(uploadAIAgentAvatar({ file: buildFile('big.png'), onSuccess }));
    pendingUploads[0]([{ id: 'big', url: '', size: 1, error: 'Max file size exceeded' }]);
    await flush();

    expect(onSuccess).not.toHaveBeenCalled();
  });
});

describe('AI creation sagas when the modal closes mid-request', () => {
  const dispatched: unknown[] = [];
  const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

  const start = (saga: (...args: any[]) => Generator, action: object) => {
    const channel = stdChannel();
    const task = runSaga(
      {
        channel,
        dispatch: (dispatchedAction) => {
          dispatched.push(dispatchedAction);
        },
        getState: () => ({}),
      },
      saga,
      action,
    );

    return { channel, task };
  };

  const deferred = () => {
    let resolve!: (value: unknown) => void;
    let reject!: (error: Error) => void;
    const promise = new Promise((res, rej) => {
      resolve = res;
      reject = rej;
    });

    return { promise, resolve, reject };
  };

  beforeEach(() => {
    dispatched.length = 0;
    jest.clearAllMocks();
    (getAIAgentsApi as jest.Mock).mockResolvedValue([]);
    (getAIProvidersApi as jest.Mock).mockResolvedValue([]);
  });

  it('does not close a reopened performer modal when an earlier agent create succeeds', async () => {
    const request = deferred();
    (createAIAgentApi as jest.Mock).mockReturnValue(request.promise);
    const { channel, task } = start(
      createAIAgentSaga,
      createAIAgent({ name: 'Agent', providerId: 1, model: 'm', systemPrompt: 'p', photo: null, isActive: true }),
    );

    channel.put(closeCreatePerformerModal());
    request.resolve({});
    await task.toPromise();

    expect(dispatched).not.toContainEqual(closeCreatePerformerModal());
    expect(NotificationManager.success).toHaveBeenCalledWith({ message: 'team.ai-agents.created' });
  });

  it('leaves the reopened performer modal state alone when an earlier agent create fails', async () => {
    const request = deferred();
    (createAIAgentApi as jest.Mock).mockReturnValue(request.promise);
    const { channel, task } = start(
      createAIAgentSaga,
      createAIAgent({ name: 'Agent', providerId: 1, model: 'm', systemPrompt: 'p', photo: null, isActive: true }),
    );

    channel.put(closeCreatePerformerModal());
    request.reject(new Error('Invalid agent'));
    await task.toPromise();
    await flush();

    expect(dispatched).not.toContainEqual(createPerformerFailed());
    expect(NotificationManager.warning).toHaveBeenCalledWith({ message: 'Invalid agent' });
  });

  it('does not close a reopened provider modal when an earlier provider create succeeds', async () => {
    const request = deferred();
    (createAIProviderApi as jest.Mock).mockReturnValue(request.promise);
    const { channel, task } = start(
      createAIProviderSaga,
      createAIProvider({ name: 'Custom', baseUrl: 'https://example.com', apiKey: 'secret' }),
    );

    channel.put(closeCreateAIProviderModal());
    request.resolve({});
    await task.toPromise();

    expect(dispatched).not.toContainEqual(createAIProviderSuccess());
    expect(NotificationManager.success).toHaveBeenCalledWith({ message: 'ai-providers.created' });
  });
});
