import type { IApplicationState } from '../../types/redux';

export const getApiKeys = (state: IApplicationState) => state.integrations.apiKeys.data;

export const getAreApiKeysLoading = (state: IApplicationState) => state.integrations.apiKeys.isLoading;

export const getNewlyCreatedApiKey = (state: IApplicationState) => state.integrations.apiKeys.newlyCreatedKey;
