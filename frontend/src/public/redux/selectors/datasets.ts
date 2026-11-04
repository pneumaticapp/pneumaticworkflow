import { EDatasetsSorting, IDataset, TDatasetItemsSortOrder, IDatasetListItem } from '../../types/dataset';
import { IDatasetsStore, IDatasetsList } from '../../types/redux';
import type { RootState } from '../store';

export const getDatasetsStore = (state: RootState): IDatasetsStore => state.datasets;

export const getDatasetsList = (state: RootState): IDatasetListItem[] => state.datasets.datasetsList.items;

export const getAllDatasetsList = (state: RootState): IDatasetListItem[] => state.datasets.allDatasetsList;

export const getIsAllDatasetsLoading = (state: RootState): boolean => state.datasets.isAllDatasetsLoading;

export const getIsAllDatasetsLoaded = (state: RootState): boolean => state.datasets.isAllDatasetsLoaded;

export const getDatasetsListSelection = (state: RootState): IDatasetsList => state.datasets.datasetsList;

export const getDatasetsIsLoading = (state: RootState): boolean => state.datasets.isLoading;

export const getDatasetsSorting = (state: RootState): EDatasetsSorting => state.datasets.datasetsListSorting;

export const isCreateModalOpen = (state: RootState): boolean => state.datasets.isCreateModalOpen;

export const isEditModalOpen = (state: RootState): boolean => state.datasets.isEditModalOpen;

export const getCurrentDataset = (state: RootState): IDataset | null => state.datasets.currentDataset;

export const isCurrentDatasetLoading = (state: RootState): boolean => state.datasets.isCurrentDatasetLoading;

export const getCurrentSearchQuery = (state: RootState): string => state.datasets.currentSearchQuery;

export const getCurrentSortOrder = (state: RootState): TDatasetItemsSortOrder => state.datasets.currentSortOrder;

export const getDatasetFromMap =
  (id: number) =>
  (state: RootState): IDataset | undefined =>
    state.datasets.datasetsMap[id];
