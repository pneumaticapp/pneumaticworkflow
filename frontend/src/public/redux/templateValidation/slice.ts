import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

import { ETemplateActions } from '../template/actions';
import type { ITemplateValidationError, ITemplateValidationStore } from './types';

const clearErrors = (state: ITemplateValidationStore) => {
  state.errors = [];
  state.focusApiName = null;
};

export const initialState: ITemplateValidationStore = {
  errors: [],
  batchId: 0,
  focusApiName: null,
};

const templateValidationSlice = createSlice({
  name: 'templateValidation',
  initialState,
  reducers: {
    setTemplateValidationErrors: (state, action: PayloadAction<ITemplateValidationError[]>) => {
      state.errors = action.payload;
      state.batchId += 1;
      state.focusApiName = action.payload[0]?.target.elementApiName ?? null;
    },
    removeTemplateValidationErrors: (state, action: PayloadAction<string[]>) => {
      state.errors = state.errors.filter(({ apiName }) => !action.payload.includes(apiName));
    },
    clearTemplateValidationErrors: clearErrors,
    clearTemplateValidationFocus: (state) => {
      state.focusApiName = null;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(ETemplateActions.ResetTemplateStore, clearErrors);
  },
});

export const {
  setTemplateValidationErrors,
  removeTemplateValidationErrors,
  clearTemplateValidationErrors,
  clearTemplateValidationFocus,
} = templateValidationSlice.actions;

export default templateValidationSlice.reducer;
