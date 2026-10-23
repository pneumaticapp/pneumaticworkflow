import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

import { ETemplateActions } from '../template/actions';
import type { ITemplateValidationError, ITemplateValidationStore } from './types';

export const initialState: ITemplateValidationStore = {
  errors: [],
  batchId: 0,
  focusElementApiName: null,
};

const templateValidationSlice = createSlice({
  name: 'templateValidation',
  initialState,
  reducers: {
    setTemplateValidationErrors: (state, action: PayloadAction<ITemplateValidationError[]>) => {
      state.errors = action.payload;
      state.batchId += 1;
      state.focusElementApiName = action.payload[0]?.target.elementApiName ?? null;
    },
    removeTemplateValidationErrors: (state, action: PayloadAction<string[]>) => {
      state.errors = state.errors.filter(({ apiName }) => !action.payload.includes(apiName));
    },
    clearTemplateValidationErrors: (state) => {
      state.errors = [];
    },
    clearTemplateValidationFocus: (state) => {
      state.focusElementApiName = null;
    },
  },
  extraReducers: (builder) => {
    builder.addMatcher(
      (action) => action.type === ETemplateActions.ResetTemplateStore,
      (state) => {
        state.errors = [];
      },
    );
  },
});

export const {
  setTemplateValidationErrors,
  removeTemplateValidationErrors,
  clearTemplateValidationErrors,
  clearTemplateValidationFocus,
} = templateValidationSlice.actions;

export default templateValidationSlice.reducer;
