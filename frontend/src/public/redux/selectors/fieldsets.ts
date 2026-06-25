import { EFieldsetsSorting, IFieldsetCatalogItem } from '../../types/fieldset';
import { IApplicationState, IFieldsetsStore, IFieldsetsList } from '../../types/redux';
import { IFieldsetData } from '../../types/template';
import { mapFieldsetTemplateToFieldsetData } from '../../utils/mapFieldsetTemplateToFieldsetData';

export const getFieldsetsStore = (state: IApplicationState): IFieldsetsStore => state.fieldsets;

export const getFieldsetsList = (state: IApplicationState): IFieldsetCatalogItem[] => state.fieldsets.fieldsetsList.items;

export const getFieldsetsListSelection = (state: IApplicationState): IFieldsetsList => state.fieldsets.fieldsetsList;

export const getFieldsetsIsLoading = (state: IApplicationState): boolean => state.fieldsets.isLoading;

export const getFieldsetsSorting = (state: IApplicationState): EFieldsetsSorting => state.fieldsets.fieldsetsListSorting;

export const isCreateModalOpen = (state: IApplicationState): boolean => state.fieldsets.isCreateModalOpen;

export const isEditModalOpen = (state: IApplicationState): boolean => state.fieldsets.isEditModalOpen;

export const getCurrentFieldset = (state: IApplicationState): IFieldsetCatalogItem | null => state.fieldsets.currentFieldset;

export const isCurrentFieldsetLoading = (state: IApplicationState): boolean => state.fieldsets.isCurrentFieldsetLoading;

export const getFieldsetsCatalogItems = (state: IApplicationState): IFieldsetCatalogItem[] => state.fieldsets.catalogAllFieldsets;

export const getFieldsetsCatalogIsLoading = (state: IApplicationState): boolean => state.fieldsets.isCatalogLoading;

export const getIsCatalogLoaded = (state: IApplicationState): boolean => state.fieldsets.isCatalogLoaded;

let cachedCatalogItems: IFieldsetCatalogItem[] = [];
let cachedCatalogMap: ReadonlyMap<string, IFieldsetData> = new Map();

export const getFieldsetsCatalogByApiName = (state: IApplicationState): ReadonlyMap<string, IFieldsetData> => {
  const items = getFieldsetsCatalogItems(state);
  if (items === cachedCatalogItems) {
    return cachedCatalogMap;
  }

  const nextMap = new Map<string, IFieldsetData>();
  items.forEach((item) => {
    const fieldsetData = mapFieldsetTemplateToFieldsetData(item);
    nextMap.set(fieldsetData.apiName, fieldsetData);
  });

  cachedCatalogItems = items;
  cachedCatalogMap = nextMap;
  return cachedCatalogMap;
};

