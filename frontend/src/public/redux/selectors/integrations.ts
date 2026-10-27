import type { IApplicationState } from '../../types/redux';

export const getApiKeys = (state: IApplicationState) => state.integrations.apiKeys.data;

export const getApiKeysIsLoading = (state: IApplicationState) => state.integrations.apiKeys.isLoading;

export const getApiKeysNewlyCreatedKey = (state: IApplicationState) => state.integrations.apiKeys.newlyCreatedKey;
