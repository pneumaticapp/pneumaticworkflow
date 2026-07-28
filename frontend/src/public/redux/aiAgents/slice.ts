import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IAiAgentsStore } from '../../types/redux';
import { IAiAgent } from './types';

const initialState: IAiAgentsStore = {
  isLoading: false,
  list: [],
};

export const loadAiAgents = createAction<void>('aiAgents/loadAiAgents');

const aiAgentsSlice = createSlice({
  name: 'aiAgents',
  initialState,
  reducers: {
    loadAiAgentsSuccess: (state, action: PayloadAction<IAiAgent[]>) => {
      state.list = action.payload;
      state.isLoading = false;
    },

    loadAiAgentsFailed: (state) => {
      state.list = [];
      state.isLoading = false;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(loadAiAgents, (state) => {
      state.isLoading = true;
    });
  },
});

export const { loadAiAgentsSuccess, loadAiAgentsFailed } = aiAgentsSlice.actions;

export default aiAgentsSlice.reducer;
