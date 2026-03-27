import { EDatasetsSorting, IDataset, TDatasetItemsSortOrder } from '../../types/dataset';
import { IApplicationState } from '../../types/redux';

export const getDatasetsSorting = (state: IApplicationState): EDatasetsSorting => state.datasets.datasetsListSorting;

export const isCreateModalOpen = (state: IApplicationState): boolean => state.datasets.isCreateModalOpen;

export const isEditModalOpen = (state: IApplicationState): boolean => state.datasets.isEditModalOpen;

export const getCurrentDataset = (state: IApplicationState): IDataset | null => state.datasets.currentDataset;

export const isCurrentDatasetLoading = (state: IApplicationState): boolean => state.datasets.isCurrentDatasetLoading;

export const getCurrentSearchQuery = (state: IApplicationState): string => state.datasets.currentSearchQuery;

export const getCurrentSortOrder = (state: IApplicationState): TDatasetItemsSortOrder => state.datasets.currentSortOrder;
