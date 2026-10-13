import { reducer } from './reducer';
import { EIntegrationsActions } from './actions';
import { IIntegrationsStore } from '../../types/redux';
import { IApiKeyItem } from '../../types/integrations';

const mockApiKey: IApiKeyItem = {
  id: 1,
  name: 'Test Key',
  prefix: 'pn_live_',
  dateCreated: '2026-07-30T00:00:00Z',
  lastUsedAt: null,
  expiresAt: null,
  isActive: true,
};

describe('integrations reducer', () => {
  let initialState: IIntegrationsStore;

  beforeEach(() => {
    initialState = {
      apiKeys: { isLoading: false, data: [], newlyCreatedKey: null },
      list: { isLoading: false, data: [] },
      detailed: { isLoading: false, data: null },
    };
  });

  it('should handle LoadApiKeys', () => {
    const action = { type: EIntegrationsActions.LoadApiKeys } as any;
    const nextState = reducer(initialState, action);
    expect(nextState.apiKeys.isLoading).toBe(true);
  });

  it('should handle LoadApiKeysSuccess', () => {
    const action = {
      type: EIntegrationsActions.LoadApiKeysSuccess,
      payload: [mockApiKey],
    } as any;
    const nextState = reducer(initialState, action);
    expect(nextState.apiKeys.isLoading).toBe(false);
    expect(nextState.apiKeys.data).toEqual([mockApiKey]);
  });

  it('should handle LoadApiKeysFailed', () => {
    const action = { type: EIntegrationsActions.LoadApiKeysFailed } as any;
    const state = {
      ...initialState,
      apiKeys: { ...initialState.apiKeys, isLoading: true },
    };
    const nextState = reducer(state, action);
    expect(nextState.apiKeys.isLoading).toBe(false);
  });

  it('should handle CreateApiKeySuccess', () => {
    const action = {
      type: EIntegrationsActions.CreateApiKeySuccess,
      payload: { apiKey: mockApiKey, rawKey: 'pn_live_123' },
    } as any;
    const nextState = reducer(initialState, action);
    expect(nextState.apiKeys.data[0]).toEqual(mockApiKey);
    expect(nextState.apiKeys.newlyCreatedKey).toBe('pn_live_123');
  });

  it('should handle DeleteApiKeySuccess', () => {
    const state = {
      ...initialState,
      apiKeys: { ...initialState.apiKeys, data: [mockApiKey] },
    };
    const action = {
      type: EIntegrationsActions.DeleteApiKeySuccess,
      payload: { id: 1 },
    } as any;
    const nextState = reducer(state, action);
    expect(nextState.apiKeys.data).toHaveLength(0);
  });

  it('should handle ClearNewlyCreatedKey', () => {
    const state = {
      ...initialState,
      apiKeys: { ...initialState.apiKeys, newlyCreatedKey: 'pn_live_123' },
    };
    const action = { type: EIntegrationsActions.ClearNewlyCreatedKey } as any;
    const nextState = reducer(state, action);
    expect(nextState.apiKeys.newlyCreatedKey).toBeNull();
  });
});
