import { EFieldsetsSorting, IFieldsetTemplate, IFieldsetListItem } from '../../types/fieldset';
import { IApplicationState, IFieldsetsStore, IFieldsetsList } from '../../types/redux';

export const getFieldsetsStore = (state: IApplicationState): IFieldsetsStore => state.fieldsets;

export const getFieldsetsTemplateId = (state: IApplicationState): number | null => state.fieldsets.templateId;

export const getFieldsetsList = (state: IApplicationState): IFieldsetListItem[] => state.fieldsets.fieldsetsList.items;

export const getFieldsetsListSelection = (state: IApplicationState): IFieldsetsList => state.fieldsets.fieldsetsList;

export const getFieldsetsIsLoading = (state: IApplicationState): boolean => state.fieldsets.isLoading;

export const getFieldsetsSorting = (state: IApplicationState): EFieldsetsSorting => state.fieldsets.fieldsetsListSorting;

export const isCreateModalOpen = (state: IApplicationState): boolean => state.fieldsets.isCreateModalOpen;

export const isEditModalOpen = (state: IApplicationState): boolean => state.fieldsets.isEditModalOpen;

export const getCurrentFieldset = (state: IApplicationState): IFieldsetTemplate | null => state.fieldsets.currentFieldset;

export const isCurrentFieldsetLoading = (state: IApplicationState): boolean => state.fieldsets.isCurrentFieldsetLoading;

