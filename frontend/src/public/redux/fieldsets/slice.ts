/* eslint-disable @typescript-eslint/no-unused-vars */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IFieldsetsStore, IFieldsetsList } from '../../types/redux';
import {
  IFieldsetCatalogItem, ICreateFieldsetParams,
  IUpdateFieldsetParams,
  EFieldsetsSorting,
} from '../../types/fieldset';
import { TDeleteFieldsetPayload } from './types';

export const initialState: IFieldsetsStore = {
  fieldsetsList: {
    count: 0,
    offset: 0,
    items: [],
  },
  isLoading: false,
  searchQuery: '',
  fieldsetsListSorting: EFieldsetsSorting.DateDesc,
  isCreateModalOpen: false,
  isEditModalOpen: false,

  currentFieldset: null,
  isCurrentFieldsetLoading: false,

  catalogAllFieldsets: [],
  isCatalogLoading: false,
  isCatalogLoaded: false,
};

const fieldsetsSlice = createSlice({
  name: 'fieldsets',
  initialState,
  reducers: {
    loadFieldsets: (state, action: PayloadAction<{ offset: number }>) => {
      state.isLoading = true;
      if (action.payload.offset === 0) {
        state.fieldsetsList = { count: 0, offset: 0, items: [] };
      }
    },

    loadFieldsetsSuccess: (state, action: PayloadAction<IFieldsetsList>) => {
      state.fieldsetsList = action.payload;
      state.isLoading = false;
    },

    loadFieldsetsFailed: (state) => {
      state.isLoading = false;
    },

    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },

    setFieldsetsListSorting: (state, action: PayloadAction<EFieldsetsSorting>) => {
      state.fieldsetsListSorting = action.payload;
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

    loadCurrentFieldset: (state, _action: PayloadAction<{ id: number }>) => {
      state.currentFieldset = null;
      state.isCurrentFieldsetLoading = true;
    },

    loadCurrentFieldsetSuccess: (state, action: PayloadAction<IFieldsetCatalogItem>) => {
      state.currentFieldset = action.payload;
      state.isCurrentFieldsetLoading = false;
    },

    loadCurrentFieldsetFailed: (state) => {
      state.isCurrentFieldsetLoading = false;
    },

    resetCurrentFieldset: (state) => {
      state.currentFieldset = null;
      state.isCurrentFieldsetLoading = false;
    },

    setCurrentFieldset: (state, action: PayloadAction<IFieldsetCatalogItem>) => {
      state.currentFieldset = action.payload;
      state.isCurrentFieldsetLoading = false;

      const listIndex = state.fieldsetsList.items.findIndex(
        (item) => item.id === action.payload.id
      );
      if (listIndex !== -1) {
        state.fieldsetsList.items[listIndex].name = action.payload.name;
        state.fieldsetsList.items[listIndex].description = action.payload.description;
      }
    },

    createFieldsetAction: (state, _action: PayloadAction<ICreateFieldsetParams>) => {
      state.isCatalogLoaded = false;
    },

    updateFieldsetAction: (state, _action: PayloadAction<IUpdateFieldsetParams>) => {
      state.isCatalogLoaded = false;
    },

    deleteFieldsetAction: (state, _action: PayloadAction<TDeleteFieldsetPayload>) => {
      state.isLoading = true;
      state.isCatalogLoaded = false;
    },

    removeFieldsetFromList: (state, action: PayloadAction<number>) => {
      state.fieldsetsList.items = state.fieldsetsList.items.filter((item) => item.id !== action.payload);
      state.fieldsetsList.count -= 1;
      state.isLoading = false;
    },
    loadFieldsetsCatalog: (state) => {
      state.isCatalogLoading = true;
    },

    loadFieldsetsCatalogSuccess: (state, action: PayloadAction<IFieldsetCatalogItem[]>) => {
      state.catalogAllFieldsets = action.payload;
      state.isCatalogLoading = false;
      state.isCatalogLoaded = true;
    },

    loadFieldsetsCatalogFailed: (state) => {
      state.isCatalogLoading = false;
      state.isCatalogLoaded = false;
    },
  },
});

export const {
  loadFieldsets,
  loadFieldsetsSuccess,
  loadFieldsetsFailed,
  setSearchQuery,
  setFieldsetsListSorting,
  openCreateModal,
  closeCreateModal,
  openEditModal,
  closeEditModal,

  loadCurrentFieldset,
  loadCurrentFieldsetSuccess,
  loadCurrentFieldsetFailed,
  resetCurrentFieldset,
  setCurrentFieldset,

  createFieldsetAction,
  updateFieldsetAction,
  deleteFieldsetAction,
  removeFieldsetFromList,

  loadFieldsetsCatalog,
  loadFieldsetsCatalogSuccess,
  loadFieldsetsCatalogFailed,
} = fieldsetsSlice.actions;

export default fieldsetsSlice.reducer;
