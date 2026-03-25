import { EDatasetsSorting } from '../../types/dataset';
import { IApplicationState } from '../../types/redux';

export const getDatasetsSorting = (state: IApplicationState): EDatasetsSorting => state.datasets.datasetsListSorting;
