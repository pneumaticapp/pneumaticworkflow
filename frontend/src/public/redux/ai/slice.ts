import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IAIStore } from '../../types/redux';
import { IAIAgent, IAIModel, IAIProvider, ICreateAIAgentRequest, ICreateAIProviderRequest } from '../../types/ai';

const initialState: IAIStore = {
  providers: {
    isLoading: false,
    isLoaded: false,
    list: [],
  },
  agents: {
    isLoading: false,
    isLoaded: false,
    list: [],
  },
  models: {
    isLoading: false,
    providerId: null,
    list: [],
  },
  isSaving: false,
};

export const loadAIProviders = createAction<void>('ai/loadAIProviders');
export const createAIProvider = createAction<ICreateAIProviderRequest>('ai/createAIProvider');
export const deleteAIProvider = createAction<number>('ai/deleteAIProvider');
export const loadAIProviderModels = createAction<number>('ai/loadAIProviderModels');

export const loadAIAgents = createAction<void>('ai/loadAIAgents');
export const createAIAgent = createAction<ICreateAIAgentRequest>('ai/createAIAgent');
export const updateAIAgent = createAction<{ id: number } & Partial<ICreateAIAgentRequest>>('ai/updateAIAgent');
export const deleteAIAgent = createAction<number>('ai/deleteAIAgent');

const aiSlice = createSlice({
  name: 'ai',
  initialState,
  reducers: {
    loadAIProvidersStarted: (state) => {
      state.providers.isLoading = true;
    },
    loadAIProvidersSuccess: (state, action: PayloadAction<IAIProvider[]>) => {
      state.providers = { isLoading: false, isLoaded: true, list: action.payload };
    },
    loadAIProvidersFailed: (state) => {
      state.providers.isLoading = false;
    },

    loadAIAgentsStarted: (state) => {
      state.agents.isLoading = true;
    },
    loadAIAgentsSuccess: (state, action: PayloadAction<IAIAgent[]>) => {
      state.agents = { isLoading: false, isLoaded: true, list: action.payload };
    },
    loadAIAgentsFailed: (state) => {
      state.agents.isLoading = false;
    },

    loadAIProviderModelsStarted: (state, action: PayloadAction<number>) => {
      state.models = { isLoading: true, providerId: action.payload, list: [] };
    },
    loadAIProviderModelsSuccess: (state, action: PayloadAction<{ providerId: number; models: IAIModel[] }>) => {
      // A slower response for a provider the user already switched away from must not land.
      if (state.models.providerId !== action.payload.providerId) {
        return;
      }
      state.models = { isLoading: false, providerId: action.payload.providerId, list: action.payload.models };
    },
    loadAIProviderModelsFailed: (state, action: PayloadAction<number>) => {
      if (state.models.providerId !== action.payload) {
        return;
      }
      state.models.isLoading = false;
    },
    resetAIProviderModels: (state) => {
      state.models = { isLoading: false, providerId: null, list: [] };
    },

    savingStarted: (state) => {
      state.isSaving = true;
    },
    savingFinished: (state) => {
      state.isSaving = false;
    },
  },
});

export const {
  loadAIProvidersStarted,
  loadAIProvidersSuccess,
  loadAIProvidersFailed,
  loadAIAgentsStarted,
  loadAIAgentsSuccess,
  loadAIAgentsFailed,
  loadAIProviderModelsStarted,
  loadAIProviderModelsSuccess,
  loadAIProviderModelsFailed,
  resetAIProviderModels,
  savingStarted,
  savingFinished,
} = aiSlice.actions;

export default aiSlice.reducer;
