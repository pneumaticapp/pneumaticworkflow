import type { EFieldsetsSorting, IFieldsetCatalogItem } from '../../types/fieldset';

export type TDeleteFieldsetPayload = {
  id: number;
  onSuccess?: () => void;
};

export interface IFieldsetsList {
  count: number;
  offset: number;
  items: IFieldsetCatalogItem[];
}

export interface IFieldsetsStore {
  fieldsetsList: IFieldsetsList;
  isLoading: boolean;
  searchQuery: string;
  fieldsetsListSorting: EFieldsetsSorting;

  isCreateModalOpen: boolean;
  isEditModalOpen: boolean;

  currentFieldset: IFieldsetCatalogItem | null;
  isCurrentFieldsetLoading: boolean;

  catalogAllFieldsets: IFieldsetCatalogItem[];
  isCatalogLoading: boolean;
  isCatalogLoaded: boolean;
}
