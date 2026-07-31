import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IAiAgentsStore } from '../../types/redux';
import { IAiAgent, IAiConnection, IAiModel, TAiAgentDraft, TAiConnectionDraft } from './types';

const initialState: IAiAgentsStore = {
  isLoading: false,
  isEnabled: false,
  list: [],
  editModal: {
    isOpen: false,
    editAgent: null,
  },
  connection: {
    isAvailable: false,
    isSaving: false,
    value: null,
  },
  models: {
    isLoading: false,
    list: [],
  },
};

export const loadAiAgents = createAction<void>('aiAgents/loadAiAgents');
export const createAiAgent = createAction<TAiAgentDraft>('aiAgents/createAiAgent');
export const updateAiAgent = createAction<IAiAgent>('aiAgents/updateAiAgent');
export const deleteAiAgent = createAction<Pick<IAiAgent, 'id'>>('aiAgents/deleteAiAgent');
export const loadAiConnection = createAction<void>('aiAgents/loadAiConnection');
export const saveAiConnection = createAction<TAiConnectionDraft>('aiAgents/saveAiConnection');
export const removeAiConnection = createAction<void>('aiAgents/removeAiConnection');
export const loadAiModels = createAction<void>('aiAgents/loadAiModels');

const aiAgentsSlice = createSlice({
  name: 'aiAgents',
  initialState,
  reducers: {
    loadAiAgentsSuccess: (state, action: PayloadAction<IAiAgent[]>) => {
      state.list = action.payload;
      state.isEnabled = true;
      state.isLoading = false;
    },

    loadAiAgentsFailed: (state) => {
      state.list = [];
      state.isEnabled = false;
      state.isLoading = false;
    },

    createAiAgentSuccess: (state, action: PayloadAction<IAiAgent>) => {
      state.list = [...state.list, action.payload];
      state.isLoading = false;
      state.editModal = { isOpen: false, editAgent: null };
    },

    updateAiAgentSuccess: (state, action: PayloadAction<IAiAgent>) => {
      const { id } = action.payload;
      state.list = state.list.map((agent) => (agent.id === id ? action.payload : agent));
      state.isLoading = false;
      state.editModal = { isOpen: false, editAgent: null };
    },

    deleteAiAgentSuccess: (state, action: PayloadAction<Pick<IAiAgent, 'id'>>) => {
      state.list = state.list.filter((agent) => agent.id !== action.payload.id);
      state.isLoading = false;
    },

    aiAgentRequestFailed: (state) => {
      state.isLoading = false;
    },

    openAiAgentModal: (state, action: PayloadAction<IAiAgent | null>) => {
      state.editModal = { isOpen: true, editAgent: action.payload };
    },

    closeAiAgentModal: (state) => {
      state.editModal = { isOpen: false, editAgent: null };
    },

    loadAiConnectionSuccess: (state, action: PayloadAction<IAiConnection | null>) => {
      state.connection.isAvailable = true;
      state.connection.value = action.payload;
    },

    loadAiConnectionFailed: (state) => {
      state.connection.isAvailable = false;
      state.connection.value = null;
    },

    saveAiConnectionSuccess: (state, action: PayloadAction<IAiConnection>) => {
      state.connection.isSaving = false;
      state.connection.value = action.payload;
    },

    removeAiConnectionSuccess: (state) => {
      state.connection.isSaving = false;
      state.connection.value = null;
    },

    aiConnectionRequestFailed: (state) => {
      state.connection.isSaving = false;
    },

    loadAiModelsSuccess: (state, action: PayloadAction<IAiModel[]>) => {
      state.models.isLoading = false;
      state.models.list = action.payload;
    },

    loadAiModelsFailed: (state) => {
      state.models.isLoading = false;
      state.models.list = [];
    },
  },
  extraReducers: (builder) => {
    builder.addCase(loadAiAgents, (state) => {
      state.isLoading = true;
    });
    builder.addCase(createAiAgent, (state) => {
      state.isLoading = true;
    });
    builder.addCase(updateAiAgent, (state) => {
      state.isLoading = true;
    });
    builder.addCase(deleteAiAgent, (state) => {
      state.isLoading = true;
    });
    builder.addCase(saveAiConnection, (state) => {
      state.connection.isSaving = true;
    });
    builder.addCase(removeAiConnection, (state) => {
      state.connection.isSaving = true;
    });
    builder.addCase(loadAiModels, (state) => {
      state.models.isLoading = true;
    });
  },
});

export const {
  loadAiAgentsSuccess,
  loadAiAgentsFailed,
  createAiAgentSuccess,
  updateAiAgentSuccess,
  deleteAiAgentSuccess,
  aiAgentRequestFailed,
  openAiAgentModal,
  closeAiAgentModal,
  loadAiConnectionSuccess,
  loadAiConnectionFailed,
  saveAiConnectionSuccess,
  removeAiConnectionSuccess,
  aiConnectionRequestFailed,
  loadAiModelsSuccess,
  loadAiModelsFailed,
} = aiAgentsSlice.actions;

export default aiAgentsSlice.reducer;
