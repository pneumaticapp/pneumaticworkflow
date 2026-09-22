import { IApplicationState } from '../../types/redux';

export const getAIStore = (state: IApplicationState) => state.ai;

export const getAIProviders = (state: IApplicationState) => state.ai.providers.list;

export const getAIProvidersState = (state: IApplicationState) => state.ai.providers;

export const getAIAgents = (state: IApplicationState) => state.ai.agents.list;

export const getAIAgentsState = (state: IApplicationState) => state.ai.agents;

export const getAIProviderModelsState = (state: IApplicationState) => state.ai.models;

export const getIsAISaving = (state: IApplicationState) => state.ai.isSaving;

/**
 * Agents can only be created once a provider exists, and the answer must not be "no" merely because
 * the list has not been fetched yet.
 */
export const getCanCreateAIAgent = (state: IApplicationState) =>
  state.ai.providers.isLoaded && state.ai.providers.list.length > 0;
