import { createAction, createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

import type { IAIStore, IUploadAIAgentAvatarPayload, TUpdateAIAgentPayload } from './types';
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
  createProviderModal: { isOpen: false, isLoading: false },
  createAgent: { isLoading: false },
  agentAvatarUpload: { isLoading: false },
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
};

export const loadAIProviders = createAction<void>('ai/loadAIProviders');
export const createAIProvider = createAction<ICreateAIProviderRequest>('ai/createAIProvider');
export const createAIProviderByVendor = createAction<ICreateAIProviderByVendorRequest>('ai/createAIProviderByVendor');
export const deleteAIProvider = createAction<number>('ai/deleteAIProvider');
export const loadAIProviderModels = createAction<number>('ai/loadAIProviderModels');
export const loadAIVendors = createAction<void>('ai/loadAIVendors');

export const loadAIAgents = createAction<void>('ai/loadAIAgents');
export const createAIAgent = createAction<ICreateAIAgentRequest>('ai/createAIAgent');
export const updateAIAgent = createAction<TUpdateAIAgentPayload>('ai/updateAIAgent');
export const deleteAIAgent = createAction<number>('ai/deleteAIAgent');
export const uploadAIAgentAvatar = createAction<IUploadAIAgentAvatarPayload>('ai/uploadAIAgentAvatar');
export const cancelAIAgentAvatarUpload = createAction<void>('ai/cancelAIAgentAvatarUpload');

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

    openCreateAIProviderModal: (state) => {
      state.createProviderModal.isOpen = true;
    },
    closeCreateAIProviderModal: (state) => {
      state.createProviderModal.isOpen = false;
    },
    createAIProviderStarted: (state) => {
      state.createProviderModal.isLoading = true;
    },
    createAIProviderSuccess: (state) => {
      state.createProviderModal = { isOpen: false, isLoading: false };
    },
    createAIProviderFailed: (state) => {
      state.createProviderModal.isLoading = false;
    },

    createAIAgentStarted: (state) => {
      state.createAgent.isLoading = true;
    },
    createAIAgentSuccess: (state) => {
      state.createAgent.isLoading = false;
    },
    createAIAgentFailed: (state) => {
      state.createAgent.isLoading = false;
    },

    uploadAIAgentAvatarStarted: (state) => {
      state.agentAvatarUpload.isLoading = true;
    },
    uploadAIAgentAvatarFinished: (state) => {
      state.agentAvatarUpload.isLoading = false;
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
  },
});

export const {
  loadAIProvidersStarted,
  loadAIProvidersSuccess,
  loadAIProvidersFailed,
  openCreateAIProviderModal,
  closeCreateAIProviderModal,
  createAIProviderStarted,
  createAIProviderSuccess,
  createAIProviderFailed,
  createAIAgentStarted,
  createAIAgentSuccess,
  createAIAgentFailed,
  uploadAIAgentAvatarStarted,
  uploadAIAgentAvatarFinished,
  loadAIAgentsStarted,
  loadAIAgentsSuccess,
  loadAIAgentsFailed,
  loadAIVendorsStarted,
  loadAIVendorsSuccess,
  loadAIVendorsFailed,
  loadAIProviderModelsStarted,
  loadAIProviderModelsSuccess,
  loadAIProviderModelsFailed,
} = aiSlice.actions;

export default aiSlice.reducer;
