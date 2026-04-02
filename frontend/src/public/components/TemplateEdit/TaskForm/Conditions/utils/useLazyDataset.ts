import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { loadDatasetForMap } from '../../../../../redux/datasets/slice';
import { getDatasetFromMap } from '../../../../../redux/selectors/datasets';
import { IDataset } from '../../../../../types/dataset';

import { TTaskVariable } from '../../../types';
import { shouldLoadDatasetForVariable } from './shouldLoadDatasetForVariable';

export function useLazyDataset(variable: TTaskVariable): IDataset | undefined {
  const dispatch = useDispatch();

  const shouldLoad = shouldLoadDatasetForVariable(variable);
  const {datasetId} = variable;

  const datasetFromMap = useSelector(getDatasetFromMap(datasetId as number));

  useEffect(() => {
    if (shouldLoad && !datasetFromMap) {
      dispatch(loadDatasetForMap(datasetId!));
    }
  }, [shouldLoad, datasetId, datasetFromMap, dispatch]);

  return shouldLoad ? datasetFromMap : undefined;
}
