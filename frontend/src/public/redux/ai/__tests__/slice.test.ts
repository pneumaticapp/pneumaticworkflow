import reducer, {
  createAIAgentFailed,
  createAIAgentStarted,
  createAIAgentSucceeded,
  createAIProviderFailed,
  createAIProviderStarted,
  createAIProviderSucceeded,
  loadAIProvidersFailed,
  loadAIProvidersStarted,
  loadAIProvidersSuccess,
} from '../slice';
import { EAIVendor } from '../../../api/ai/types';

describe('AI request state', () => {
  it('uses isLoading until the provider request succeeds or fails', () => {
    const initial = reducer(undefined, { type: 'init' });
    expect(initial.providers).toEqual({ isLoading: true, list: [] });

    const loading = reducer(initial, loadAIProvidersStarted());
    expect(loading.providers.isLoading).toBe(true);
    expect(reducer(loading, loadAIProvidersSuccess([])).providers).toEqual({ isLoading: false, list: [] });
    const failed = reducer(loading, loadAIProvidersFailed());
    expect(failed.providers).toEqual({ isLoading: false, list: [] });
    expect(reducer(failed, loadAIProvidersStarted()).providers.isLoading).toBe(true);
  });

  it('preserves the last provider list when a refresh fails', () => {
    const initial = reducer(undefined, { type: 'init' });
    const provider = {
      id: 1,
      name: 'OpenRouter',
      baseUrl: '',
      apiKeyPrefix: '',
      vendor: EAIVendor.OpenRouter,
      isActive: true,
      usage: [],
    };
    const loaded = reducer(initial, loadAIProvidersSuccess([provider]));
    const refreshing = reducer(loaded, loadAIProvidersStarted());
    expect(refreshing.providers.isLoading).toBe(false);
    const failed = reducer(refreshing, loadAIProvidersFailed());

    expect(failed.providers).toEqual({ isLoading: false, list: [provider] });
  });

  it('ignores completion of an old agent request after a retry starts', () => {
    const initial = reducer(undefined, { type: 'init' });
    const pending = reducer(reducer(initial, createAIAgentStarted(1)), createAIAgentStarted(2));

    expect(reducer(pending, createAIAgentSucceeded(1)).createAgent).toEqual({ status: 'pending', requestId: 2 });
    expect(reducer(pending, createAIAgentFailed(1)).createAgent).toEqual({ status: 'pending', requestId: 2 });
    expect(reducer(pending, createAIAgentSucceeded(2)).createAgent.status).toBe('succeeded');
  });

  it('tracks both provider creation paths by the current request ID', () => {
    const initial = reducer(undefined, { type: 'init' });
    const pending = reducer(reducer(initial, createAIProviderStarted(3)), createAIProviderStarted(4));

    expect(reducer(pending, createAIProviderSucceeded(3)).createProvider.status).toBe('pending');
    expect(reducer(pending, createAIProviderFailed(4)).createProvider).toEqual({ status: 'failed', requestId: 4 });
  });
});
