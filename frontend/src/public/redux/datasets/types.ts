import type { EDatasetsSorting, IDataset, IDatasetListItem, TDatasetItemsSortOrder } from '../../types/dataset';

export type TDeleteDatasetPayload = {
  id: number;
  onSuccess?: () => void;
};

export interface IDatasetsList {
  count: number;
  offset: number;
  items: IDatasetListItem[];
}

export interface IDatasetsStore {
  datasetsList: IDatasetsList;
  allDatasetsList: IDatasetListItem[];
  isAllDatasetsLoading: boolean;
  isAllDatasetsLoaded: boolean;
  isLoading: boolean;
  searchQuery: string;
  datasetsListSorting: EDatasetsSorting;

  isCreateModalOpen: boolean;
  isEditModalOpen: boolean;

  currentDataset: IDataset | null;
  isCurrentDatasetLoading: boolean;
  currentSearchQuery: string;
  currentSortOrder: TDatasetItemsSortOrder;

  datasetsMap: Record<number, IDataset>;
}
