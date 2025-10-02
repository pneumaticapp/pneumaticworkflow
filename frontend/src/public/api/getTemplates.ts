import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ETemplatesSorting } from '../types/workflow';
import { ITemplateListItem } from '../types/template';

export interface IGetTemplatesResponsePaginated {
  count: number;
  next: string;
  previous: string;
  results: ITemplateListItem[];
}

export type IGetTemplatesResponse = IGetTemplatesResponsePaginated | ITemplateListItem[];

export interface IGetTemplatesConfig {
  offset: number | undefined;
  limit: number | undefined;
  sorting: ETemplatesSorting;
  searchText: string;
  isActive: boolean | undefined;
  isTemplateOwner: boolean | undefined;
}

const QS_BY_SORTING: {[key in ETemplatesSorting]: string} = {
  [ETemplatesSorting.DateAsc]: 'ordering=date',
  [ETemplatesSorting.DateDesc]: 'ordering=-date',
  [ETemplatesSorting.NameAsc]: 'ordering=name',
  [ETemplatesSorting.NameDesc]: 'ordering=-name',
  [ETemplatesSorting.UsageAsc]: 'ordering=usage',
  [ETemplatesSorting.UsageDesc]: 'ordering=-usage',
};

export function getTemplates({
  offset,
  limit,
  sorting = ETemplatesSorting.DateDesc,
  searchText = '',
  isActive,
  isTemplateOwner,
}: Partial<IGetTemplatesConfig>) {
  const { api: { urls }} = getBrowserConfigEnv();

  const queryString = getTemplatesQueryString(
    { limit, offset, sorting, searchText, isActive, isTemplateOwner },
  );

  return commonRequest<IGetTemplatesResponse>(
    `${urls.templates}?${queryString}`,
    {}, {shouldThrow: true},
  );
}

export function getTemplatesQueryString({
  limit,
  offset,
  sorting,
  searchText,
  isActive,
  isTemplateOwner,
}: IGetTemplatesConfig) {
  return [
    limit !== undefined && `limit=${limit}`,
    offset !== undefined && `offset=${offset}`,
    isActive !== undefined && `is_active=${Boolean(isActive)}`,
    isTemplateOwner !== undefined && `is_template_owner=${Boolean(isTemplateOwner)}`,
    searchText && `search=${searchText}`,
    QS_BY_SORTING[sorting],
  ].filter(Boolean).join('&');
}
