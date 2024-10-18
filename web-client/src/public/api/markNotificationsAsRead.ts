import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export type TMarkNotificationsAsReadRequest = {
  notifications: number[];
};

export function markNotificationsAsRead(data: TMarkNotificationsAsReadRequest) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest(
    urls.markNotificationsAsRead,
    {
      method: 'POST',
      body: mapRequestBody(data),
    },
    {
      responseType: 'empty',
    },
  );
}
