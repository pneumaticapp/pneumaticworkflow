import { createSelector } from 'reselect';

import type { IApplicationState } from '../../types/redux';

export const getAIProviders = (state: IApplicationState) => state.ai.providers.list;

export const getAIProvidersState = (state: IApplicationState) => state.ai.providers;

export const getAICreateProviderModalState = (state: IApplicationState) => state.ai.createProviderModal;

export const getAICreateAgentState = (state: IApplicationState) => state.ai.createAgent;

export const getAIAgentsState = (state: IApplicationState) => state.ai.agents;

export const getAIAgentsSortedByName = createSelector(getAIAgentsState, ({ list }) =>
  list.slice().sort((first, second) => first.name.localeCompare(second.name)),
);

export const getAIVendorsState = (state: IApplicationState) => state.ai.vendors;

export const getAIProviderModelsState = (state: IApplicationState) => state.ai.models;

export const getAIAgentAvatarUploadState = (state: IApplicationState) => state.ai.agentAvatarUpload;
