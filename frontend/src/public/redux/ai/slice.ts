import { createAction, createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

import type { IAIStore } from './types';
import type {
  IAIAgent,
  IAIModel,
  IAIProvider,
  ICreateAIAgentRequest,
  ICreateAIProviderByVendorRequest,
  ICreateAIProviderRequest,
  IAIVendor,
} from '../../api/ai/types';

const initialState: IAIStore = {
  providers: {
    isLoading: true,
    list: [],
  },
  createProvider: { status: 'idle', requestId: null },
  createAgent: { status: 'idle', requestId: null },
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
let lastCreateRequestId = 0;
export const createAIProvider = createAction('ai/createAIProvider', (payload: ICreateAIProviderRequest) => ({
  payload,
  meta: { requestId: ++lastCreateRequestId },
}));
export const createAIProviderByVendor = createAction(
  'ai/createAIProviderByVendor',
  (payload: ICreateAIProviderByVendorRequest) => ({ payload, meta: { requestId: ++lastCreateRequestId } }),
);
export const deleteAIProvider = createAction<number>('ai/deleteAIProvider');
export const loadAIProviderModels = createAction<number>('ai/loadAIProviderModels');
export const loadAIVendors = createAction<void>('ai/loadAIVendors');

export const loadAIAgents = createAction<void>('ai/loadAIAgents');
export const createAIAgent = createAction('ai/createAIAgent', (payload: ICreateAIAgentRequest) => ({
  payload,
  meta: { requestId: ++lastCreateRequestId },
}));
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

    createAIProviderStarted: (state, action: PayloadAction<number>) => {
      state.createProvider = { status: 'pending', requestId: action.payload };
    },
    createAIProviderSucceeded: (state, action: PayloadAction<number>) => {
      if (state.createProvider.requestId === action.payload) state.createProvider.status = 'succeeded';
    },
    createAIProviderFailed: (state, action: PayloadAction<number>) => {
      if (state.createProvider.requestId === action.payload) state.createProvider.status = 'failed';
    },
    createAIAgentStarted: (state, action: PayloadAction<number>) => {
      state.createAgent = { status: 'pending', requestId: action.payload };
    },
    createAIAgentSucceeded: (state, action: PayloadAction<number>) => {
      if (state.createAgent.requestId === action.payload) state.createAgent.status = 'succeeded';
    },
    createAIAgentFailed: (state, action: PayloadAction<number>) => {
      if (state.createAgent.requestId === action.payload) state.createAgent.status = 'failed';
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
  createAIProviderStarted,
  createAIProviderSucceeded,
  createAIProviderFailed,
  createAIAgentStarted,
  createAIAgentSucceeded,
  createAIAgentFailed,
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
