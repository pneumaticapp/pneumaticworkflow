
import { createAction, createSlice, PayloadAction } from "@reduxjs/toolkit";

import { getBrowserConfig } from '../../utils/getConfig';
import { IPages, IPagesStore } from './types';

const { pages } = getBrowserConfig();

const initialState: IPagesStore = {
  list: pages ? JSON.parse(String(pages)) : [],
};

const pagesSlice = createSlice({
  name: "pages",
  initialState,
  reducers: {
    loadPagesSuccess: (state, action: PayloadAction<IPages>) => {
      state.list = action.payload;
    },
  },
});

export const loadPages = createAction<void>('pages/loadPages');
export const loadPagesFailed = createAction<void>('pages/loadPagesFailed');

export const {
  loadPagesSuccess,
} = pagesSlice.actions;

export default pagesSlice.reducer;
