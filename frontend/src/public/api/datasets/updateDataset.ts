import { commonRequest } from '../commonRequest';
import { IDataset, IUpdateDatasetParams } from '../../types/dataset';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export function updateDataset({ id, ...data }: IUpdateDatasetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.dataset.replace(':id', String(id));

  return commonRequest<IDataset>(
    url,
    {
      method: 'PATCH',
      data: mapRequestBody(data),
    },
    {
      shouldThrow: true,
    },
  );
}
