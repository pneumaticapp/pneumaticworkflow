import { EFieldsetsSorting, IFieldsetCatalogItem } from '../../types/fieldset';
import { IFieldsetsStore, IFieldsetsList } from '../../types/redux';
import type { RootState } from '../store';

export const getFieldsetsStore = (state: RootState): IFieldsetsStore => state.fieldsets;

export const getFieldsetsList = (state: RootState): IFieldsetCatalogItem[] => state.fieldsets.fieldsetsList.items;

export const getFieldsetsListSelection = (state: RootState): IFieldsetsList => state.fieldsets.fieldsetsList;

export const getFieldsetsIsLoading = (state: RootState): boolean => state.fieldsets.isLoading;

export const getFieldsetsSorting = (state: RootState): EFieldsetsSorting => state.fieldsets.fieldsetsListSorting;

export const isCreateModalOpen = (state: RootState): boolean => state.fieldsets.isCreateModalOpen;

export const isEditModalOpen = (state: RootState): boolean => state.fieldsets.isEditModalOpen;

export const getCurrentFieldset = (state: RootState): IFieldsetCatalogItem | null => state.fieldsets.currentFieldset;

export const isCurrentFieldsetLoading = (state: RootState): boolean => state.fieldsets.isCurrentFieldsetLoading;

export const getFieldsetsCatalogItems = (state: RootState): IFieldsetCatalogItem[] =>
  state.fieldsets.catalogAllFieldsets;

export const getFieldsetsCatalogIsLoading = (state: RootState): boolean => state.fieldsets.isCatalogLoading;

export const getIsCatalogLoaded = (state: RootState): boolean => state.fieldsets.isCatalogLoaded;
