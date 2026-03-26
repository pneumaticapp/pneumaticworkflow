import { EDatasetsSorting } from '../../types/dataset';
import { IApplicationState } from '../../types/redux';

export const getDatasetsSorting = (state: IApplicationState): EDatasetsSorting => state.datasets.datasetsListSorting;

export const getDatasetsIsCreateModalOpen = (state: IApplicationState): boolean => state.datasets.isCreateModalOpen;
