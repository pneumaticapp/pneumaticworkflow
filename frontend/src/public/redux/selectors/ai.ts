import { createSelector } from 'reselect';

import type { IApplicationState } from '../../types/redux';

export const getAIProvidersList = (state: IApplicationState) => state.ai.providers.list;

export const getAIProvidersIsLoading = (state: IApplicationState) => state.ai.providers.isLoading;

export const getAICreateProviderModalIsOpen = (state: IApplicationState) => state.ai.createProviderModal.isOpen;

export const getAICreateProviderModalIsLoading = (state: IApplicationState) => state.ai.createProviderModal.isLoading;

export const getAICreateAgentIsLoading = (state: IApplicationState) => state.ai.createAgent.isLoading;

const getAIAgentsList = (state: IApplicationState) => state.ai.agents.list;

export const getAIAgentsIsLoading = (state: IApplicationState) => state.ai.agents.isLoading;

export const getAIAgentsSortedByName = createSelector(getAIAgentsList, (list) =>
  list.slice().sort((first, second) => first.name.localeCompare(second.name)),
);

export const getAIVendorsList = (state: IApplicationState) => state.ai.vendors.list;

export const getAIProviderModelsList = (state: IApplicationState) => state.ai.models.list;

export const getAIProviderModelsIsLoading = (state: IApplicationState) => state.ai.models.isLoading;

export const getAIProviderModelsProviderId = (state: IApplicationState) => state.ai.models.providerId;

export const getAIAgentAvatarUploadIsLoading = (state: IApplicationState) => state.ai.agentAvatarUpload.isLoading;
