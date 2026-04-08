import { commonRequest } from '../commonRequest';
import { IGetDatasetsResponse, IGetDatasetsParams } from '../../types/dataset';
import { datasetsOrderingMap } from '../../constants/sortings';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function getDatasets(config: IGetDatasetsParams = {}) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const { signal } = config;
  const queryString = getDatasetsQueryString(config);
  const url = queryString ? `${urls.datasets}?${queryString}` : urls.datasets;

  return commonRequest<IGetDatasetsResponse>(
    url,
    {
      method: 'GET',
      signal,
    },
    {
      shouldThrow: true,
    },
  );
}

function getDatasetsQueryString({ ordering, limit, offset }: IGetDatasetsParams): string {
  const backendOrdering = ordering ? datasetsOrderingMap[ordering] || ordering : undefined;

  return [
    backendOrdering && `ordering=${backendOrdering}`,
    limit !== undefined && `limit=${limit}`,
    offset !== undefined && `offset=${offset}`,
  ].filter(Boolean).join('&');
}
