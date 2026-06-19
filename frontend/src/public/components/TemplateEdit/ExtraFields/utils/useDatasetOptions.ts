import { useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { IExtraField } from '../../../../types/template';
import { getAllDatasetsList, getIsAllDatasetsLoading, getIsAllDatasetsLoaded } from '../../../../redux/selectors/datasets';
import { loadAllDatasets } from '../../../../redux/datasets/slice';
import { DATASET_FIELD_TYPES } from '../constants';

export function useDatasetOptions(fields: IExtraField[]) {
  const dispatch = useDispatch();

  const hasDatasetFields = fields.some((field) => DATASET_FIELD_TYPES.includes(field.type));

  const datasetsList = useSelector(getAllDatasetsList);
  const isDatasetsLoading = useSelector(getIsAllDatasetsLoading);
  const isDatasetsLoaded = useSelector(getIsAllDatasetsLoaded);

  useEffect(() => {
    if (hasDatasetFields && !isDatasetsLoaded && !isDatasetsLoading) {
      dispatch(loadAllDatasets());
    }
  }, [hasDatasetFields, isDatasetsLoaded, isDatasetsLoading, dispatch]);

  return useMemo(
    () => datasetsList.map((dataset) => ({ label: dataset.name, value: String(dataset.id) })),
    [datasetsList],
  );
}
