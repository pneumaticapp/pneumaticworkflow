import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ISystemTemplate } from '../types/template';

export type TGetSystemTemplatesResponse = {
  count: number;
  results: ISystemTemplate[];
};

export interface IGetTemplatesSystemConfig {
  offset: number | undefined;
  limit: number | undefined;
  searchText: string | undefined;
  category?: number | null;
}

export function getTemplatesSystem({ offset, limit, searchText, category }: Partial<IGetTemplatesSystemConfig>) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const queryString = getTemplatesQueryString({ limit, offset, searchText, category });
  return commonRequest<TGetSystemTemplatesResponse>(
    `${urls.systemTemplates}?${queryString}`,
    {},
    { shouldThrow: true },
  );
}

export function getTemplatesQueryString({ limit, offset, searchText, category }: IGetTemplatesSystemConfig) {
  return [
    limit !== undefined && `limit=${limit}`,
    offset !== undefined && `offset=${offset}`,
    searchText !== undefined && `search=${searchText}`,
    category && `category=${category}`,
  ]
    .filter(Boolean)
    .join('&');
}
