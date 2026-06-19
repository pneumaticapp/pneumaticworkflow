import { commonRequest } from '../commonRequest';
import { IDataset, ICreateDatasetParams } from '../../types/dataset';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export function createDataset({ name, description, items }: ICreateDatasetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IDataset>(
    urls.datasets,
    {
      method: 'POST',
      data: mapRequestBody({ name, description, items }),
    },
    {
      shouldThrow: true,
    },
  );
}
