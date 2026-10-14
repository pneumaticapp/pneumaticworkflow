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
import { EAIVendor } from '../../../types/ai';

describe('AI request state', () => {
  it('distinguishes a successfully loaded empty list from a failed load', () => {
    const initial = reducer(undefined, { type: 'init' });
    expect(initial.providers.status).toBe('idle');

    const loading = reducer(initial, loadAIProvidersStarted());
    expect(loading.providers.status).toBe('loading');
    expect(reducer(loading, loadAIProvidersSuccess([])).providers.status).toBe('succeeded');
    expect(reducer(loading, loadAIProvidersFailed()).providers.status).toBe('failed');
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
    const failed = reducer(reducer(loaded, loadAIProvidersStarted()), loadAIProvidersFailed());

    expect(failed.providers).toEqual({ status: 'failed', list: [provider] });
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
