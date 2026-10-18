import { IApplicationState } from '../../types/redux';

export const getAIProviders = (state: IApplicationState) => state.ai.providers.list;

export const getAIProvidersState = (state: IApplicationState) => state.ai.providers;

export const getAICreateProviderState = (state: IApplicationState) => state.ai.createProvider;

export const getAICreateAgentState = (state: IApplicationState) => state.ai.createAgent;

export const getAIAgentsState = (state: IApplicationState) => state.ai.agents;

export const getAIVendorsState = (state: IApplicationState) => state.ai.vendors;

export const getAIProviderModelsState = (state: IApplicationState) => state.ai.models;

export const getIsAISaving = (state: IApplicationState) => state.ai.isSaving;
