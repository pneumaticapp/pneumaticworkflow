import { commonRequest } from '../commonRequest';
import { IDeleteDatasetParams } from '../../types/dataset';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function deleteDataset({ id }: IDeleteDatasetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.dataset.replace(':id', String(id));

  return commonRequest<void>(
    url,
    {
      method: 'DELETE',
    },
    {
      shouldThrow: true,
      responseType: 'empty',
    },
  );
}
