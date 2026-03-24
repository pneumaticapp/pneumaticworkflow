import { commonRequest } from '../commonRequest';
import { IGetDatasetsResponse, IGetDatasetsParams } from '../../types/dataset';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function getDatasets(config: IGetDatasetsParams = {}) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const queryString = getDatasetsQueryString(config);
  const url = queryString ? `${urls.datasets}?${queryString}` : urls.datasets;

  return commonRequest<IGetDatasetsResponse>(
    url,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}

function getDatasetsQueryString({ ordering, limit, offset }: IGetDatasetsParams): string {
  return [
    ordering && `ordering=${ordering}`,
    limit !== undefined && `limit=${limit}`,
    offset !== undefined && `offset=${offset}`,
  ].filter(Boolean).join('&');
}
