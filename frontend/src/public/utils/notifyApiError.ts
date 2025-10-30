import { NotificationManager } from '../components/UI/Notifications';
import { INotification } from '../types';

export type TNotificationType = 'error' | 'warning';

export function getApiErrorNotificationType(error: any): TNotificationType {
  const status = error?.status;
  if (!status) {
    return 'warning';
  }

  return status >= 500 && status < 600 ? 'error' : 'warning';
}

export function notifyApiError(error: any, notification: Partial<INotification>) {
  const type = getApiErrorNotificationType(error);

  if (type === 'error') {
    NotificationManager.error(notification);
  } else {
    NotificationManager.warning(notification);
  }
}
