import { createSelector } from 'reselect';

import type { IApplicationState } from '../../types/redux';
import { aiAgentsComparators } from '../ai/utils/aiAgentsComparators';

export const getAIProvidersList = (state: IApplicationState) => state.ai.providers.list;

export const getAIProvidersIsLoading = (state: IApplicationState) => state.ai.providers.isLoading;

export const getAICreateProviderModalIsOpen = (state: IApplicationState) => state.ai.createProviderModal.isOpen;

export const getAICreateProviderModalIsLoading = (state: IApplicationState) => state.ai.createProviderModal.isLoading;

const getAIAgentsList = (state: IApplicationState) => state.ai.agents.list;

export const getAIAgentsIsLoading = (state: IApplicationState) => state.ai.agents.isLoading;

export const getAIAgentsSorting = (state: IApplicationState) => state.ai.agentsSorting;

export const getAIAgentsSorted = createSelector(getAIAgentsList, getAIAgentsSorting, (list, sorting) =>
  list.slice().sort(aiAgentsComparators[sorting]),
);

export const getAIVendorsList = (state: IApplicationState) => state.ai.vendors.list;

export const getAIProviderModelsList = (state: IApplicationState) => state.ai.models.list;

export const getAIProviderModelsIsLoading = (state: IApplicationState) => state.ai.models.isLoading;

export const getAIProviderModelsProviderId = (state: IApplicationState) => state.ai.models.providerId;
