import reducer, {
  closeCreateAIProviderModal,
  createAIProviderFailed,
  createAIProviderStarted,
  createAIProviderSuccess,
  loadAIProvidersFailed,
  loadAIProvidersStarted,
  loadAIProvidersSuccess,
  openCreateAIProviderModal,
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
      usage: [],
    };
    const loaded = reducer(initial, loadAIProvidersSuccess([provider]));
    const refreshing = reducer(loaded, loadAIProvidersStarted());
    expect(refreshing.providers.isLoading).toBe(false);
    const failed = reducer(refreshing, loadAIProvidersFailed());

    expect(failed.providers).toEqual({ isLoading: false, list: [provider] });
  });

  it('closes the provider modal only when creation succeeds', () => {
    const initial = reducer(undefined, { type: 'init' });
    const pending = reducer(reducer(initial, openCreateAIProviderModal()), createAIProviderStarted());

    expect(pending.createProviderModal).toEqual({ isOpen: true, isLoading: true });
    expect(reducer(pending, createAIProviderFailed()).createProviderModal).toEqual({ isOpen: true, isLoading: false });
    expect(reducer(pending, createAIProviderSuccess()).createProviderModal).toEqual({
      isOpen: false,
      isLoading: false,
    });
    expect(reducer(pending, closeCreateAIProviderModal()).createProviderModal.isOpen).toBe(false);
  });

  it('releases create loading when its modal closes', () => {
    const initial = reducer(undefined, { type: 'init' });
    const pendingProvider = reducer(reducer(initial, openCreateAIProviderModal()), createAIProviderStarted());

    expect(reducer(pendingProvider, closeCreateAIProviderModal()).createProviderModal).toEqual({
      isOpen: false,
      isLoading: false,
    });
  });
});
