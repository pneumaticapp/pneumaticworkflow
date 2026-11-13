import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { loadDatasetForMap } from '../../../../../redux/datasets/slice';
import { getDatasetFromMap } from '../../../../../redux/selectors/datasets';
import type { IDataset } from '../../../../../types/dataset';

import type { TTaskVariable } from '../../../../../types/template';
import { shouldLoadDatasetForVariable } from './shouldLoadDatasetForVariable';

export function useLazyDataset(variable: TTaskVariable | null): IDataset | undefined {
  const dispatch = useDispatch();

  const shouldLoad = variable ? shouldLoadDatasetForVariable(variable) : false;
  const datasetId = variable?.datasetId ?? null;

  const datasetFromMap = useSelector(getDatasetFromMap(datasetId as number));

  useEffect(() => {
    if (shouldLoad && !datasetFromMap && datasetId) {
      dispatch(loadDatasetForMap(datasetId));
    }
  }, [shouldLoad, datasetId, datasetFromMap, dispatch]);

  return shouldLoad ? datasetFromMap : undefined;
}
