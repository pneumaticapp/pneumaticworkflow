import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IAiAgentsStore } from '../../types/redux';
import { IAiAgent, TAiAgentDraft } from './types';

const initialState: IAiAgentsStore = {
  isLoading: false,
  isEnabled: false,
  list: [],
  editModal: {
    isOpen: false,
    editAgent: null,
  },
};

export const loadAiAgents = createAction<void>('aiAgents/loadAiAgents');
export const createAiAgent = createAction<TAiAgentDraft>('aiAgents/createAiAgent');
export const updateAiAgent = createAction<IAiAgent>('aiAgents/updateAiAgent');
export const deleteAiAgent = createAction<Pick<IAiAgent, 'id'>>('aiAgents/deleteAiAgent');

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
} = aiAgentsSlice.actions;

export default aiAgentsSlice.reducer;
