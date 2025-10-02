import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export type TRemoveNotificationItemRequest = {
  notificationId: number;
};

export function removeNotificationItem(data: TRemoveNotificationItemRequest) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest(
    urls.removeNotificationItem.replace(':id', String(data.notificationId)),
    {
      method: 'DELETE',
    },
    {
      responseType: 'empty',
    },
  );
}
