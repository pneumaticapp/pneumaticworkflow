import { createSelector } from 'reselect';

import type { RootState } from '../store';
import { aiAgentsComparators } from '../ai/utils/aiAgentsComparators';

export const getAIProvidersList = (state: RootState) => state.ai.providers.list;

export const getAIProvidersIsLoading = (state: RootState) => state.ai.providers.isLoading;

export const getAICreateProviderModalIsOpen = (state: RootState) => state.ai.createProviderModal.isOpen;

export const getAICreateProviderModalIsLoading = (state: RootState) => state.ai.createProviderModal.isLoading;

const getAIAgentsList = (state: RootState) => state.ai.agents.list;

export const getAIAgentsIsLoading = (state: RootState) => state.ai.agents.isLoading;

export const getAIAgentsSorting = (state: RootState) => state.ai.agentsSorting;

export const getAIAgentsSorted = createSelector(getAIAgentsList, getAIAgentsSorting, (list, sorting) =>
  list.slice().sort(aiAgentsComparators[sorting]),
);

export const getAIVendorsList = (state: RootState) => state.ai.vendors.list;

export const getAIProviderModelsList = (state: RootState) => state.ai.models.list;

export const getAIProviderModelsIsLoading = (state: RootState) => state.ai.models.isLoading;

export const getAIProviderModelsProviderId = (state: RootState) => state.ai.models.providerId;
