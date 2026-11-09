import type { RootState } from '../store';

export const getApiKeys = (state: RootState) => state.integrations.apiKeys.data;

export const getApiKeysIsLoading = (state: RootState) => state.integrations.apiKeys.isLoading;

export const getApiKeysNewlyCreatedKey = (state: RootState) => state.integrations.apiKeys.newlyCreatedKey;
