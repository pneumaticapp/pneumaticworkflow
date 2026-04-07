import { commonRequest } from '../commonRequest';
import { IDataset, IGetDatasetParams } from '../../types/dataset';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function getDataset({ id }: IGetDatasetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.dataset.replace(':id', String(id));

  return commonRequest<IDataset>(
    url,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}
