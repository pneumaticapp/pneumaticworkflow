import { createAction, createSlice } from "@reduxjs/toolkit";

import { getBrowserConfig } from '../../utils/getConfig';
import { IPagesStore } from './types';

const { pages } = getBrowserConfig();

const initialState: IPagesStore = {
  list: pages ? JSON.parse(String(pages)) : [],
};

const pagesSlice = createSlice({
  name: "pages",
  initialState,
  reducers: {
    loadPagesSuccess: (state, action) => {
      state.list = action.payload;
    },
  },
});

export const loadPages = createAction('pages/loadPages');
export const loadPagesFailed = createAction('pages/loadPagesFailed');

export const {
  loadPagesSuccess,
} = pagesSlice.actions;

export default pagesSlice.reducer;
