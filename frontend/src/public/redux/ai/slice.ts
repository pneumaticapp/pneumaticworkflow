import { createAction, createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

import type { IAIStore } from '../../types/redux';
import type {
  IAIAgent,
  IAIModel,
  IAIProvider,
  ICreateAIAgentRequest,
  ICreateAIProviderByVendorRequest,
  ICreateAIProviderRequest,
  IAIVendor,
} from '../../types/ai';

const initialState: IAIStore = {
  providers: {
    isLoading: true,
    list: [],
  },
  agents: {
    isLoading: true,
    list: [],
  },
  vendors: {
    isLoading: false,
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
export const createAIProviderByVendor = createAction<ICreateAIProviderByVendorRequest>('ai/createAIProviderByVendor');
export const deleteAIProvider = createAction<number>('ai/deleteAIProvider');
export const loadAIProviderModels = createAction<number>('ai/loadAIProviderModels');
export const loadAIVendors = createAction<void>('ai/loadAIVendors');

export const loadAIAgents = createAction<void>('ai/loadAIAgents');
export const createAIAgent = createAction<ICreateAIAgentRequest>('ai/createAIAgent');
export const updateAIAgent = createAction<{ id: number } & Partial<ICreateAIAgentRequest>>('ai/updateAIAgent');
export const deleteAIAgent = createAction<number>('ai/deleteAIAgent');

const aiSlice = createSlice({
  name: 'ai',
  initialState,
  reducers: {
    loadAIProvidersStarted: (state) => {
      state.providers.isLoading = state.providers.list.length === 0;
    },
    loadAIProvidersSuccess: (state, action: PayloadAction<IAIProvider[]>) => {
      state.providers = { isLoading: false, list: action.payload };
    },
    loadAIProvidersFailed: (state) => {
      state.providers.isLoading = false;
    },

    loadAIAgentsStarted: (state) => {
      state.agents.isLoading = state.agents.list.length === 0;
    },
    loadAIAgentsSuccess: (state, action: PayloadAction<IAIAgent[]>) => {
      state.agents = { isLoading: false, list: action.payload };
    },
    loadAIAgentsFailed: (state) => {
      state.agents.isLoading = false;
    },

    loadAIVendorsStarted: (state) => {
      state.vendors.isLoading = true;
    },
    loadAIVendorsSuccess: (state, action: PayloadAction<IAIVendor[]>) => {
      state.vendors = { isLoading: false, list: action.payload };
    },
    loadAIVendorsFailed: (state) => {
      state.vendors.isLoading = false;
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
      state.models.providerId = null;
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
  loadAIVendorsStarted,
  loadAIVendorsSuccess,
  loadAIVendorsFailed,
  loadAIProviderModelsStarted,
  loadAIProviderModelsSuccess,
  loadAIProviderModelsFailed,
  resetAIProviderModels,
  savingStarted,
  savingFinished,
} = aiSlice.actions;

export default aiSlice.reducer;
