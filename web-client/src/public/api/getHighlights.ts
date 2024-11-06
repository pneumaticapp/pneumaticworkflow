import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IHighlightsItem } from '../types/highlights';
import { isArrayWithItems } from '../utils/helpers';

export interface IGetHighlightsResponse {
  count: number;
  next?: string;
  previous?: string;
  results: IHighlightsItem[];
}

export interface IGetHighlightsConfig {
  limit?: number;
  offset?: number;
  filters?: IGetHighlightsFilters;
}

export interface IGetHighlightsFilters {
  dateAfter?: Date | null;
  dateBefore?: Date | null;
  users?: string[] | null;
  templates?: string[] | null;
}

export type TFiltersQuery = string | null;

const DEFAULT_FILTERS: IGetHighlightsFilters = {
  dateAfter: null,
  dateBefore: null,
  users: null,
  templates: null,
};

export function getHighlights({ limit = 12, offset = 0, filters = DEFAULT_FILTERS }: Partial<IGetHighlightsConfig>) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const baseUrl = urls.highlights;
  const query = getHighlightsQueryString({ limit, offset, filters });
  const url = `${baseUrl}?${query}`;

  return commonRequest<IGetHighlightsResponse>(url);
}

export function getHighlightsQueryString({ limit, offset, filters }: IGetHighlightsConfig) {
  const { dateAfter, dateBefore, users, templates } = filters || {};
  let dateAfterQuery: TFiltersQuery = null;
  let dateBeforeQuery: TFiltersQuery = null;
  let usersQuery: TFiltersQuery = null;
  let templatesQuery: TFiltersQuery = null;

  if (dateAfter) {
    const formattedDateAfterTsp =
      typeof dateAfter === 'string' ? new Date(dateAfter).getTime() / 1000 : dateAfter.getTime() / 1000;
    dateAfterQuery = `date_after_tsp=${formattedDateAfterTsp}`;
  }

  if (dateBefore) {
    const formattedDateBeforeTsp =
      typeof dateBefore === 'string' ? new Date(dateBefore).getTime() / 1000 : dateBefore.getTime() / 1000;
    dateBeforeQuery = `date_before_tsp=${formattedDateBeforeTsp}`;
  }

  if (isArrayWithItems(users)) {
    usersQuery = `users=${users.join(',')}`;
  }

  if (isArrayWithItems(templates)) {
    templatesQuery = `templates=${templates.join(',')}`;
  }

  return [`limit=${limit}`, `offset=${offset}`, dateAfterQuery, dateBeforeQuery, usersQuery, templatesQuery]
    .filter(Boolean)
    .join('&');
}
