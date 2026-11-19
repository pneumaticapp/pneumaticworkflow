import type { TNotificationsListItem } from '../../types/notifications';

export interface IStoreNotification {
  items: TNotificationsListItem[];
  totalItemsCount: number;
  unreadItemsCount: number;
  isNotificationsListOpen: boolean;
  hasNewNotifications: boolean;
  isLoading: boolean;
}
