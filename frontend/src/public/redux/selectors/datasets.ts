import { EDatasetsSorting } from '../../types/dataset';
import { IApplicationState } from '../../types/redux';

export const getDatasetsSorting = (state: IApplicationState): EDatasetsSorting => state.datasets.datasetsListSorting;

export const isCreateModalOpen = (state: IApplicationState): boolean => state.datasets.isCreateModalOpen;
