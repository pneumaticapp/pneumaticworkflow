import { commonRequest } from '../commonRequest';
import { IGetFieldsetsResponse, IGetFieldsetsParams } from '../../types/fieldset';
import { fieldsetsOrderingMap } from '../../constants/sortings';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function getFieldsets(config: IGetFieldsetsParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const { signal, templateId } = config;
  const queryString = getFieldsetsQueryString(config);
  const baseUrl = urls.templateFieldsets.replace(':id', String(templateId));
  const url = queryString ? `${baseUrl}?${queryString}` : baseUrl;

  return commonRequest<IGetFieldsetsResponse>(
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

function getFieldsetsQueryString({ ordering, limit, offset }: IGetFieldsetsParams): string {
  const backendOrdering = ordering ? fieldsetsOrderingMap[ordering] || ordering : undefined;

  return [
    backendOrdering && `ordering=${backendOrdering}`,
    limit !== undefined && `limit=${limit}`,
    offset !== undefined && `offset=${offset}`,
  ].filter(Boolean).join('&');
}
