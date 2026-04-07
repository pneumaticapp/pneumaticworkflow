/* eslint-disable @typescript-eslint/no-unused-vars */
import { createSlice, PayloadAction, createAction } from '@reduxjs/toolkit';

import { IDatasetsStore, IDatasetsList } from '../../types/redux';
import {
  IDataset, ICreateDatasetParams, IDatasetListItem,
  IUpdateDatasetParams, EDatasetsSorting, TDatasetItemsSortOrder,
} from '../../types/dataset';
import { TDeleteDatasetPayload } from './types';

export const initialState: IDatasetsStore = {
  datasetsList: {
    count: 0,
    offset: 0,
    items: [],
  },
  allDatasetsList: [],
  isAllDatasetsLoading: false,
  isAllDatasetsLoaded: false,
  isLoading: false,
  searchQuery: '',
  datasetsListSorting: EDatasetsSorting.DateDesc,
  isCreateModalOpen: false,
  isEditModalOpen: false,

  currentDataset: null,
  isCurrentDatasetLoading: false,
  currentSearchQuery: '',
  currentSortOrder: 'asc',
  
  datasetsMap: {},
};

const datasetsSlice = createSlice({
  name: 'datasets',
  initialState,
  reducers: {
    loadDatasets: (state, _action: PayloadAction<number>) => {
      state.isLoading = true;
    },

    loadDatasetsSuccess: (state, action: PayloadAction<IDatasetsList>) => {
      state.datasetsList = action.payload;
      state.isLoading = false;
    },

    loadDatasetsFailed: (state) => {
      state.isLoading = false;
    },

    loadAllDatasets: (state) => {
      state.isAllDatasetsLoading = true;
    },

    loadAllDatasetsSuccess: (state, action: PayloadAction<IDatasetListItem[]>) => {
      state.allDatasetsList = action.payload;
      state.isAllDatasetsLoading = false;
      state.isAllDatasetsLoaded = true;
    },

    loadAllDatasetsFailed: (state) => {
      state.isAllDatasetsLoading = false;
    },

    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },

    setDatasetsListSorting: (state, action: PayloadAction<EDatasetsSorting>) => {
      state.datasetsListSorting = action.payload;
    },

    openCreateModal: (state) => {
      state.isCreateModalOpen = true;
    },

    closeCreateModal: (state) => {
      state.isCreateModalOpen = false;
    },

    openEditModal: (state) => {
      state.isEditModalOpen = true;
    },

    closeEditModal: (state) => {
      state.isEditModalOpen = false;
    },

    loadCurrentDataset: (state, _action: PayloadAction<{ id: number }>) => {
      state.currentDataset = null;
      state.isCurrentDatasetLoading = true;
      state.currentSearchQuery = '';
      state.currentSortOrder = 'asc';
    },

    loadCurrentDatasetSuccess: (state, action: PayloadAction<IDataset>) => {
      state.currentDataset = action.payload;
      state.isCurrentDatasetLoading = false;
      
      if (state.datasetsMap[action.payload.id]) {
        state.datasetsMap[action.payload.id] = action.payload;
      }
    },

    loadCurrentDatasetFailed: (state) => {
      state.isCurrentDatasetLoading = false;
    },

    resetCurrentDataset: (state) => {
      state.currentDataset = null;
      state.isCurrentDatasetLoading = false;
      state.currentSearchQuery = '';
      state.currentSortOrder = 'asc';
    },

    saveDatasetToMap: (state, action: PayloadAction<IDataset>) => {
      state.datasetsMap[action.payload.id] = action.payload;
    },

    setCurrentDataset: (state, action: PayloadAction<IDataset>) => {
      state.currentDataset = action.payload;
      state.isCurrentDatasetLoading = false;
      
      if (state.datasetsMap[action.payload.id]) {
        state.datasetsMap[action.payload.id] = action.payload;
      }

      const listIndex = state.datasetsList.items.findIndex(
        (item) => item.id === action.payload.id
      );
      if (listIndex !== -1) {
        state.datasetsList.items[listIndex].name = action.payload.name;
        state.datasetsList.items[listIndex].description = action.payload.description;
      }
    },

    setCurrentSearchQuery: (state, action: PayloadAction<string>) => {
      state.currentSearchQuery = action.payload;
    },

    setCurrentSortOrder: (state, action: PayloadAction<TDatasetItemsSortOrder>) => {
      state.currentSortOrder = action.payload;
    },

    createDatasetAction: (state, _action: PayloadAction<ICreateDatasetParams>) => {
      state.isAllDatasetsLoaded = false;
    },

    cloneDatasetAction: (state, _action: PayloadAction<{ id: number }>) => {
      state.isAllDatasetsLoaded = false;
    },
    
    updateDatasetAction: (state, action: PayloadAction<IUpdateDatasetParams>) => {
      state.isAllDatasetsLoaded = false;
      if (state.currentDataset && state.currentDataset.id === action.payload.id) {
        if (action.payload.name !== undefined) state.currentDataset.name = action.payload.name;
        if (action.payload.description !== undefined) state.currentDataset.description = action.payload.description;
        if (action.payload.items) {
          state.currentDataset.items = action.payload.items.map((item, index) => ({
            ...item,
            id: item.id || -(index + 1),
          })) as any;
        }
        
        if (state.datasetsMap[action.payload.id]) {
          state.datasetsMap[action.payload.id] = state.currentDataset as IDataset;
        }
      }
    },

    deleteDatasetAction: (state, _action: PayloadAction<TDeleteDatasetPayload>) => {
      state.isLoading = true;
      state.isAllDatasetsLoaded = false;
    },

    removeDatasetFromList: (state, action: PayloadAction<number>) => {
      state.datasetsList.items = state.datasetsList.items.filter((item) => item.id !== action.payload);
      state.datasetsList.count -= 1;
      state.isLoading = false;
      delete state.datasetsMap[action.payload];
    },
  },
});

export const {
  loadDatasets,
  loadDatasetsSuccess,
  loadDatasetsFailed,
  loadAllDatasets,
  loadAllDatasetsSuccess,
  loadAllDatasetsFailed,
  setSearchQuery,
  setDatasetsListSorting,
  openCreateModal,
  closeCreateModal,
  openEditModal,
  closeEditModal,

  loadCurrentDataset,
  loadCurrentDatasetSuccess,
  loadCurrentDatasetFailed,
  resetCurrentDataset,
  setCurrentDataset,
  setCurrentSearchQuery,
  setCurrentSortOrder,

  createDatasetAction,
  cloneDatasetAction,
  updateDatasetAction,
  deleteDatasetAction,
  removeDatasetFromList,
  saveDatasetToMap,
} = datasetsSlice.actions;

export const loadDatasetForMap = createAction<number>('datasets/loadDatasetForMap');

export default datasetsSlice.reducer;
