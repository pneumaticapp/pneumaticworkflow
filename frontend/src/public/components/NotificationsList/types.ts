import { IChangeNotificationsListPayload, ILoadNotificationsPayload } from '../../redux/notifications/actions';
import { TNotificationsListItem } from '../../types';
import { TUserListItem } from '../../types/user';

export interface INotificationsListProps {
  users: TUserListItem[];
  notifications: TNotificationsListItem[];
  isLoading: boolean;
  withPaywall: boolean;
  totalNotificationsCount: number;
  isClosing: boolean;
  setNotificationsListIsOpen(payload: boolean): void;
  removeNotificationItem(value: { notificationId: number }): void;
  changeNotificationsList(notifications: IChangeNotificationsListPayload): void;
  fetchNotificationsAsRead(): void;
  markNotificationsAsRead(): void;
  loadNotificationsList(payload?: ILoadNotificationsPayload): void;
}
