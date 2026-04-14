/* eslint-disable @typescript-eslint/no-unused-vars */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IFieldsetsStore, IFieldsetsList } from '../../types/redux';
import {
  IFieldsetTemplate, ICreateFieldsetParams,
  IUpdateFieldsetParams,
  EFieldsetsSorting,
} from '../../types/fieldset';
import { TDeleteFieldsetPayload } from './types';

export const initialState: IFieldsetsStore = {
  templateId: null,
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
};

const fieldsetsSlice = createSlice({
  name: 'fieldsets',
  initialState,
  reducers: {
    setTemplateId: (state, action: PayloadAction<number>) => {
      state.templateId = action.payload;
    },

    loadFieldsets: (state, _action: PayloadAction<{ offset: number; templateId: number }>) => {
      state.isLoading = true;
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

    loadCurrentFieldsetSuccess: (state, action: PayloadAction<IFieldsetTemplate>) => {
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

    setCurrentFieldset: (state, action: PayloadAction<IFieldsetTemplate>) => {
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
      // saga handles side effect
    },

    updateFieldsetAction: (state, action: PayloadAction<IUpdateFieldsetParams>) => {
      if (state.currentFieldset && state.currentFieldset.id === action.payload.id) {
        if (action.payload.name !== undefined) state.currentFieldset.name = action.payload.name;
        if (action.payload.description !== undefined) state.currentFieldset.description = action.payload.description;
        if (action.payload.label_position !== undefined) state.currentFieldset.labelPosition = action.payload.label_position;
        if (action.payload.layout !== undefined) state.currentFieldset.layout = action.payload.layout;
        if (action.payload.kickoff_id !== undefined) state.currentFieldset.kickoffId = action.payload.kickoff_id;
        if (action.payload.task_id !== undefined) state.currentFieldset.taskId = action.payload.task_id;
        if (action.payload.rules) state.currentFieldset.rules = action.payload.rules;
        if (action.payload.fields) state.currentFieldset.fields = action.payload.fields as any;
      }
    },

    deleteFieldsetAction: (state, _action: PayloadAction<TDeleteFieldsetPayload>) => {
      state.isLoading = true;
    },

    removeFieldsetFromList: (state, action: PayloadAction<number>) => {
      state.fieldsetsList.items = state.fieldsetsList.items.filter((item) => item.id !== action.payload);
      state.fieldsetsList.count -= 1;
      state.isLoading = false;
    },
  },
});

export const {
  setTemplateId,
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
} = fieldsetsSlice.actions;

export default fieldsetsSlice.reducer;
