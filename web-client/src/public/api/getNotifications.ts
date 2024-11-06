import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { TNotificationsListItem } from '../types';

export type TGetNotificationsResponse = {
  count: number;
  next?: string;
  previous?: string;
  results: TNotificationsListItem[];
};
export interface IGetNotificationsConfig {
  offset: number;
  limit?: number;
}

export function getNotifications({
  offset,
  limit = 20,
}: IGetNotificationsConfig) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<TGetNotificationsResponse>(
    `${urls.getNotifications}?${getNotificationsQueryString({ limit, offset })}`,
    {},
    { shouldThrow: true },
  );
}

export function getNotificationsQueryString({
  limit,
  offset,
}: IGetNotificationsConfig) {

  return [
    `limit=${limit}`,
    `offset=${offset}`,
  ].join('&');
}
