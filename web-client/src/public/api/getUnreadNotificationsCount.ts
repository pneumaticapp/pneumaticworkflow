import { getBrowserConfigEnv } from '../utils/getConfig';
import { commonRequest } from './commonRequest';

export type TGetUnreadNotificationsCount = {
  count: number;
};

export function getUnreadNotificationsCount() {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<TGetUnreadNotificationsCount>(
    `${urls.getNotificationsCount}?status=new`,
    {},
    { shouldThrow: true },
  );
}
