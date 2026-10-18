import { IApplicationState } from '../../types/redux';

export const getAIProviders = (state: IApplicationState) => state.ai.providers.list;

export const getAIProvidersState = (state: IApplicationState) => state.ai.providers;

export const getAICreateProviderModalState = (state: IApplicationState) => state.ai.createProviderModal;

export const getAICreateAgentState = (state: IApplicationState) => state.ai.createAgent;

export const getAIAgentsState = (state: IApplicationState) => state.ai.agents;

export const getAIVendorsState = (state: IApplicationState) => state.ai.vendors;

export const getAIProviderModelsState = (state: IApplicationState) => state.ai.models;
