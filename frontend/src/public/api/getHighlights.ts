import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IHighlightsItem } from '../types/highlights';
import { isArrayWithItems } from '../utils/helpers';
import { toTspDate } from '../utils/dateTime';

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

  if (dateAfter) dateAfterQuery = `date_after_tsp=${toTspDate(dateAfter)}`;
  if (dateBefore) dateBeforeQuery = `date_before_tsp=${toTspDate(dateBefore)}`;
  if (isArrayWithItems(users)) usersQuery = `current_performer_ids=${users.join(',')}`;
  if (isArrayWithItems(templates)) templatesQuery = `templates=${templates.join(',')}`;

  return [`limit=${limit}`, `offset=${offset}`, dateAfterQuery, dateBeforeQuery, usersQuery, templatesQuery]
    .filter(Boolean)
    .join('&');
}
