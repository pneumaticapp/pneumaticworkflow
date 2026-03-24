/* eslint-disable @typescript-eslint/no-unused-vars */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IDatasetsStore } from '../../types/redux';
import { IDataset, IDatasetListItem, ICreateDatasetParams, IUpdateDatasetParams } from '../../types/dataset';
import { TDeleteDatasetPayload } from './types';

export const initialState: IDatasetsStore = {
  items: [],
  isLoading: false,
  searchQuery: '',
  sortOrder: 'asc',

  currentDataset: null,
  isCurrentDatasetLoading: false,
  currentSearchQuery: '',
  currentSortOrder: 'asc',
};

const datasetsSlice = createSlice({
  name: 'datasets',
  initialState,
  reducers: {
    loadDatasets: (state) => {
      state.isLoading = true;
    },

    loadDatasetsSuccess: (state, action: PayloadAction<IDatasetListItem[]>) => {
      state.items = action.payload;
      state.isLoading = false;
    },

    loadDatasetsFailed: (state) => {
      state.isLoading = false;
    },

    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },

    setSortOrder: (state, action: PayloadAction<'asc' | 'desc'>) => {
      state.sortOrder = action.payload;
    },

    loadDataset: (state, _action: PayloadAction<{ id: number }>) => {
      state.currentDataset = null;
      state.isCurrentDatasetLoading = true;
      state.currentSearchQuery = '';
      state.currentSortOrder = 'asc';
    },

    loadDatasetSuccess: (state, action: PayloadAction<IDataset>) => {
      state.currentDataset = action.payload;
      state.isCurrentDatasetLoading = false;
    },

    loadDatasetFailed: (state) => {
      state.isCurrentDatasetLoading = false;
    },

    setCurrentDataset: (state, action: PayloadAction<IDataset>) => {
      state.currentDataset = action.payload;
    },

    setCurrentSearchQuery: (state, action: PayloadAction<string>) => {
      state.currentSearchQuery = action.payload;
    },

    setCurrentSortOrder: (state, action: PayloadAction<'asc' | 'desc'>) => {
      state.currentSortOrder = action.payload;
    },

    createDatasetAction: (state, _action: PayloadAction<ICreateDatasetParams>) => {
      state.isLoading = true;
    },

    cloneDatasetAction: (state, _action: PayloadAction<{ id: number }>) => {
      state.isLoading = true;
    },
    
    updateDatasetAction: (state, _action: PayloadAction<IUpdateDatasetParams>) => {
      state.isCurrentDatasetLoading = true;
    },

    deleteDatasetAction: (state, _action: PayloadAction<TDeleteDatasetPayload>) => {
      state.isLoading = true;
    },
  },
});

export const {
  loadDatasets,
  loadDatasetsSuccess,
  loadDatasetsFailed,
  setSearchQuery,
  setSortOrder,

  loadDataset,
  loadDatasetSuccess,
  loadDatasetFailed,
  setCurrentDataset,
  setCurrentSearchQuery,
  setCurrentSortOrder,

  createDatasetAction,
  cloneDatasetAction,
  updateDatasetAction,
  deleteDatasetAction,
} = datasetsSlice.actions;

export default datasetsSlice.reducer;
