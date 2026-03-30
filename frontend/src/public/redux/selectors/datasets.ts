import { EDatasetsSorting, IDataset, TDatasetItemsSortOrder, IDatasetListItem } from '../../types/dataset';
import { IApplicationState, IDatasetsStore, IDatasetsList } from '../../types/redux';

export const getDatasetsStore = (state: IApplicationState): IDatasetsStore => state.datasets;

export const getDatasetsList = (state: IApplicationState): IDatasetListItem[] => state.datasets.datasetsList.items;

export const getDatasetsListSelection = (state: IApplicationState): IDatasetsList => state.datasets.datasetsList;

export const getDatasetsIsLoading = (state: IApplicationState): boolean => state.datasets.isLoading;

export const getDatasetsSorting = (state: IApplicationState): EDatasetsSorting => state.datasets.datasetsListSorting;

export const isCreateModalOpen = (state: IApplicationState): boolean => state.datasets.isCreateModalOpen;

export const isEditModalOpen = (state: IApplicationState): boolean => state.datasets.isEditModalOpen;

export const getCurrentDataset = (state: IApplicationState): IDataset | null => state.datasets.currentDataset;

export const isCurrentDatasetLoading = (state: IApplicationState): boolean => state.datasets.isCurrentDatasetLoading;

export const getCurrentSearchQuery = (state: IApplicationState): string => state.datasets.currentSearchQuery;

export const getCurrentSortOrder = (state: IApplicationState): TDatasetItemsSortOrder => state.datasets.currentSortOrder;
